import React from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, Cpu, Database, Sparkles, Check } from 'lucide-react';

export default function ProgressStepper({ currentStep = 1 }) {
  const steps = [
    { id: 1, label: 'Hosting Resume', icon: UploadCloud, detail: 'Cloudinary storage' },
    { id: 2, label: 'AI Extraction', icon: Cpu, detail: 'Groq candidate JSON' },
    { id: 3, label: 'ChromaDB RAG', icon: Database, detail: 'Semantic distance query' },
    { id: 4, label: 'Fit Synthesis', icon: Sparkles, detail: 'Top 3 corporate fits' }
  ];

  const progressPercentage = Math.min(100, ((currentStep - 1) / (steps.length - 1)) * 100);

  return (
    <div className="w-full p-3 bg-slate-900/90 border border-slate-800 rounded-xl shadow-xs">
      {/* Step Header */}
      <div className="flex items-center justify-between mb-2.5">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-semibold">
            Ingestion Pipeline
          </span>
          <h4 className="text-xs font-bold text-white tracking-tight">
            Step {currentStep} of {steps.length}: {steps[currentStep - 1]?.label}
          </h4>
        </div>
        <div className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
          {Math.round(progressPercentage)}%
        </div>
      </div>

      {/* Progress Bar Track */}
      <div className="relative mb-3">
        <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-indigo-500 rounded-full"
            initial={{ width: '0%' }}
            animate={{ width: `${progressPercentage}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Steps Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
        {steps.map((step) => {
          const isCompleted = currentStep > step.id;
          const isCurrent = currentStep === step.id;
          const StepIcon = step.icon;

          return (
            <div
              key={step.id}
              className={`p-2 rounded-lg border text-left transition-all ${
                isCompleted
                  ? 'bg-emerald-950/30 border-emerald-800/50 text-emerald-300'
                  : isCurrent
                  ? 'bg-indigo-950/40 border-indigo-700/60 text-indigo-200 ring-1 ring-indigo-500/30'
                  : 'bg-slate-900/50 border-slate-800 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div
                  className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-mono font-bold ${
                    isCompleted
                      ? 'bg-emerald-600 text-white'
                      : isCurrent
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {isCompleted ? <Check className="w-3 h-3" /> : step.id}
                </div>

                <StepIcon
                  className={`w-3 h-3 ${
                    isCompleted
                      ? 'text-emerald-400'
                      : isCurrent
                      ? 'text-indigo-400 animate-pulse'
                      : 'text-slate-500'
                  }`}
                />
              </div>

              <div className="text-[11px] font-semibold truncate text-slate-200">
                {step.label}
              </div>
              <div className="text-[9px] font-mono text-slate-500 truncate mt-0.5">
                {step.detail}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
