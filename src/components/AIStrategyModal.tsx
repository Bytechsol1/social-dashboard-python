// ... (Imports logic) ...
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Sparkles, RefreshCw, Activity, Copy, CheckCircle2 } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function AIStrategyModal({ 
// ... (The rest of the function down to the markdown render logic) ...
  isOpen, 
  onClose, 
  videoId 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
  videoId: string | null;
}) {
  const [strategy, setStrategy] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && videoId && !strategy) {
      generateStrategy();
    }
    // Reset state when modal closes
    if (!isOpen) {
      setStrategy(null);
      setError('');
      setCopied(false);
    }
  }, [isOpen, videoId]);

  const generateStrategy = async () => {
    if (!videoId) return;
    
    setLoading(true);
    setError('');
    
    try {
      const res = await fetch('/api/ai/strategy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ video_id: videoId })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to generate strategy');
      }
      
      setStrategy(data.markdown);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (strategy) {
      navigator.clipboard.writeText(strategy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getMarkdownHtml = (mdContent: string) => {
    try {
        const rawHtml = marked.parse(mdContent);
        return { __html: DOMPurify.sanitize(rawHtml as string) };
    } catch (e) {
        return { __html: '<p>Error rendering markdown.</p>' };
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0B0E14]/80 backdrop-blur-sm p-4"
        >
          <motion.div
            initial={{ scale: 0.95, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: 20 }}
            className="w-full max-w-4xl bg-slate-50 dark:bg-[#161B22] border border-slate-200 dark:border-white/10 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
          >
            {/* Header */}
            <div className="flex justify-between items-center p-6 border-b border-slate-200 dark:border-white/10 shrink-0 bg-white/5">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-brand-yt/10 rounded-xl relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-brand-yt/20 to-purple-500/20 animate-pulse" />
                  <Sparkles className="w-5 h-5 text-brand-yt relative z-10" />
                </div>
                <div>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight">AI Viral Strategy Engine</h3>
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Cross-Platform Growth Analysis</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {strategy && !loading && (
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border border-white/5 hover:border-white/10"
                  >
                    {copied ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    {copied ? 'Copied to Clipboard' : 'Copy Full Strategy'}
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="p-2 bg-slate-200 dark:bg-white/5 rounded-xl hover:bg-slate-300 dark:hover:bg-white/10 transition-colors text-slate-600 dark:text-slate-400"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-6 bg-[#0B0E14] relative">
              {loading ? (
                <div className="flex flex-col items-center justify-center h-full min-h-[400px] space-y-6">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-slate-800 border-t-brand-yt rounded-full animate-spin" />
                    <Sparkles className="w-6 h-6 text-brand-yt absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
                  </div>
                  <div className="text-center space-y-2">
                    <h4 className="text-white font-black uppercase tracking-widest animate-pulse">Running Neural Analysis</h4>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest space-y-1 text-center flex flex-col items-center">
                      <span>• Scanning YouTube transcription patterns</span>
                      <span>• Analyzing Instagram engagement metrics</span>
                      <span>• Synthesizing cross-platform growth hooks</span>
                      <span>• Generating 7-day posting schedule</span>
                    </p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center max-w-md mx-auto">
                  <Activity className="w-12 h-12 text-rose-500/50 mb-4" />
                  <p className="text-rose-400 font-bold text-sm bg-rose-500/10 border border-rose-500/20 p-4 rounded-xl mb-6">
                    {error}
                  </p>
                  <button
                    onClick={generateStrategy}
                    className="flex items-center gap-2 px-6 py-3 bg-brand-yt text-white rounded-xl text-xs font-black uppercase tracking-widest transition-all hover:shadow-[0_0_20px_rgba(255,0,0,0.3)]"
                  >
                    <RefreshCw className="w-4 h-4" /> Try Again
                  </button>
                </div>
              ) : strategy ? (
                <div 
                  className="prose prose-invert prose-slate max-w-none prose-headings:font-black prose-headings:tracking-tight prose-a:text-brand-yt hover:prose-a:text-red-400 prose-pre:bg-slate-900 prose-pre:border prose-pre:border-white/10 prose-strong:text-white prose-strong:font-black text-slate-300"
                  dangerouslySetInnerHTML={getMarkdownHtml(strategy)} 
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-full min-h-[300px]">
                  <p className="text-slate-500 font-bold uppercase tracking-widest">Initialization failed.</p>
                </div>
              )}
            </div>

            
            {/* Footer */}
            {!loading && strategy && (
              <div className="p-4 border-t border-slate-200 dark:border-white/10 bg-white/5 shrink-0 flex justify-between items-center">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">
                  Powered by Gemini 2.5 Pro Neural Engine
                </span>
                <button
                  onClick={generateStrategy}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-800 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all hover:bg-slate-700"
                >
                  <RefreshCw className="w-3 h-3" /> Regenerate Analysis
                </button>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
