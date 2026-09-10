import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, X, CheckCircle2, Database, ShieldCheck } from 'lucide-react';

export default function AdminToggle({ isOpen, onClose, onTrigger, isScraping, scrapeResult }) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 10 }}
          className="bg-[#111827] border border-slate-800 max-w-lg w-full rounded-xl p-5 shadow-2xl relative overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-3.5 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white tracking-tight">Live Market Ingestion Hub</h3>
                <p className="text-[11px] text-slate-400">DuckDuckGo crawler sync into ChromaDB vector index</p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Workflow Steps */}
          <div className="my-4 p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-2 text-xs text-slate-300">
            <div className="flex items-center gap-1.5 text-white font-semibold">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span>Crawler Pipeline Operations:</span>
            </div>
            <ol className="list-decimal list-inside space-y-1 text-slate-400 pl-1 text-[11px] font-mono">
              <li>Purges dynamic <code className="text-indigo-400">source="live"</code> ChromaDB embeddings.</li>
              <li>Iterates across target enterprise organizations.</li>
              <li>Crawls live postings & tech stacks via DuckDuckGo (<code className="text-indigo-400">ddgs</code>).</li>
              <li>Generates vectors and stores records into ChromaDB.</li>
            </ol>
          </div>

          {/* Scrape Result */}
          {scrapeResult && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-xs space-y-1">
              <div className="flex items-center gap-1.5 text-emerald-300 font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Market Sync Completed in {scrapeResult.elapsed_seconds}s</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-slate-300 pt-1 text-[11px] font-mono">
                <div>Purged Stale Live: <strong className="text-white">{scrapeResult.deleted_previous_live_records}</strong></div>
                <div>Fresh Records Ingested: <strong className="text-emerald-400">{scrapeResult.total_new_records_ingested}</strong></div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Close
            </button>

            <button
              onClick={onTrigger}
              disabled={isScraping}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-xs disabled:opacity-50 transition-colors cursor-pointer"
            >
              <RefreshCw className={`w-3 h-3 ${isScraping ? 'animate-spin text-white' : ''}`} />
              <span>{isScraping ? 'Crawling & Indexing...' : 'Start Ingestion'}</span>
            </button>
          </div>

        </motion.div>
      </div>
    </AnimatePresence>
  );
}
