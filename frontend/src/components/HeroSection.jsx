import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Database, Search, Bot } from 'lucide-react';

export default function HeroSection() {
  return (
    <div className="pt-8 pb-6 text-center max-w-4xl mx-auto px-4">
      
      {/* Top Feature Pill */}
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-xs font-semibold text-indigo-700 mb-4"
      >
        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
        <span>Agentic RAG Engine Powered by Groq Llama-3 & ChromaDB</span>
      </motion.div>

      {/* Headline */}
      <motion.h1 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight"
      >
        Find Your Perfect Tech Role with{' '}
        <span className="text-indigo-600">AI Precision</span>
      </motion.h1>

      {/* Subtitle */}
      <motion.p 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="mt-3 text-base text-slate-600 max-w-2xl mx-auto leading-relaxed"
      >
        Upload your resume to instantly match with top tech companies, extract candidate profile insights, 
        and converse with our stateful LangGraph agent.
      </motion.p>

      {/* Feature Highlights Grid */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="mt-6 flex flex-wrap justify-center gap-2.5 text-xs text-slate-600"
      >
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-white border border-slate-200 shadow-2xs">
          <Database className="w-3.5 h-3.5 text-indigo-600" />
          <span>Two-Tier ChromaDB (Live + Base)</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-white border border-slate-200 shadow-2xs">
          <Search className="w-3.5 h-3.5 text-indigo-600" />
          <span>DDGS Live Web Scraping</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-white border border-slate-200 shadow-2xs">
          <Bot className="w-3.5 h-3.5 text-indigo-600" />
          <span>LangGraph MongoDB Agent</span>
        </div>
      </motion.div>

    </div>
  );
}
