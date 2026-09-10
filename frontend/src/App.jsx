import React, { useState, useEffect } from 'react';
import axios from 'axios';
import confetti from 'canvas-confetti';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import UploadZone from './components/UploadZone';
import CandidateProfileCard from './components/CandidateProfileCard';
import JobCard from './components/JobCard';
import ChatInterface from './components/ChatInterface';
import AdminToggle from './components/AdminToggle';
import ToastNotification from './components/ToastNotification';
import AuthModal from './components/AuthModal';
import { 
  Sparkles, 
  MessageSquare, 
  Cloud, 
  Database, 
  Search, 
  Layers, 
  Cpu, 
  CheckCircle2, 
  ExternalLink,
  Activity,
  ArrowUpRight,
  Briefcase
} from 'lucide-react';

function AppContent() {
  const { user, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState('matchmaker');
  const [backendConnected, setBackendConnected] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState(1);
  const [isScrapingLive, setIsScrapingLive] = useState(false);
  const [isAdminModalOpen, setIsAdminModalOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('login');
  const [matchResult, setMatchResult] = useState(null);
  const [scrapeResult, setScrapeResult] = useState(null);
  const [toast, setToast] = useState(null);

  // Check Backend Health on Mount
  useEffect(() => {
    checkHealth();
  }, []);

  // When user logs in, if they have a mapped resume in Cloudinary, load their profile into view
  useEffect(() => {
    if (user?.resume?.candidate_profile && !matchResult) {
      setMatchResult({
        success: true,
        message: 'Loaded mapped Cloudinary resume profile.',
        candidate_profile: user.resume.candidate_profile,
        cloudinary_url: user.resume.cloudinary_url,
        source_used: 'Cloudinary User Account',
        is_fallback: false,
        top_company_fits: user.resume.top_company_fits || []
      });
    }
  }, [user]);

  const checkHealth = async () => {
    try {
      const res = await axios.get('/api/health');
      if (res.status === 200 && res.data.status === 'healthy') {
        setBackendConnected(true);
      }
    } catch (err) {
      console.warn('Backend health check failed:', err);
      setBackendConnected(false);
    }
  };

  const showToast = ({ type, title, message }) => {
    setToast({ type, title, message });
    setTimeout(() => setToast(null), 5000);
  };

  const handleOpenAuth = (mode = 'login') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  // 1. Resume Match Pipeline Handler (POST /api/match/resume)
  const handleResumeUpload = async (file, experience = 'Fresher') => {
    setIsUploading(true);
    setUploadStep(1);

    const stepInterval = setInterval(() => {
      setUploadStep((prev) => (prev < 4 ? prev + 1 : prev));
    }, 1200);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('experience', experience);

    try {
      const res = await axios.post('/api/match/resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (res.data && res.data.success) {
        setUploadStep(4);
        setMatchResult(res.data);
        
        await refreshUser();

        showToast({
          type: 'success',
          title: 'Matching Complete',
          message: `Extracted profile, synced to Cloudinary, and evaluated top matches.`
        });

        confetti({
          particleCount: 60,
          spread: 55,
          origin: { y: 0.6 }
        });
      } else {
        throw new Error(res.data?.message || 'Failed to match resume');
      }
    } catch (err) {
      console.error('Resume upload error:', err);
      showToast({
        type: 'error',
        title: 'Matching Failed',
        message: err.response?.data?.detail || err.message || 'Could not connect to FastAPI server'
      });
    } finally {
      clearInterval(stepInterval);
      setIsUploading(false);
      setUploadStep(1);
    }
  };

  // Quick Load Sample Profile for Instant Demo/Testing
  const handleLoadSample = () => {
    setMatchResult({
      success: true,
      message: 'Loaded sample verified candidate profile.',
      cloudinary_url: 'https://res.cloudinary.com/demo/image/upload/sample_alex_chen_resume.pdf',
      candidate_profile: {
        name: 'Alex Chen',
        years_of_experience: 5.0,
        provided_experience: '3-5 Years (Mid/Senior)',
        role_preferences: ['Staff Backend Engineer', 'Distributed Systems Architect'],
        technical_skills: ['Python', 'FastAPI', 'Go', 'Docker', 'Kubernetes', 'Apache Kafka', 'Redis', 'MongoDB'],
        domain_experience: ['FinTech', 'Cloud Infrastructure', 'Distributed Data Stores'],
        summary: 'Senior Backend Engineer with 5+ years designing high-throughput microservices, distributed stores, and event streams. Architected high-concurrency event stream handling 50k req/sec with FastAPI and Kafka.'
      },
      source_used: 'live',
      is_fallback: false,
      top_company_fits: [
        {
          company: 'Stripe',
          role: 'Staff Infrastructure Engineer',
          experience_level: '3-5 Years (Mid/Senior)',
          source: 'live',
          similarity_score: 0.94,
          distance: 0.06,
          why_perfect_fit: "Alex's deep expertise in high-concurrency event processing with Kafka and FastAPI directly mirrors Stripe's global transaction ingestion pipelines. His proven background in reducing database read latency aligns with Stripe's 99.999% uptime mandate.",
          key_matching_points: ['High-throughput event streaming (50k req/sec)', 'FastAPI & Go microservice architectures', 'Distributed key-value caching (Redis)'],
          recommendations: 'Emphasize reliability engineering trade-offs and zero-downtime database migration experiences in the technical architectural interview.'
        },
        {
          company: 'Oracle',
          role: 'Principal Cloud Platform Engineer',
          experience_level: '3-5 Years',
          source: 'excel',
          similarity_score: 0.89,
          distance: 0.11,
          why_perfect_fit: "Alex's mastery over containerized Kubernetes orchestrations and Python backend services fits Oracle Cloud Infrastructure's distributed control plane requirements.",
          key_matching_points: ['Docker & Kubernetes cluster orchestration', 'Production-grade Python service design', 'Distributed systems telemetry'],
          recommendations: 'Showcase hands-on experience debugging asynchronous gRPC/REST APIs under packet loss conditions.'
        },
        {
          company: 'PhonePe',
          role: 'Senior Distributed Data Systems Engineer',
          experience_level: '3-5 Years',
          source: 'excel',
          similarity_score: 0.87,
          distance: 0.13,
          why_perfect_fit: "Alex's direct experience designing high-volume Kafka pipelines and MongoDB indexing satisfies PhonePe's transaction settlement scale.",
          key_matching_points: ['Distributed Kafka stream processing', 'MongoDB performance indexing', 'High-throughput payment event flow'],
          recommendations: 'Discuss architecture designs for maintaining transaction idempotency across distributed worker clusters.'
        }
      ]
    });

    showToast({
      type: 'info',
      title: 'Sample Profile Active',
      message: 'Loaded Staff Distributed Systems profile with 3 enterprise matches.'
    });
  };

  // 2. Admin Live Scraping Handler (POST /api/data/trigger-live)
  const handleTriggerLiveScraping = async () => {
    setIsScrapingLive(true);
    showToast({
      type: 'info',
      title: 'Crawler In Progress',
      message: 'Purging stale records and crawling live postings via DuckDuckGo...'
    });

    try {
      const res = await axios.post('/api/data/trigger-live');
      if (res.data && res.data.success) {
        setScrapeResult(res.data);
        setIsAdminModalOpen(true);
        showToast({
          type: 'success',
          title: 'Live Market Synced',
          message: `Ingested ${res.data.total_new_records_ingested} records across ${res.data.total_companies_processed} companies.`
        });
        checkHealth();
      } else {
        throw new Error(res.data?.message || 'Live scraping failed');
      }
    } catch (err) {
      console.error('Live scraping error:', err);
      showToast({
        type: 'error',
        title: 'Sync Error',
        message: err.response?.data?.detail || err.message || 'Error triggering live crawler'
      });
    } finally {
      setIsScrapingLive(false);
    }
  };

  return (
    <div className="h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans overflow-hidden">
      
      {/* Navigation Header (Fixed 52px) */}
      <Navbar 
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onTriggerLiveScraping={() => setIsAdminModalOpen(true)}
        isScrapingLive={isScrapingLive}
        backendConnected={backendConnected}
        onOpenAuth={handleOpenAuth}
      />

      {/* Main Workspace Area (Fit to Viewport) */}
      <main className="flex-1 overflow-hidden">
        {activeTab === 'matchmaker' ? (
          <div className="max-w-[1600px] mx-auto h-full p-3 lg:p-4 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
            
            {/* Left Column: Ingestion Hub & Candidate Dossier (lg:col-span-4) */}
            <div className="lg:col-span-4 flex flex-col gap-3 h-full overflow-y-auto pr-1">
              
              {/* Telemetry Indicator */}
              <div className="bg-[#111827] border border-slate-800 rounded-xl p-3 flex items-center justify-between shadow-xs">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                    <Activity className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white tracking-tight">RAG Matchmaking Engine</h3>
                    <p className="text-[10px] text-slate-400 font-mono">ChromaDB • Groq Llama-3 • Cloudinary</p>
                  </div>
                </div>

                <span className="px-2 py-0.5 text-[10px] font-mono text-emerald-300 bg-emerald-950/60 border border-emerald-800/60 rounded">
                  Two-Tier Ready
                </span>
              </div>

              {/* Cloudinary Notice for Logged-In User */}
              {user && user.resume?.cloudinary_url && (
                <div className="p-2.5 bg-indigo-950/30 border border-indigo-800/50 rounded-xl flex items-center justify-between text-xs text-indigo-200">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <Cloud className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span className="truncate text-[11px]">
                      Account Resume: <strong className="text-white font-medium">{user.resume.filename || 'resume.pdf'}</strong>
                    </span>
                  </div>
                  <a
                    href={user.resume.cloudinary_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] font-mono text-indigo-400 hover:text-indigo-300 underline shrink-0 ml-2"
                  >
                    View Cloudinary
                  </a>
                </div>
              )}

              {/* Upload & Ingestion Zone */}
              <UploadZone 
                onUpload={handleResumeUpload}
                isUploading={isUploading}
                uploadStep={uploadStep}
                onLoadSample={handleLoadSample}
              />

              {/* Candidate Profile Card */}
              {matchResult && matchResult.candidate_profile && (
                <CandidateProfileCard 
                  profile={matchResult.candidate_profile}
                  cloudinaryUrl={matchResult.cloudinary_url}
                  sourceUsed={matchResult.source_used}
                  isFallback={matchResult.is_fallback}
                />
              )}

            </div>

            {/* Right Column: RAG Match Intelligence (lg:col-span-8) */}
            <div className="lg:col-span-8 flex flex-col gap-3 h-full overflow-y-auto pr-1 min-w-0">
              
              {matchResult ? (
                <>
                  {/* Results Sub-Header Bar */}
                  <div className="bg-[#111827] border border-slate-800 rounded-xl px-4 py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-xs shrink-0">
                    <div>
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-indigo-400" />
                        <h2 className="text-xs font-bold text-white tracking-tight uppercase font-mono">
                          Market Alignment Analysis (Top 3 Matches)
                        </h2>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Synthesized via vector distance in ChromaDB and Groq fit evaluation
                      </p>
                    </div>

                    <button
                      onClick={() => setActiveTab('agent')}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-xs transition-colors cursor-pointer self-start sm:self-auto"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Deep Dive with Agent</span>
                    </button>
                  </div>

                  {/* Top 3 Matched Companies Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 flex-1">
                    {matchResult.top_company_fits?.map((fit, idx) => (
                      <JobCard key={idx} fit={fit} index={idx} />
                    ))}
                  </div>
                </>
              ) : (
                /* Empty / Readiness Executive State */
                <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 flex flex-col justify-between h-full shadow-sm">
                  
                  {/* Top Intro */}
                  <div className="space-y-4">
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-mono text-indigo-300">
                      <Sparkles className="w-3 h-3 text-indigo-400" />
                      <span>Two-Tier ChromaDB Market Intelligence</span>
                    </div>

                    <h2 className="text-2xl font-extrabold text-white tracking-tight">
                      Enterprise Agentic Career Matchmaking
                    </h2>

                    <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
                      Ingest candidate resumes to parse structured engineering profiles, compute semantic distance against 
                      verified company technical requirements, and autonomously explore real-time market postings with DuckDuckGo.
                    </p>

                    {/* Architecture Telemetry Bento */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                      <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="flex items-center gap-1.5 text-indigo-400 text-xs font-semibold">
                          <Database className="w-3.5 h-3.5" />
                          <span>Vector Store</span>
                        </div>
                        <p className="text-[11px] text-slate-300">ChromaDB <code className="text-indigo-300">job_market</code> with live/excel dual tiering.</p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="flex items-center gap-1.5 text-indigo-400 text-xs font-semibold">
                          <Search className="w-3.5 h-3.5" />
                          <span>Live Crawler</span>
                        </div>
                        <p className="text-[11px] text-slate-300">Autonomous web scraping for real-time hiring posts via DDGS.</p>
                      </div>

                      <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="flex items-center gap-1.5 text-indigo-400 text-xs font-semibold">
                          <Cpu className="w-3.5 h-3.5" />
                          <span>Groq LLM Engine</span>
                        </div>
                        <p className="text-[11px] text-slate-300">Candidate profile extraction and personalized fit synthesis.</p>
                      </div>
                    </div>
                  </div>

                  {/* Ready to Test Callout Banner */}
                  <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 via-slate-900 to-slate-900 border border-indigo-800/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div className="space-y-0.5">
                      <span className="text-xs font-bold text-white tracking-tight flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-indigo-400" />
                        <span>Instant Verification Mode Available</span>
                      </span>
                      <p className="text-[11px] text-slate-400">
                        Test the end-to-end vector matching pipeline immediately with a sample senior profile.
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={handleLoadSample}
                      className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors shadow-xs shrink-0 cursor-pointer"
                    >
                      Load Sample Profile
                    </button>
                  </div>

                </div>
              )}

            </div>

          </div>
        ) : (
          /* Agent Chat Tab */
          <div className="h-full">
            <ChatInterface onShowToast={showToast} />
          </div>
        )}
      </main>

      {/* Admin Control Modal */}
      <AdminToggle
        isOpen={isAdminModalOpen}
        onClose={() => setIsAdminModalOpen(false)}
        onTrigger={handleTriggerLiveScraping}
        isScraping={isScrapingLive}
        scrapeResult={scrapeResult}
      />

      {/* User Authentication Modal (Login / Register) */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
        onAuthSuccess={(mode) => {
          showToast({
            type: 'success',
            title: mode === 'login' ? 'Signed In' : 'Account Ready',
            message: mode === 'login' 
              ? 'Welcome back to TALENTIQ.' 
              : 'Account registered and linked to MongoDB.'
          });
        }}
      />

      {/* Toast Notification Banner */}
      <ToastNotification toast={toast} onClose={() => setToast(null)} />

    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
