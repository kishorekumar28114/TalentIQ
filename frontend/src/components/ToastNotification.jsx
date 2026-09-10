import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export default function ToastNotification({ toast, onClose }) {
  if (!toast) return null;

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />,
    info: <Info className="w-5 h-5 text-indigo-600 shrink-0" />
  };

  const borders = {
    success: 'border-emerald-800/80 bg-[#0f172a] text-slate-100 shadow-xl shadow-emerald-950/20',
    error: 'border-rose-800/80 bg-[#0f172a] text-slate-100 shadow-xl shadow-rose-950/20',
    info: 'border-indigo-800/80 bg-[#0f172a] text-slate-100 shadow-xl shadow-indigo-950/20'
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 max-w-sm w-full px-2">
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, y: 15, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 15, scale: 0.95 }}
          className={`flex items-start gap-2.5 p-3 rounded-xl border ${borders[toast.type] || borders.info}`}
        >
          {icons[toast.type] || icons.info}
          <div className="flex-1 text-xs">
            <h4 className="font-semibold text-white tracking-tight">{toast.title || toast.type}</h4>
            <p className="mt-0.5 text-slate-300 text-[11px] leading-relaxed">{toast.message}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
