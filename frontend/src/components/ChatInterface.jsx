import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import MarkdownRenderer from './MarkdownRenderer';
import { 
  Bot, 
  User, 
  Send, 
  Loader2, 
  Globe, 
  Database, 
  ExternalLink, 
  RefreshCw, 
  MessageSquare, 
  Sparkles,
  Copy,
  Check,
  RotateCcw,
  Compass,
  Terminal,
  Layers,
  Cpu
} from 'lucide-react';

export default function ChatInterface({ onShowToast }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'agent',
      text: "👋 **Enterprise Talent Intelligence & Recruiter Agent Online.**\n\nI am connected to your two-tier ChromaDB vector store and equipped with autonomous DuckDuckGo live web intelligence.\n\n- **Internal Index**: Query roles, engineering requirements, and salary levels for target companies.\n- **Autonomous Web Search**: If a company or role is absent from the local index, I will autonomously search live web postings and engineering blogs.",
      toolsUsed: ['search_job_market_database'],
      citations: []
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  
  // Persistent session thread ID for MongoDB state checkpointer
  const [threadId, setThreadId] = useState(() => {
    return localStorage.getItem('jobfit_thread_id') || `thread_${Math.random().toString(36).substring(2, 11)}`;
  });

  useEffect(() => {
    localStorage.setItem('jobfit_thread_id', threadId);
  }, [threadId]);

  const messagesEndRef = useRef(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || isLoading) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text
    };

    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const res = await axios.post('/api/chat', {
        message: text,
        thread_id: threadId
      });

      if (res.data && res.data.success) {
        const agentMsg = {
          id: (Date.now() + 1).toString(),
          sender: 'agent',
          text: res.data.response,
          toolsUsed: res.data.tools_used || [],
          citations: res.data.citations || []
        };
        setMessages(prev => [...prev, agentMsg]);
      } else {
        throw new Error(res.data?.message || 'Chat response failed');
      }
    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'agent',
        text: '⚠️ **Agent connection interrupted.** Please check that the FastAPI server is running.',
        toolsUsed: [],
        citations: []
      };
      setMessages(prev => [...prev, errorMsg]);
      if (onShowToast) {
        onShowToast({ type: 'error', title: 'Agent Offline', message: 'Could not connect to Chat API' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleResetChat = () => {
    const newThreadId = `thread_${Math.random().toString(36).substring(2, 11)}`;
    setThreadId(newThreadId);
    setMessages([
      {
        id: 'welcome',
        sender: 'agent',
        text: "👋 **New Session Initialized.** How can I assist your engineering recruitment or career intelligence inquiry?",
        toolsUsed: [],
        citations: []
      }
    ]);
  };

  const quickPrompts = [
    "What engineering roles does Google look for?",
    "Tell me about software engineering jobs at Palantir.",
    "What tech stack does Stripe use for payment infrastructure?",
    "Which companies look for FastAPI, Docker, and Kubernetes?",
    "Hiring requirements for Junior Full-Stack Developer at Razorpay?"
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 h-[calc(100dvh-64px)] py-2 flex flex-col md:flex-row gap-4 overflow-hidden">
      
      {/* Left Sidebar: Session Control & Prompt Library */}
      <div className="hidden md:flex w-72 flex-col gap-3 shrink-0">
        
        {/* Agent Metadata Card */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-3.5 space-y-3">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <Cpu className="w-3.5 h-3.5" />
              </div>
              <span className="text-xs font-semibold text-white tracking-tight">Agent Engine</span>
            </div>
            <span className="flex items-center gap-1 px-2 py-0.5 text-[9px] font-mono text-emerald-300 bg-emerald-950/60 border border-emerald-800/60 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Active</span>
            </span>
          </div>

          <div className="space-y-1.5 text-[11px] font-mono text-slate-400">
            <div className="flex items-center justify-between">
              <span>LLM Engine:</span>
              <span className="text-slate-200">Groq Llama-3 / Qwen</span>
            </div>
            <div className="flex items-center justify-between">
              <span>RAG Store:</span>
              <span className="text-slate-200">ChromaDB job_market</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Fallback:</span>
              <span className="text-slate-200">DuckDuckGo Autonomous</span>
            </div>
            <div className="flex items-center justify-between">
              <span>State Store:</span>
              <span className="text-slate-200">MongoDB Checkpointer</span>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
            <span className="text-[10px] font-mono text-slate-500 truncate max-w-[140px]">
              ID: {threadId.slice(0, 14)}...
            </span>
            <button
              onClick={handleResetChat}
              title="Reset conversation thread"
              className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[10px] font-medium text-slate-300 transition-colors cursor-pointer"
            >
              <RotateCcw className="w-2.5 h-2.5" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Quick Query Library */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-3.5 flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="flex items-center gap-1.5 pb-2 mb-2 border-b border-slate-800 text-xs font-semibold text-slate-300">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Corporate Queries</span>
          </div>
          
          <div className="space-y-1.5 overflow-y-auto pr-1 flex-1">
            {quickPrompts.map((prompt, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(prompt)}
                disabled={isLoading}
                className="w-full text-left p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 text-[11px] text-slate-300 hover:text-white transition-all disabled:opacity-50 cursor-pointer line-clamp-2"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* Main Terminal Viewport */}
      <div className="flex-1 bg-[#111827] border border-slate-800 rounded-xl flex flex-col h-full shadow-sm overflow-hidden min-w-0">
        
        {/* Terminal Header */}
        <div className="px-4 py-2.5 border-b border-slate-800 bg-[#0f172a]/90 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-indigo-400" />
            <span className="text-xs font-bold text-white tracking-tight">Recruiter Intelligence Session</span>
            <span className="hidden sm:inline-block px-1.5 py-0.2 text-[9px] font-mono text-slate-400 bg-slate-800 rounded">
              thread: {threadId}
            </span>
          </div>

          <div className="flex items-center gap-2 md:hidden">
            <button
              onClick={handleResetChat}
              className="flex items-center gap-1 px-2 py-1 text-[11px] rounded bg-slate-800 text-slate-300"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-[#0b0f19]/60">
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className={`flex gap-2.5 group ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'agent' && (
                <div className="w-7 h-7 rounded bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5" />
                </div>
              )}

              <div className={`relative max-w-[85%] md:max-w-[80%] rounded-xl p-3.5 text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-[#111827] text-slate-200 border border-slate-800 shadow-xs'
              }`}>
                
                {/* Agent Action Badges */}
                {msg.toolsUsed && msg.toolsUsed.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 mb-2.5 pb-2 border-b border-slate-800/80">
                    <span className="text-[9px] uppercase font-mono font-bold text-slate-400 tracking-wider">
                      Action Executed:
                    </span>
                    {msg.toolsUsed.map((tool, idx) => (
                      <span 
                        key={idx} 
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-indigo-300"
                      >
                        {tool.includes('web') ? (
                          <Globe className="w-2.5 h-2.5 text-indigo-400" />
                        ) : (
                          <Database className="w-2.5 h-2.5 text-indigo-400" />
                        )}
                        <span>
                          {tool === 'search_web_for_jobs' 
                            ? 'Live DuckDuckGo Crawler' 
                            : tool === 'search_job_market_database' 
                            ? 'ChromaDB Job Market' 
                            : tool}
                        </span>
                      </span>
                    ))}
                  </div>
                )}

                {/* Message Text */}
                {msg.sender === 'agent' ? (
                  <MarkdownRenderer content={msg.text} />
                ) : (
                  <div className="whitespace-pre-wrap font-sans text-white text-xs leading-relaxed">
                    {msg.text}
                  </div>
                )}

                {/* Citations / External Sources */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-1">
                    <span className="text-[9px] font-mono font-bold text-slate-400 uppercase tracking-wider block">
                      Sources & Citations:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.citations.map((cite, i) => (
                        <a
                          key={i}
                          href={cite.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[10px] font-mono text-indigo-300 hover:text-indigo-200 transition-colors"
                        >
                          <ExternalLink className="w-2.5 h-2.5" />
                          <span>Source [{i+1}]</span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Copy Button */}
                {msg.sender === 'agent' && (
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleCopy(msg.text, msg.id)}
                      title="Copy response"
                      className="p-1 rounded bg-slate-900/80 hover:bg-slate-800 border border-slate-700/60 text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      {copiedId === msg.id ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </div>
                )}

              </div>

              {msg.sender === 'user' && (
                <div className="w-7 h-7 rounded bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-0.5 text-xs font-bold">
                  U
                </div>
              )}
            </motion.div>
          ))}

          {/* Agent Loading Indicator */}
          {isLoading && (
            <motion.div 
              initial={{ opacity: 0, y: 5 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="flex gap-2.5 items-center"
            >
              <div className="w-7 h-7 rounded bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <Bot className="w-3.5 h-3.5" />
              </div>
              <div className="bg-[#111827] border border-slate-800 px-3 py-2 rounded-xl text-xs text-slate-300 flex items-center gap-2 shadow-xs">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                <span className="font-mono text-[11px]">Executing ChromaDB lookup & autonomous search...</span>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-2.5 bg-[#0f172a] border-t border-slate-800 flex items-center gap-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask about target companies, engineering requirements, salary benchmarks... (Enter to send)"
            rows={1}
            disabled={isLoading}
            className="flex-1 bg-slate-900 text-xs text-slate-100 placeholder-slate-500 rounded-lg px-3 py-2 border border-slate-800 focus:outline-hidden focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 resize-none font-sans"
          />

          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0 shadow-xs cursor-pointer"
            title="Send Message"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>

    </div>
  );
}
