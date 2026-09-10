"""Matchmaking Service for RAG-based job matchmaking and personalized fit synthesis."""

import json
import re
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.core.logging import logger
from app.db.chroma import chroma_manager
from app.db.mongodb import mongo_manager
from app.services.cloudinary_service import cloudinary_service
from app.services.resume_parser import resume_parser
from app.schemas.match import CandidateProfile, CompanyFitItem, ResumeMatchResponse


class MatchmakingService:
    """Orchestrates resume ingestion, ChromaDB querying with fallback, and Groq fit generation."""

    def __init__(self):
        pass

    def _get_groq_llm(self):
        """Initializes Groq client with model selection."""
        if not settings.has_groq_key:
            return None
        return ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=0.2
        )

    async def generate_fit_summaries(
        self,
        candidate_profile: CandidateProfile,
        matched_jobs: List[Dict[str, Any]],
        user_experience: Optional[str] = None
    ) -> List[CompanyFitItem]:
        """Uses Groq API to generate personalized 'Why you are a perfect fit' summaries for the top 3 companies,
        incorporating experience level alignment.
        """
        fits: List[CompanyFitItem] = []
        top_candidates = matched_jobs[:3]

        if not top_candidates:
            return []

        effective_exp = user_experience or (f"{candidate_profile.years_of_experience} years" if candidate_profile.years_of_experience else "Fresher")

        # If Groq is available, ask Groq to synthesize the fit evaluations
        if settings.has_groq_key:
            try:
                llm = self._get_groq_llm()

                # Build context for LLM
                job_contexts_str = ""
                for idx, job in enumerate(top_candidates):
                    meta = job.get("metadata", {})
                    job_contexts_str += (
                        f"\n--- MATCH {idx + 1} ---\n"
                        f"Company: {meta.get('company', 'Unknown')}\n"
                        f"Role: {meta.get('title', 'Software Engineer')}\n"
                        f"Experience Level Required: {meta.get('experience_level', 'Not specified')}\n"
                        f"Source Tier: {job.get('source', 'excel')}\n"
                        f"Required Skills / Tech: {meta.get('skills', '')} | {meta.get('tech_stack', '')}\n"
                        f"Description/Snippet: {job.get('document', '')[:400]}\n"
                    )

                prompt = (
                    "You are a Senior Technical Talent Partner and RAG Matchmaker. Given the candidate profile and the 3 matched companies below,\n"
                    "generate an in-depth, personalized 'Why you are a perfect fit' evaluation for each company.\n\n"
                    f"CANDIDATE PROFILE:\n"
                    f"Name: {candidate_profile.name}\n"
                    f"Declared Experience Level: {effective_exp}\n"
                    f"Target Roles: {', '.join(candidate_profile.role_preferences)}\n"
                    f"Technical Skills: {', '.join(candidate_profile.technical_skills)}\n"
                    f"Domain Experience: {', '.join(candidate_profile.domain_experience)}\n"
                    f"Summary: {candidate_profile.summary}\n\n"
                    f"MATCHED COMPANIES & JOBS:\n{job_contexts_str}\n\n"
                    "CRITICAL EXPERIENCE-MATCHING DIRECTIVE:\n"
                    f"- Explicitly tailor the fit analysis to the candidate's current experience level: '{effective_exp}'.\n"
                    "- If the candidate is a Fresher / Entry-Level, emphasize foundational programming, eagerness to learn, relevant internships/coursework, and suitability for growth.\n"
                    "- If the candidate is Experienced / Senior, emphasize leadership, production reliability, and architectural scope.\n"
                    "- Avoid mismatching senior expectations to junior candidates.\n\n"
                    "Generate a JSON list of objects matching this schema:\n"
                    "[\n"
                    "  {\n"
                    '    "company": "Company Name",\n'
                    '    "role": "Role Name",\n'
                    '    "why_perfect_fit": "2-3 compelling sentences detailing exactly how candidate skills and experience match the company architecture and mission.",\n'
                    '    "key_matching_points": ["Point 1", "Point 2", "Point 3"],\n'
                    '    "recommendations": "Advice on standout talking points or portfolio artifacts for this application."\n'
                    "  }\n"
                    "]\n"
                    "Return ONLY the raw JSON array. No markdown code blocks."
                )

                messages = [
                    SystemMessage(content="You are an elite AI Career & Engineering Matchmaker producing valid JSON output."),
                    HumanMessage(content=prompt)
                ]

                try:
                    response = await llm.ainvoke(messages)
                except Exception as invoke_err:
                    logger.warning("Fit synthesis failed with %s: %s. Retrying with fallback model %s...", settings.GROQ_MODEL, invoke_err, settings.GROQ_FALLBACK_MODEL)
                    fallback_llm = ChatGroq(
                        groq_api_key=settings.GROQ_API_KEY,
                        model_name=settings.GROQ_FALLBACK_MODEL,
                        temperature=0.2
                    )
                    response = await fallback_llm.ainvoke(messages)

                content = response.content.strip()
                content = re.sub(r"^```json\s*", "", content)
                content = re.sub(r"^```\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

                parsed_evaluations = json.loads(content)

                # Merge with ChromaDB match metadata
                for idx, job in enumerate(top_candidates):
                    meta = job.get("metadata", {})
                    eval_item = parsed_evaluations[idx] if idx < len(parsed_evaluations) else {}

                    fits.append(CompanyFitItem(
                        company=meta.get("company", eval_item.get("company", "Tech Company")),
                        role=meta.get("title", eval_item.get("role", "Software Engineer")),
                        experience_level=meta.get("experience_level"),
                        source=job.get("source", "excel"),
                        similarity_score=job.get("similarity_score", 0.85),
                        distance=job.get("distance", 0.15),
                        why_perfect_fit=eval_item.get(
                            "why_perfect_fit",
                            f"Strong match based on technical alignment in {', '.join(candidate_profile.technical_skills[:4])} for {effective_exp} role."
                        ),
                        key_matching_points=eval_item.get(
                            "key_matching_points",
                            candidate_profile.technical_skills[:3]
                        ),
                        recommendations=eval_item.get(
                            "recommendations",
                            "Highlight core systems projects and hands-on demonstrations in your interview."
                        ),
                        job_url=meta.get("url")
                    ))
                return fits

            except Exception as e:
                logger.error("Error synthesizing fit summary via Groq: %s. Using standard template.", e)

        # Fallback template if Groq is offline
        for job in top_candidates:
            meta = job.get("metadata", {})
            company = meta.get("company", "Tech Enterprise")
            role = meta.get("title", "Software Engineer")
            fits.append(CompanyFitItem(
                company=company,
                role=role,
                experience_level=meta.get("experience_level"),
                source=job.get("source", "excel"),
                similarity_score=job.get("similarity_score", 0.88),
                distance=job.get("distance", 0.12),
                why_perfect_fit=(
                    f"Your background in {', '.join(candidate_profile.technical_skills[:3])} directly aligns with "
                    f"{company}'s engineering needs for {role} at the {effective_exp} stage."
                ),
                key_matching_points=[
                    f"Technical mastery in {candidate_profile.technical_skills[0] if candidate_profile.technical_skills else 'Python'}",
                    f"Aligned experience level ({effective_exp})",
                    f"Domain background in {candidate_profile.domain_experience[0] if candidate_profile.domain_experience else 'Cloud Systems'}"
                ],
                recommendations=f"Prepare relevant portfolio artifacts suited for {company}'s tech stack.",
                job_url=meta.get("url")
            ))

        return fits

    async def match_resume_file(
        self,
        file_bytes: bytes,
        filename: str,
        experience: str = "Fresher",
        user_id: Optional[str] = None
    ) -> ResumeMatchResponse:
        """Executes the full resume matchmaking pipeline with experience-based RAG matching:

        1. Upload file to Cloudinary and get secure URL (mapped to user folder if authenticated).
        2. Extract text & parse profile with Groq API.
        3. Query ChromaDB factoring user experience into vector query and experience re-ranking.
        4. Generate personalized 'Why you are a perfect fit' summary for top 3 companies with experience alignment.
        5. Persist record to MongoDB and map Cloudinary resume directly to user profile.
        """
        logger.info(
            ">>> Beginning resume match workflow for '%s' (user: %s, experience: %s, %d bytes)...",
            filename, user_id, experience, len(file_bytes)
        )

        # STEP 1: Upload to Cloudinary under user-specific subfolder if logged in
        folder_suffix = f"users/{user_id}" if user_id else None
        upload_res = await cloudinary_service.upload_file(file_bytes, filename, folder_suffix=folder_suffix)
        file_url = upload_res.get("secure_url", "")
        logger.info("Cloudinary secure URL: %s", file_url)

        # STEP 2: Extract text & parse structured profile using Groq
        profile = await resume_parser.parse_resume(file_bytes, filename, file_url)
        profile.provided_experience = experience
        logger.info(
            "Extracted profile for '%s': Skills: %s | Roles: %s | Experience: %s",
            profile.name, profile.technical_skills[:5], profile.role_preferences, experience
        )

        # STEP 3: Formulate experience-aware vector query & search ChromaDB
        query_text = (
            f"Candidate Experience Level: {experience}\n"
            f"Desired Roles: {', '.join(profile.role_preferences)}\n"
            f"Candidate Skills: {', '.join(profile.technical_skills)}\n"
            f"Domains: {', '.join(profile.domain_experience)}\n"
            f"Summary: {profile.summary}"
        )

        matched_jobs, source_used, is_fallback = chroma_manager.search_with_fallback(
            query_text=query_text,
            user_experience=experience,
            n_results=5
        )

        # STEP 4: Generate personalized 'Why you are a perfect fit' summary factoring in experience
        top_fits = await self.generate_fit_summaries(profile, matched_jobs, user_experience=experience)

        # STEP 5: Persist match record to MongoDB
        record_id = None
        try:
            persisted_payload = {
                "filename": filename,
                "cloudinary_url": file_url,
                "cloudinary_public_id": upload_res.get("public_id"),
                "candidate_profile": profile.model_dump(),
                "provided_experience": experience,
                "source_used": source_used,
                "is_fallback": is_fallback,
                "top_company_fits": [fit.model_dump() for fit in top_fits],
                "user_id": user_id
            }
            record_id = await mongo_manager.save_resume_record(persisted_payload)
            logger.info("Saved resume match record with ID: %s", record_id)

            # Map resume directly to the user's MongoDB record
            if user_id:
                user_resume_data = {
                    "cloudinary_url": file_url,
                    "cloudinary_public_id": upload_res.get("public_id"),
                    "filename": filename,
                    "candidate_profile": profile.model_dump(),
                    "provided_experience": experience,
                    "top_company_fits": [fit.model_dump() for fit in top_fits]
                }
                await mongo_manager.update_user_resume(user_id, user_resume_data)
                logger.info("Directly mapped Cloudinary resume to user '%s' in MongoDB.", user_id)

        except Exception as e:
            logger.warning("Could not persist match record to MongoDB: %s", e)

        return ResumeMatchResponse(
            success=True,
            message=f"Resume successfully parsed, saved to Cloudinary, and matched against {source_used} job database.",
            cloudinary_url=file_url,
            candidate_profile=profile,
            source_used=source_used,
            is_fallback=is_fallback,
            provided_experience=experience,
            top_company_fits=top_fits,
            record_id=record_id
        )


matchmaking_service = MatchmakingService()
