import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, FileText, AlertCircle, ArrowRight, X, Briefcase, Sparkles, CheckCircle } from 'lucide-react';
import ProgressStepper from './ProgressStepper';

export default function UploadZone({ onUpload, isUploading, uploadStep = 1, onLoadSample }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [experience, setExperience] = useState('Fresher');
  const [uploadError, setUploadError] = useState('');
  const [experienceError, setExperienceError] = useState('');

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setUploadError('');
    if (rejectedFiles && rejectedFiles.length > 0) {
      setUploadError('Valid PDF, JPEG, PNG, or TXT file required (under 10MB).');
      return;
    }
    if (acceptedFiles && acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpeg', '.jpg'],
      'image/png': ['.png'],
      'text/plain': ['.txt']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024
  });

  const handleSubmit = () => {
    setUploadError('');
    setExperienceError('');

    if (!selectedFile) {
      setUploadError('Please select or drop a resume document first.');
      return;
    }
    if (!experience || !experience.trim()) {
      setExperienceError('Current Experience level is required.');
      return;
    }
    onUpload(selectedFile, experience.trim());
  };

  const handleClear = () => {
    setSelectedFile(null);
    setUploadError('');
    setExperienceError('');
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-4 shadow-sm">
      
      {/* Panel Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <UploadCloud className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-semibold tracking-tight text-white uppercase font-mono">
            Ingest Candidate Profile
          </span>
        </div>
        <span className="text-[10px] font-mono text-slate-400">PDF • PNG • TXT</span>
      </div>

      {/* Multi-Step Progress Stepper when uploading */}
      <AnimatePresence>
        {isUploading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="py-2"
          >
            <ProgressStepper currentStep={uploadStep} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Form Area */}
      {!isUploading && (
        <div className="space-y-3">
          
          {/* Experience Selector */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="experience-input" className="text-[11px] font-medium text-slate-300 flex items-center gap-1">
                <Briefcase className="w-3 h-3 text-indigo-400" />
                <span>Experience Tier</span>
                <span className="text-rose-400">*</span>
              </label>
              <span className="text-[10px] font-mono text-slate-500">RAG Reranking</span>
            </div>

            {/* Segmented Button Group */}
            <div className="grid grid-cols-4 gap-1 p-0.5 bg-slate-900/90 border border-slate-800 rounded-lg">
              {[
                { id: 'Fresher', label: 'Fresher' },
                { id: '1-2 Years', label: '1-2 Yrs' },
                { id: '3-5 Years', label: '3-5 Yrs' },
                { id: '5+ Years', label: '5+ Yrs' }
              ].map((tier) => (
                <button
                  key={tier.id}
                  type="button"
                  onClick={() => {
                    setExperience(tier.id);
                    if (experienceError) setExperienceError('');
                  }}
                  className={`py-1 text-[11px] font-medium rounded-md transition-all cursor-pointer ${
                    experience === tier.id
                      ? 'bg-indigo-600 text-white shadow-xs font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  {tier.label}
                </button>
              ))}
            </div>

            {experienceError && (
              <p className="text-[11px] text-rose-400 mt-1 flex items-center gap-1 font-medium">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>{experienceError}</span>
              </p>
            )}
          </div>

          {/* Dropzone Area */}
          <div
            {...getRootProps()}
            className={`border border-dashed rounded-lg p-5 text-center cursor-pointer transition-all ${
              isDragActive
                ? 'border-indigo-500 bg-indigo-950/20'
                : selectedFile
                ? 'border-indigo-500/50 bg-indigo-950/10'
                : 'border-slate-700/80 hover:border-slate-600 bg-slate-900/40 hover:bg-slate-900/70'
            }`}
          >
            <input {...getInputProps()} />

            {selectedFile ? (
              <div className="flex items-center justify-between gap-3 text-left">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 rounded bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-200 truncate">{selectedFile.name}</p>
                    <p className="text-[10px] font-mono text-slate-500">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Click to replace
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClear();
                  }}
                  className="p-1 text-slate-400 hover:text-rose-400 rounded hover:bg-slate-800 transition-colors"
                  title="Remove file"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center space-y-1.5 py-1">
                <UploadCloud className="w-5 h-5 text-slate-400" />
                <p className="text-xs font-medium text-slate-300">
                  Drop candidate resume here, or <span className="text-indigo-400 font-semibold underline">browse</span>
                </p>
                <p className="text-[10px] text-slate-500">Parsed via Groq LLM & synced to Cloudinary</p>
              </div>
            )}
          </div>

          {uploadError && (
            <div className="flex items-center gap-1.5 p-2 rounded bg-rose-950/40 border border-rose-800/60 text-[11px] text-rose-300">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-400" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Action Row */}
          <div className="flex items-center justify-between pt-1">
            {onLoadSample && !selectedFile && (
              <button
                type="button"
                onClick={onLoadSample}
                className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer flex items-center gap-1"
              >
                <Sparkles className="w-3 h-3" />
                <span>Load Sample Profile</span>
              </button>
            )}

            {selectedFile && (
              <button
                type="button"
                onClick={handleSubmit}
                className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all shadow-sm shadow-indigo-600/20 active:scale-[0.99] cursor-pointer"
              >
                <span>Run Vector Matchmaking</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

        </div>
      )}

    </div>
  );
}
