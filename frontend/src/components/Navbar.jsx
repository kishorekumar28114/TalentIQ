import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Sparkles, 
  RefreshCw, 
  MessageSquare, 
  Briefcase, 
  ShieldCheck, 
  User, 
  LogOut, 
  LogIn, 
  Cloud, 
  ExternalLink,
  Activity,
  Layers
} from 'lucide-react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  onTriggerLiveScraping, 
  isScrapingLive,
  backendConnected,
  onOpenAuth
}) {
  const { user, isAuthenticated, logout } = useAuth();
  const hasResume = !!user?.resume?.cloudinary_url;

  return (
    <header className="sticky top-0 z-40 w-full bg-[#0d1322]/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-13 flex items-center justify-between gap-4">
        
        {/* Brand Anchor */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-sm shadow-indigo-500/20">
            <Layers className="w-3.5 h-3.5" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-bold tracking-tight text-white">
              TALENT<span className="text-indigo-400">IQ</span>
            </span>
            <span className="hidden md:inline-block px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-wider text-slate-400 bg-slate-800/60 border border-slate-700/60 rounded">
              Agentic RAG
            </span>
          </div>
        </div>

        {/* Dynamic Navigation Tabs */}
        <nav className="flex items-center p-0.5 bg-slate-900/80 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('matchmaker')}
            className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-all cursor-pointer ${
              activeTab === 'matchmaker'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Matchmaker Studio</span>
          </button>
          
          <button
            onClick={() => setActiveTab('agent')}
            className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-all cursor-pointer ${
              activeTab === 'agent'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Recruiter Agent</span>
          </button>
        </nav>

        {/* Live Status & Action Buttons */}
        <div className="flex items-center gap-2.5">
          
          {/* Backend Health Badge */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900/60 border border-slate-800 text-[11px] font-mono text-slate-300">
            <span className={`w-1.5 h-1.5 rounded-full ${backendConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span>{backendConnected ? 'Vector Index Ready' : 'Index Disconnected'}</span>
          </div>

          {/* Sync Trigger Button */}
          <button
            onClick={onTriggerLiveScraping}
            disabled={isScrapingLive}
            title="Trigger live DuckDuckGo web crawler into ChromaDB"
            className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-700/60 rounded-md transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3 h-3 ${isScrapingLive ? 'animate-spin text-indigo-400' : 'text-slate-400'}`} />
            <span>Sync Live Market</span>
          </button>

          {/* User Profile / Auth Area */}
          {isAuthenticated ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
              {hasResume && (
                <a
                  href={user.resume.cloudinary_url}
                  target="_blank"
                  rel="noreferrer"
                  title="View Cloudinary Resume"
                  className="hidden md:flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono text-indigo-300 bg-indigo-950/50 border border-indigo-800/60 rounded hover:bg-indigo-900/50 transition-colors"
                >
                  <Cloud className="w-3 h-3 text-indigo-400" />
                  <span>Cloudinary Mapped</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              )}

              <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-900 border border-slate-800 text-xs text-slate-200">
                <User className="w-3.5 h-3.5 text-indigo-400" />
                <span className="font-medium max-w-[100px] truncate">{user?.name || user?.email?.split('@')[0]}</span>
              </div>

              <button
                onClick={logout}
                title="Sign out"
                className="p-1.5 text-slate-400 hover:text-rose-400 rounded-md hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => onOpenAuth('login')}
                className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-md transition-all cursor-pointer"
              >
                <LogIn className="w-3 h-3" />
                <span>Sign In</span>
              </button>
              <button
                onClick={() => onOpenAuth('register')}
                className="hidden sm:inline-flex px-2.5 py-1 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-md transition-all shadow-xs cursor-pointer"
              >
                Register
              </button>
            </div>
          )}

        </div>
      </div>
    </header>
  );
}
