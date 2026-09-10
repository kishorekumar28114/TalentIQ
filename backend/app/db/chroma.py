"""ChromaDB Vector Database Management with Two-Tier Data Strategy.

Data Strategy:
  - Base Data: metadata={"source": "excel"} -> Permanent fallback data.
  - Live Data: metadata={"source": "live"} -> Dynamic scraped data.
"""

import json
import os
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from app.core.config import settings
from app.core.logging import logger


class ChromaManager:
    """Manages the ChromaDB 'job_market' collection and query operations."""

    def __init__(self):
        self.persist_dir = settings.CHROMA_PERSIST_DIRECTORY
        os.makedirs(self.persist_dir, exist_ok=True)

        logger.info("Initializing ChromaDB PersistentClient at '%s'...", self.persist_dir)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        # Use default SentenceTransformer / ONNX embedding function
        # This provides standardized embeddings across local and cloud environments
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "Job market postings and tech stack blogs"}
        )
        logger.info(
            "ChromaDB collection '%s' ready. Current record count: %d",
            self.collection_name,
            self.collection.count()
        )

    def count(self) -> int:
        """Returns total records in the collection."""
        return self.collection.count()

    def count_by_source(self, source: str) -> int:
        """Counts records filtered by source ('live' or 'excel')."""
        try:
            results = self.collection.get(where={"source": source})
            return len(results.get("ids", []))
        except Exception as e:
            logger.error("Error counting Chroma records by source '%s': %s", source, e)
            return 0

    def delete_live_records(self) -> int:
        """Deletes all existing ChromaDB records where metadata={'source': 'live'}.

        Workflow:
          1. Query all record IDs with where={'source': 'live'}.
          2. Call collection.delete(ids=...)
          Returns number of deleted records.
        """
        try:
            live_data = self.collection.get(where={"source": "live"})
            ids_to_delete = live_data.get("ids", [])
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info("Successfully deleted %d existing 'live' records from ChromaDB.", len(ids_to_delete))
                return len(ids_to_delete)
            logger.info("No existing 'live' records found in ChromaDB to delete.")
            return 0
        except Exception as e:
            logger.error("Error deleting live records from ChromaDB: %s", e)
            raise

    def add_job_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Inserts documents with metadata into the ChromaDB collection."""
        if not documents:
            return []

        if ids is None:
            ids = [f"job_{uuid.uuid4().hex[:12]}" for _ in range(len(documents))]

        # Ensure all metadata values are primitive (Chroma requirement)
        cleaned_metadatas = []
        for m in metadatas:
            cleaned = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    cleaned[k] = v
                elif isinstance(v, list):
                    cleaned[k] = ", ".join(str(item) for item in v)
                else:
                    cleaned[k] = str(v)
            cleaned_metadatas.append(cleaned)

        self.collection.add(
            documents=documents,
            metadatas=cleaned_metadatas,
            ids=ids
        )
        logger.info("Added %d documents to ChromaDB collection '%s'.", len(documents), self.collection_name)
        return ids

    def query_jobs(
        self,
        query_text: str,
        source: Optional[str] = None,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """Queries ChromaDB with optional metadata filtering on source."""
        where_clause = {"source": source} if source else None
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_clause
        )
        return results

    @staticmethod
    def classify_experience_level(exp_str: str) -> str:
        """Classifies an experience description into: 'fresher', 'junior' (1-2y), 'mid' (3-5y), 'senior' (5y+)."""
        if not exp_str:
            return "mid"
        s = exp_str.lower()
        if any(k in s for k in ["fresher", "intern", "entry", "trainee", "college", "graduate", "0 yr", "0-1", "freshers"]):
            return "fresher"
        nums = re.findall(r"(\d+)", s)
        if nums:
            val = float(nums[0])
            if val <= 1.0:
                return "fresher"
            elif val <= 2.5:
                return "junior"
            elif val <= 5.0:
                return "mid"
            else:
                return "senior"
        if any(k in s for k in ["lead", "staff", "principal", "architect", "senior", "sr.", "director", "head of"]):
            return "senior"
        return "mid"

    def rerank_by_experience(
        self,
        items: List[Dict[str, Any]],
        user_experience: Optional[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Reranks vector search matches based on candidate experience alignment."""
        if not user_experience or not items:
            return items[:top_k]

        user_tier = self.classify_experience_level(user_experience)
        scored_items = []

        for item in items:
            meta = item.get("metadata", {})
            doc = item.get("document", "")
            role = meta.get("title", "")
            exp_meta = meta.get("experience_level", "")
            combined_text = f"{role} {exp_meta} {doc}".lower()

            job_tier = self.classify_experience_level(f"{exp_meta} {role}")
            orig_dist = item.get("distance", 0.5)
            adjusted_dist = orig_dist

            # Apply domain-aware alignment penalties/bonuses
            if user_tier == "fresher":
                # Severe penalty if job is Senior / Staff / Lead / Principal / 5+ yrs
                if any(k in combined_text for k in ["senior", "lead", "principal", "staff", "architect", "director", "5+ years", "6+ years", "7+ years", "8+ years"]):
                    adjusted_dist += 0.45
                elif job_tier == "senior":
                    adjusted_dist += 0.40
                elif job_tier == "mid":
                    adjusted_dist += 0.15
                elif job_tier in ("fresher", "junior") or "intern" in combined_text or "graduate" in combined_text:
                    adjusted_dist = max(0.01, adjusted_dist - 0.15)

            elif user_tier == "junior":
                if any(k in combined_text for k in ["principal", "staff engineer", "architect", "director", "8+ years"]):
                    adjusted_dist += 0.35
                elif job_tier in ("junior", "mid", "fresher"):
                    adjusted_dist = max(0.01, adjusted_dist - 0.10)

            elif user_tier == "mid":
                if "intern" in role.lower():
                    adjusted_dist += 0.25
                elif job_tier in ("mid", "junior", "senior"):
                    adjusted_dist = max(0.01, adjusted_dist - 0.10)

            elif user_tier == "senior":
                if any(k in combined_text for k in ["intern", "trainee", "fresher"]):
                    adjusted_dist += 0.40
                elif any(k in combined_text for k in ["senior", "lead", "principal", "staff", "architect"]):
                    adjusted_dist = max(0.01, adjusted_dist - 0.15)

            new_sim = round(max(0.0, min(1.0, 1.0 - adjusted_dist)), 4)
            item_copy = dict(item)
            item_copy["distance"] = round(adjusted_dist, 4)
            item_copy["similarity_score"] = new_sim
            scored_items.append(item_copy)

        scored_items.sort(key=lambda x: x["distance"])
        return scored_items[:top_k]

    def search_with_fallback(
        self,
        query_text: str,
        user_experience: Optional[str] = None,
        n_results: int = 3,
        threshold: Optional[float] = None
    ) -> Tuple[List[Dict[str, Any]], str, bool]:
        """Performs vector search trying 'live' data first with experience-based re-ranking.

        If poor match scores (best distance > threshold) or no live results exist,
        seamlessly falls back to 'excel' base permanent data.

        Returns:
          Tuple: (list_of_job_matches, source_used, is_fallback)
        """
        sim_threshold = threshold if threshold is not None else settings.SIMILARITY_DISTANCE_THRESHOLD
        matched_items: List[Dict[str, Any]] = []
        fetch_k = max(10, n_results * 3)

        # 1. Try 'live' data first
        live_count = self.count_by_source("live")
        logger.info("Attempting Chroma search with 'live' data first (Available live records: %d)...", live_count)

        if live_count > 0:
            live_results = self.query_jobs(query_text=query_text, source="live", n_results=fetch_k)
            documents = live_results.get("documents", [[]])[0]
            metadatas = live_results.get("metadatas", [[]])[0]
            distances = live_results.get("distances", [[]])[0] if "distances" in live_results else []

            if documents and distances:
                for doc, meta, dist in zip(documents, metadatas, distances):
                    matched_items.append({
                        "document": doc,
                        "metadata": meta,
                        "distance": round(dist, 4),
                        "similarity_score": round(max(0.0, 1.0 - dist), 4),
                        "source": "live"
                    })

                # Apply experience-based filtering and re-ranking
                reranked_live = self.rerank_by_experience(matched_items, user_experience, top_k=n_results)

                if reranked_live:
                    best_distance = reranked_live[0]["distance"]
                    logger.info("Live data search best distance (after exp rerank): %.4f (Threshold: %.4f)", best_distance, sim_threshold)

                    if best_distance <= sim_threshold:
                        logger.info("Matched %d records from 'live' data successfully.", len(reranked_live))
                        return reranked_live, "live", False
                    else:
                        logger.warning(
                            "Live matches yielded poor score (best distance %.4f > %.4f). Falling back to 'excel' data...",
                            best_distance, sim_threshold
                        )
            else:
                logger.warning("No documents returned for 'live' query. Falling back to 'excel' data...")
        else:
            logger.info("No 'live' records currently indexed. Falling back to permanent 'excel' baseline data...")

        # 2. Fallback to permanent 'excel' data
        excel_items: List[Dict[str, Any]] = []
        excel_results = self.query_jobs(query_text=query_text, source="excel", n_results=fetch_k)
        documents = excel_results.get("documents", [[]])[0]
        metadatas = excel_results.get("metadatas", [[]])[0]
        distances = excel_results.get("distances", [[]])[0] if "distances" in excel_results else [0.0] * len(documents)

        for doc, meta, dist in zip(documents, metadatas, distances):
            excel_items.append({
                "document": doc,
                "metadata": meta,
                "distance": round(dist, 4),
                "similarity_score": round(max(0.0, 1.0 - dist), 4),
                "source": "excel"
            })

        reranked_excel = self.rerank_by_experience(excel_items, user_experience, top_k=n_results)
        logger.info("Matched %d records from permanent 'excel' base data (fallback triggered).", len(reranked_excel))
        return reranked_excel, "excel", True

    def seed_excel_base_data(self, force: bool = False) -> int:
        """Seeds permanent fallback data (metadata={'source': 'excel'})."""
        current_excel_count = self.count_by_source("excel")
        if current_excel_count > 0 and not force:
            logger.info("ChromaDB already contains %d 'excel' base records. Skipping seeding.", current_excel_count)
            return current_excel_count

        if not os.path.exists(settings.BASE_SEED_FILE):
            logger.warning("Base seed file '%s' not found.", settings.BASE_SEED_FILE)
            return 0

        with open(settings.BASE_SEED_FILE, "r", encoding="utf-8") as f:
            seed_data = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for item in seed_data:
            job_id = item.get("id", f"excel_{uuid.uuid4().hex[:8]}")
            company = item.get("company", "Tech Company")
            title = item.get("title", "Software Engineer")
            skills = ", ".join(item.get("skills", []))
            tech_stack = item.get("tech_stack", "")
            description = item.get("description", "")
            url = item.get("url", "")
            exp = item.get("experience_level", "")

            # Formulate rich searchable document
            doc_text = (
                f"Company: {company}\n"
                f"Role: {title}\n"
                f"Experience Level: {exp}\n"
                f"Required Skills: {skills}\n"
                f"Tech Stack: {tech_stack}\n"
                f"Job Description: {description}"
            )

            documents.append(doc_text)
            metadatas.append({
                "source": "excel",
                "company": company,
                "title": title,
                "experience_level": exp,
                "skills": skills,
                "tech_stack": tech_stack,
                "url": url
            })
            ids.append(job_id)

        self.add_job_documents(documents=documents, metadatas=metadatas, ids=ids)
        logger.info("Seeded %d permanent 'excel' base records into ChromaDB.", len(documents))
        return len(documents)


chroma_manager = ChromaManager()
