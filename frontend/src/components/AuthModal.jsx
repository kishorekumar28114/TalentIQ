import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  X, 
  Mail, 
  Lock, 
  User, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  Loader2, 
  ShieldCheck, 
  CloudUpload,
  AlertCircle
} from 'lucide-react';

export default function AuthModal({ isOpen, onClose, onAuthSuccess, initialMode = 'login' }) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState(initialMode); // 'login' or 'register'
  const [showPassword, setShowPassword] = useState(false);
  
  // Form states
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // UI states
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (mode === 'register') {
      if (!fullName.trim()) {
        setErrorMessage('Please provide your full name.');
        return;
      }
      if (password.length < 6) {
        setErrorMessage('Password must be at least 6 characters long.');
        return;
      }
      if (password !== confirmPassword) {
        setErrorMessage('Passwords do not match.');
        return;
      }
    }

    try {
      setIsLoading(true);
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(fullName, email, password);
      }

      onClose();
      if (onAuthSuccess) {
        onAuthSuccess(mode);
      }
    } catch (err) {
      console.error('Auth error:', err);
      const detail = err.response?.data?.detail;
      setErrorMessage(detail || err.message || 'Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setErrorMessage('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs transition-opacity animate-in fade-in duration-200">
      
      {/* Modal Dialog Card */}
      <div 
        className="relative w-full max-w-md bg-[#111827] rounded-xl shadow-2xl border border-slate-800 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Banner */}
        <div className="bg-[#0f172a] p-5 text-white text-center relative border-b border-slate-800">
          <button
            onClick={onClose}
            className="absolute top-3.5 right-3.5 p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
            title="Close modal"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 mx-auto flex items-center justify-center mb-2">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
          </div>

          <h2 className="text-base font-bold tracking-tight text-white">
            {mode === 'login' ? 'Candidate Authentication' : 'Create Recruiter/Candidate Account'}
          </h2>
          <p className="text-[11px] text-slate-400 mt-0.5 max-w-xs mx-auto font-mono">
            {mode === 'login' 
              ? 'Access mapped Cloudinary dossiers & past RAG matches' 
              : 'Join TALENTIQ platform with persistent MongoDB storage'}
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="grid grid-cols-2 p-1 bg-slate-900 border-b border-slate-800">
          <button
            type="button"
            onClick={() => switchMode('login')}
            className={`py-1.5 text-xs font-medium rounded-md transition-all cursor-pointer ${
              mode === 'login'
                ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => switchMode('register')}
            className={`py-1.5 text-xs font-medium rounded-md transition-all cursor-pointer ${
              mode === 'register'
                ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Register Account
          </button>
        </div>

        {/* Form Body */}
        <div className="p-5">
          {errorMessage && (
            <div className="mb-3.5 p-2.5 rounded-lg bg-rose-950/40 border border-rose-800/60 flex items-start gap-2 text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            
            {/* Full Name */}
            {mode === 'register' && (
              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <User className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Alex Chen"
                    className="w-full pl-8 pr-3 py-2 text-xs bg-slate-900 border border-slate-800 rounded-lg focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-hidden transition-all placeholder:text-slate-500 text-white"
                  />
                </div>
              </div>
            )}

            {/* Email Address */}
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="alex.chen@example.com"
                  className="w-full pl-8 pr-3 py-2 text-xs bg-slate-900 border border-slate-800 rounded-lg focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-hidden transition-all placeholder:text-slate-500 text-white"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === 'register' ? 'Min 6 characters' : 'Enter account password'}
                  className="w-full pl-8 pr-9 py-2 text-xs bg-slate-900 border border-slate-800 rounded-lg focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-hidden transition-all placeholder:text-slate-500 text-white"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Confirm Password (Register mode only) */}
            {mode === 'register' && (
              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                    className="w-full pl-8 pr-3 py-2 text-xs bg-slate-900 border border-slate-800 rounded-lg focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-hidden transition-all placeholder:text-slate-500 text-white"
                  />
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-xs transition-all flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>{mode === 'login' ? 'Authenticating...' : 'Registering...'}</span>
                </>
              ) : (
                <>
                  <span>{mode === 'login' ? 'Sign In to Workspace' : 'Create Free Account'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>

          </form>

          {/* Cloudinary Integration Badge */}
          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-center gap-1.5 text-[10px] font-mono text-slate-400">
            <CloudUpload className="w-3 h-3 text-indigo-400" />
            <span>Encrypted JWT Sessions • Cloudinary Storage</span>
          </div>

        </div>

      </div>
    </div>
  );
}
