import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Briefcase, Award, Code, ExternalLink, Sparkles, Compass, ChevronDown, ChevronUp } from 'lucide-react';

export default function CandidateProfileCard({ profile, cloudinaryUrl, sourceUsed, isFallback }) {
  const [isExpanded, setIsExpanded] = useState(false);
  if (!profile) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-[#111827] border border-slate-800 rounded-xl p-4 shadow-sm"
    >
      {/* Dossier Header */}
      <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-sm">
            {profile.name ? profile.name.charAt(0).toUpperCase() : <User className="w-5 h-5" />}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-white tracking-tight">{profile.name || "Candidate Profile"}</h2>
              <span className="px-2 py-0.5 text-[10px] font-mono font-semibold text-indigo-300 bg-indigo-950/60 border border-indigo-800/60 rounded">
                {profile.provided_experience || (profile.years_of_experience ? `${profile.years_of_experience}y Exp` : "Fresher")}
              </span>
            </div>
            
            <p className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-1.5">
              <Briefcase className="w-3 h-3 text-slate-500 shrink-0" />
              <span className="truncate max-w-[240px]">{profile.role_preferences?.join(' • ') || "Software Engineer"}</span>
            </p>
          </div>
        </div>

        {/* Cloudinary Link */}
        {cloudinaryUrl && (
          <a
            href={cloudinaryUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 px-2 py-1 rounded bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-[10px] font-mono font-medium text-slate-300 hover:text-white transition-colors"
          >
            <ExternalLink className="w-2.5 h-2.5 text-indigo-400" />
            <span>PDF Source</span>
          </a>
        )}
      </div>

      {/* AI Executive Summary */}
      {profile.summary && (
        <div className="mt-3 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-300 leading-relaxed">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-wider text-indigo-400 font-semibold mb-1 block">
              AI Talent Evaluation Brief
            </span>
          </div>
          <p className="line-clamp-3 hover:line-clamp-none transition-all cursor-pointer">
            {profile.summary}
          </p>
        </div>
      )}

      {/* Technical Stack Pills */}
      <div className="mt-3">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Code className="w-3 h-3 text-indigo-400" />
            <span>Verified Skills ({profile.technical_skills?.length || 0})</span>
          </span>
          {profile.technical_skills?.length > 8 && (
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-0.5 cursor-pointer"
            >
              <span>{isExpanded ? 'Less' : 'More'}</span>
              {isExpanded ? <ChevronUp className="w-2.5 h-2.5" /> : <ChevronDown className="w-2.5 h-2.5" />}
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-1">
          {(isExpanded ? profile.technical_skills : profile.technical_skills?.slice(0, 8))?.map((skill, i) => (
            <span key={i} className="px-2 py-0.5 text-[10px] font-mono text-slate-300 bg-slate-900 border border-slate-800 rounded">
              {skill}
            </span>
          ))}
        </div>
      </div>

      {/* Domains & Strengths Row */}
      {profile.domain_experience?.length > 0 && (
        <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center gap-2 text-[10px] text-slate-400">
          <Compass className="w-3 h-3 text-slate-500 shrink-0" />
          <span className="font-mono text-slate-500">Domains:</span>
          <div className="flex flex-wrap gap-1">
            {profile.domain_experience.slice(0, 3).map((dom, i) => (
              <span key={i} className="text-slate-300 font-medium">
                {dom}{i < Math.min(2, profile.domain_experience.length - 1) ? ',' : ''}
              </span>
            ))}
          </div>
        </div>
      )}

    </motion.div>
  );
}
