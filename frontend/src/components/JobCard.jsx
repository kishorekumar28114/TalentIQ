import React from 'react';
import { motion } from 'framer-motion';
import { Building2, MapPin, Briefcase, Sparkles, CheckCircle2, ArrowUpRight, Lightbulb, ExternalLink } from 'lucide-react';

export default function JobCard({ fit, index }) {
  const matchPercentage = Math.round((fit.similarity_score || 0.85) * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.08 }}
      className="bg-[#111827] border border-slate-800 hover:border-slate-700 rounded-xl p-4 flex flex-col justify-between transition-all duration-200 shadow-sm"
    >
      <div>
        {/* Header: Company, Rank & Match Score Badge */}
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-indigo-400 font-bold text-xs shrink-0">
              {fit.company.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-wider">
                  #{index + 1} Match
                </span>
                <span className={`px-1.5 py-0.2 text-[9px] font-mono font-medium rounded ${
                  fit.source === 'live'
                    ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/60'
                    : 'bg-slate-900 text-slate-400 border border-slate-800'
                }`}>
                  {fit.source === 'live' ? '⚡ Live Crawl' : 'Base Index'}
                </span>
              </div>
              <h3 className="text-sm font-bold text-white mt-0.5 tracking-tight">
                {fit.company}
              </h3>
            </div>
          </div>

          {/* Match Score Badge */}
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/50 text-emerald-300 text-xs font-mono font-semibold">
            <Sparkles className="w-3 h-3 text-emerald-400" />
            <span>{matchPercentage}% Fit</span>
          </div>
        </div>

        {/* Job Title & Experience */}
        <div className="mt-3">
          <h4 className="text-xs font-bold text-slate-100">{fit.role}</h4>
          
          <div className="flex flex-wrap items-center gap-2.5 mt-1 text-[11px] text-slate-400">
            {fit.experience_level && (
              <span className="flex items-center gap-1">
                <Briefcase className="w-3 h-3 text-slate-500" />
                <span>{fit.experience_level}</span>
              </span>
            )}
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3 text-slate-500" />
              <span>HQ / Hybrid / Remote</span>
            </span>
          </div>
        </div>

        {/* Why You're a Fit Section (AI Rationale) */}
        <div className="mt-3 p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-1 text-[10px] font-mono font-semibold uppercase tracking-wider text-indigo-300 mb-1">
            <Sparkles className="w-3 h-3 text-indigo-400" />
            <span>AI Fit Assessment:</span>
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            {fit.why_perfect_fit}
          </p>
        </div>

        {/* Key Matching Skill Points */}
        {fit.key_matching_points && fit.key_matching_points.length > 0 && (
          <div className="mt-3 space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">Core Alignment:</span>
            {fit.key_matching_points.map((point, i) => (
              <div key={i} className="flex items-start gap-1.5 text-[11px] text-slate-300">
                <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
                <span className="line-clamp-1">{point}</span>
              </div>
            ))}
          </div>
        )}

        {/* Recommendations / Advice */}
        {fit.recommendations && (
          <div className="mt-2.5 p-2 rounded bg-slate-900/50 border border-slate-800/80 flex items-start gap-1.5 text-[10px] text-slate-400">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
            <span><strong className="text-slate-300">Strategy:</strong> {fit.recommendations}</span>
          </div>
        )}

      </div>

      {/* Apply Now Button */}
      <div className="mt-4 pt-3 border-t border-slate-800/80">
        <a
          href={fit.job_url || `https://www.google.com/search?q=${encodeURIComponent(fit.company + " " + fit.role + " careers")}`}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-xs transition-colors group/btn"
        >
          <span>Apply at {fit.company}</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
        </a>
      </div>

    </motion.div>
  );
}
