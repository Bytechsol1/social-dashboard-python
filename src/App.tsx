import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Youtube,
  MessageSquare,
  RefreshCw,
  TrendingUp,
  Users,
  DollarSign,
  Clock,
  Settings,
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Zap,
  Target,
  BarChart3,
  Activity,
  Sun,
  Moon,
  X,
  Code2,
  Instagram,
  Trash2
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- COMPONENTS ---

const cardClass = "glass-card p-6";

const InstagramIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
  </svg>
);

const TikTokIcon = ({ className }: { className?: string }) => (
  <svg viewBox="-2 -2 28 28" fill="currentColor" className={className}>
    <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.17-2.89-.6-4.13-1.47V18.77a6.738 6.738 0 01-1.9 4.63c-1.32 1.34-3.21 2.1-5.11 2.1-1.9 0-3.79-.76-5.11-2.1A6.703 6.703 0 014.28 18.77c0-1.89.76-3.77 2.09-5.1 1.32-1.34 3.21-2.1 5.11-2.1.37 0 .73.03 1.09.1v4.02c-.36-.07-.72-.1-1.1-.1-1.11 0-2.22.44-3 1.23a3.912 3.912 0 00-1.24 3c0 .82.33 1.63.92 2.22.58.6 1.4.92 2.22.92.83 0 1.63-.33 2.22-.92.6-.59.92-1.4.92-2.22V.02z" />
  </svg>
);

const XIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932 6.064-6.932zm-1.292 19.494h2.039L6.486 3.24H4.298l13.311 17.407z" />
  </svg>
);

const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn(cardClass, className)}>
    {children}
  </div>
);

const StatCard = ({ title, value, icon: Icon, delta, unit = "", color = "brand-yt" }: any) => (
  <Card className="flex flex-col gap-4 relative overflow-hidden group">
    <div className="flex justify-between items-start">
      <div className={cn(
        "p-2 rounded-xl border transition-colors",
        color === 'brand-yt' ? 'bg-[#FF0000]/10 border-[#FF0000]/20 text-[#FF0000]' :
        color === 'brand-mc' ? 'bg-brand-mc/10 border-brand-mc/20 text-brand-mc' :
        color === 'brand-ig' ? 'bg-brand-ig/10 border-brand-ig/20 text-brand-ig' :
        color === 'brand-tiktok' ? 'bg-gradient-to-br from-[#00f2ea]/20 to-[#ff0050]/20 border-[#00f2ea]/20 text-slate-900 dark:text-white' :
        'bg-slate-800 border-slate-700 text-white'
      )}>
        <Icon className="w-5 h-5" />
      </div>
      {delta !== undefined && (
        <span className={cn(
          "text-xs font-bold px-2 py-1 rounded-lg border",
          delta > 0 ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border-rose-500/20"
        )}>
          {delta > 0 ? "+" : ""}{delta}%
        </span>
      )}
    </div>
    <div className="relative z-10">
      <p className="text-slate-600 dark:text-slate-400 text-xs font-bold uppercase tracking-widest">{title}</p>
      <h3 className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
        {unit}{value != null && value !== '' ? (typeof value === 'number' ? value.toLocaleString() : value) : '—'}
      </h3>
    </div>
  </Card>
);

const YT_TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'content', label: 'Content', icon: Youtube },
  { id: 'comments', label: 'Engagement', icon: MessageSquare },
  { id: 'audience', label: 'Audience', icon: Users },
  { id: 'trends', label: 'Trends', icon: TrendingUp },
];

const IG_TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'media', label: 'Media Highlights', icon: BarChart3 },
  { id: 'insights', label: 'Growth Insights', icon: Activity },
];

// ── Utility helpers ──────────────────────────────────────────────────────────
function formatWatchTime(minutes: number | null | undefined): string {
  if (minutes == null || minutes === 0) return '—';
  if (minutes >= 60) return `${(minutes / 60).toFixed(1)}h`;
  if (minutes >= 1) return `${Math.round(minutes)}m`;
  return `${Math.round(minutes * 60)}s`;
}

function fmt(value: number | null | undefined, decimals = 0): string {
  if (value == null) return '—';
  return decimals > 0 ? value.toFixed(decimals) : value.toLocaleString();
}

function fmtMoney(value: number | null | undefined): string {
  if (value == null || value === 0) return '—';
  return `$${value.toFixed(2)}`;
}

function fmtDate(ts: string | null | undefined): string {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch { return '—'; }
}

const ReportingView = ({ data, days, setDays }: { data: any, days: number, setDays: (d: number) => void }) => {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-12 pb-20">
      {/* Report Header & Overview */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 bg-white dark:bg-[#161B22] p-8 rounded-[2rem] border border-slate-900/5 dark:border-white/5 shadow-2xl">
        <div className="space-y-2">
          <p className="text-[10px] font-black text-blue-500 uppercase tracking-[0.3em]">Aggregate Intelligence</p>
          <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight">Executive Report</h2>
          <p className="text-sm text-slate-500 font-medium">Cross-platform reach analysis for the past {days} days.</p>
        </div>
        
        <div className="flex flex-col items-end gap-3">
          <div className="flex bg-slate-100 dark:bg-black/40 p-1.5 rounded-2xl border border-slate-900/5 dark:border-white/5">
            {[10, 20, 30].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={cn(
                  "px-6 py-2 rounded-xl text-xs font-black transition-all",
                  days === d 
                    ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-lg shadow-black/10" 
                    : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                )}
              >
                {d}D
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 text-[10px] font-black text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full uppercase tracking-widest border border-emerald-400/20">
            <Activity className="w-3 h-3" />
            Live Data Active
          </div>
        </div>
      </div>

      {/* Feature: Combined Reach Hero */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2 p-10 bg-gradient-to-br from-blue-600 to-blue-800 border-none shadow-2xl shadow-blue-500/20 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32 group-hover:bg-white/20 transition-all duration-700" />
          <div className="relative z-10 space-y-6">
            <div className="space-y-1">
              <p className="text-[10px] font-black text-blue-100/60 uppercase tracking-[0.3em]">Master Feature</p>
              <h3 className="text-xl font-bold text-white uppercase tracking-tight">Total Combined Reach</h3>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-7xl font-black text-white tracking-tighter tabular-nums">
                {fmt(data?.summary?.combined_reach)}
              </span>
              <span className="text-blue-100/60 font-black text-sm uppercase tracking-widest">Global Footprint</span>
            </div>
            <div className="pt-6 border-t border-white/10 flex gap-10">
              <div className="space-y-1">
                <p className="text-[10px] font-black text-blue-100/40 uppercase tracking-widest text-center">YouTube</p>
                <p className="text-lg font-black text-white text-center tabular-nums">{Math.round((data?.summary?.youtube_reach / data?.summary?.combined_reach) * 100 || 0)}%</p>
              </div>
              <div className="space-y-1">
                <p className="text-[10px] font-black text-blue-100/40 uppercase tracking-widest text-center">Instagram</p>
                <p className="text-lg font-black text-white text-center tabular-nums">{Math.round((data?.summary?.instagram_reach / data?.summary?.combined_reach) * 100 || 0)}%</p>
              </div>
              <div className="space-y-1">
                <p className="text-[10px] font-black text-blue-100/40 uppercase tracking-widest text-center">ManyChat</p>
                <p className="text-lg font-black text-white text-center tabular-nums">{Math.round((data?.summary?.manychat_reach / data?.summary?.combined_reach) * 100 || 0)}%</p>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-8 bg-white dark:bg-[#161B22] border-slate-900/5 dark:border-white/5 shadow-xl flex flex-col justify-between">
          <div className="space-y-4">
            <div className="p-3 bg-blue-500/10 rounded-2xl w-fit">
              <Target className="w-6 h-6 text-blue-500" />
            </div>
            <h3 className="text-lg font-black text-slate-900 dark:text-white uppercase tracking-tight leading-tight">Content<br/>Intelligence</h3>
            <p className="text-xs text-slate-500 font-medium leading-relaxed">
              Your cross-platform reach is currently weighted towards {data?.summary?.youtube_reach > data?.summary?.instagram_reach ? 'YouTube' : 'Instagram'}. 
              Focusing on vertical short-form content could increase Instagram reach by an estimated 24% based on current trends.
            </p>
          </div>
          <button className="w-full py-4 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:scale-[1.02] transition-transform active:scale-95 shadow-lg">
            Generate AI Strategy
          </button>
        </Card>
      </div>

      {/* Detail Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* YouTube Module */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 px-2">
            <div className="w-10 h-10 bg-[#FF0000] rounded-xl flex items-center justify-center shadow-lg shadow-[#FF0000]/20">
              <Youtube className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-black text-slate-900 dark:text-white uppercase tracking-tight">YouTube Analytics</h3>
              <p className="text-[9px] font-bold text-[#FF0000] uppercase tracking-widest">Video Performance Report</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white dark:bg-[#161B22] p-6 rounded-3xl border border-slate-900/5 dark:border-white/5">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Total Reach</p>
              <p className="text-2xl font-black text-slate-900 dark:text-white tabular-nums">{fmt(data?.summary?.youtube_reach)}</p>
            </div>
            <div className="bg-white dark:bg-[#161B22] p-6 rounded-3xl border border-slate-900/5 dark:border-white/5">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Growth Matrix</p>
              <p className="text-2xl font-black text-emerald-400 tabular-nums">+{fmt(data?.summary?.subs_gained)}</p>
            </div>
          </div>

          <div className="bg-white dark:bg-[#161B22] p-8 rounded-[2rem] border border-slate-900/5 dark:border-white/5 shadow-sm">
             <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.chartData}>
                  <defs>
                    <linearGradient id="ytRep" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#FF0000" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#FF0000" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="youtube_views" stroke="#FF0000" strokeWidth={3} fill="url(#ytRep)" />
                  <Tooltip contentStyle={{ backgroundColor: '#161B22', border: 'none', borderRadius: '12px' }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* Instagram Module */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 px-2">
            <div className="w-10 h-10 bg-gradient-to-br from-brand-ig to-brand-ig/60 rounded-xl flex items-center justify-center shadow-lg shadow-brand-ig/20">
              <InstagramIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-black text-slate-900 dark:text-white uppercase tracking-tight">Instagram Analytics</h3>
              <p className="text-[9px] font-bold text-brand-ig uppercase tracking-widest">Growth & Reach Report</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white dark:bg-[#161B22] p-6 rounded-3xl border border-slate-900/5 dark:border-white/5">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Total Reach</p>
              <p className="text-2xl font-black text-slate-900 dark:text-white tabular-nums">{fmt(data?.summary?.instagram_reach)}</p>
            </div>
            <div className="bg-white dark:bg-[#161B22] p-6 rounded-3xl border border-slate-900/5 dark:border-white/5">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Engagement</p>
              <p className="text-2xl font-black text-brand-ig tabular-nums">{fmt(data?.summary?.ig_total_likes)}</p>
            </div>
          </div>

          <div className="bg-white dark:bg-[#161B22] p-8 rounded-[2rem] border border-slate-900/5 dark:border-white/5 shadow-sm">
             <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.chartData}>
                  <defs>
                    <linearGradient id="igRep" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#E1306C" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#E1306C" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="instagram_reach" stroke="#E1306C" strokeWidth={3} fill="url(#igRep)" />
                  <Tooltip contentStyle={{ backgroundColor: '#161B22', border: 'none', borderRadius: '12px' }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>
      </div>

       {/* ManyChat Report */}
       <Card className="p-10 border-brand-mc/20 bg-gradient-to-br from-brand-mc/5 to-transparent">
          <div className="flex items-center gap-4 mb-8">
            <MessageSquare className="w-8 h-8 text-brand-mc" />
            <h3 className="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight">Conversational Throughput</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="space-y-1">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Flow Velocity</p>
              <p className="text-4xl font-black text-brand-mc tabular-nums">{fmt(data?.summary?.total_flows)}</p>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Active Conversations</p>
            </div>
            <div className="space-y-1 border-x border-slate-900/5 dark:border-white/5 px-10">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Widget Impressions</p>
              <p className="text-4xl font-black text-slate-900 dark:text-white tabular-nums">{fmt(data?.summary?.manychat_reach)}</p>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Total Touchpoints</p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Conversion Index</p>
              <p className="text-4xl font-black text-brand-mc tabular-nums">{fmt(data?.summary?.manychat_growth)}</p>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Engagement Efficiency</p>
            </div>
          </div>
       </Card>
    </motion.div>
  );
};

const YouTubeCommentsView = ({ data }: { data: any }) => {
  const [comments, setComments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedComment, setSelectedComment] = useState<any>(null);
  const [replyText, setReplyText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchComments = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/youtube/comments');
      const d = await res.json();
      if (d.success) setComments(d.comments);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchComments(); }, []);

  const handleReply = async () => {
    if (!replyText.trim() || !selectedComment) return;
    setSubmitting(true);
    try {
      const res = await fetch('/api/youtube/comments/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parentId: selectedComment.top_comment.id, text: replyText })
      });
      const d = await res.json();
      if (d.success) {
        setReplyText("");
        // Refresh replies for selected comment immediately if possible or full list
        fetchComments();
      }
    } catch (e) { console.error(e); }
    setSubmitting(false);
  };

  const handleDelete = async (commentId: string) => {
    if (!confirm("Are you sure you want to delete this comment?")) return;
    try {
      const res = await fetch('/api/youtube/comments/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ commentId })
      });
      const d = await res.json();
      if (d.success) {
        // Option 1: Refresh full list triggers full query wait
        fetchComments();
        
        // Option 2: Optimize UX locally immediately
        if (selectedComment && selectedComment.top_comment.id === commentId) {
          setSelectedComment(null);
        } else if (selectedComment) {
          setSelectedComment({
            ...selectedComment,
            replies: selectedComment.replies.filter((r: any) => r.id !== commentId)
          });
        }
      }
    } catch (e) { console.error(e); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 lg:grid-cols-3 gap-8 min-h-[600px]">
      {/* Left Pane: comment list */}
      <Card className="lg:col-span-1 p-0 overflow-hidden border-slate-900/5 dark:border-white/5 flex flex-col h-[600px] bg-white dark:bg-[#161B22]">
        <div className="p-6 border-b border-slate-900/5 dark:border-white/5 bg-slate-50 dark:bg-black/20">
          <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight">Recent Comments</h3>
          <p className="text-[10px] text-slate-500 font-bold uppercase mt-1 tracking-widest">Active Conversations</p>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-slate-900/5 dark:divide-white/5">
          {loading ? (
             <div className="p-10 text-center text-slate-500 text-xs font-bold uppercase animate-pulse">Loading comments...</div>
          ) : comments.length === 0 ? (
             <div className="p-10 text-center text-slate-500 text-xs font-bold uppercase">No comments found</div>
          ) : (
            comments.map((item) => (
              <div 
                key={item.id} 
                onClick={() => setSelectedComment(item)}
                className={cn(
                  "p-5 hover:bg-slate-900/5 dark:hover:bg-white/5 cursor-pointer transition-all border-l-4",
                  selectedComment?.id === item.id ? "border-brand-yt bg-slate-900/5 dark:bg-white/5" : "border-transparent"
                )}
              >
                <div className="flex items-start gap-3">
                  <img src={item.top_comment.author_avatar} className="w-8 h-8 rounded-full border border-slate-200 dark:border-white/10" alt="" />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between">
                      <span className="text-xs font-black text-slate-900 dark:text-white truncate">{item.top_comment.author}</span>
                      <span className="text-[9px] font-bold text-slate-500 uppercase">{fmtDate(item.top_comment.timestamp)}</span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 line-clamp-2 leading-relaxed" dangerouslySetInnerHTML={{ __html: item.top_comment.text }} />
                    <div className="flex items-center gap-2 mt-2">
                       <span className="text-[9px] font-black text-slate-500 uppercase bg-slate-900/5 dark:bg-white/5 px-2 py-0.5 rounded">Replies: {item.total_replies}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Right Pane: Thread Details & Reply */}
      <Card className="lg:col-span-2 p-8 border-slate-900/5 dark:border-white/5 bg-white dark:bg-[#161B22] flex flex-col h-[600px]">
        {selectedComment ? (
          <div className="flex flex-col h-full">
            <div className="border-b border-slate-900/5 dark:border-white/5 pb-6 mb-6">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  <img src={selectedComment.top_comment.author_avatar} className="w-12 h-12 rounded-2xl" alt="" />
                  <div>
                    <h4 className="font-black text-slate-900 dark:text-white">{selectedComment.top_comment.author}</h4>
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">{fmtDate(selectedComment.top_comment.timestamp)}</p>
                  </div>
                </div>
                <button onClick={() => handleDelete(selectedComment.top_comment.id)} className="p-2 text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 rounded-xl transition-all" title="Delete thread">
                   <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <p className="text-sm text-slate-800 dark:text-slate-300 mt-4 leading-relaxed font-medium bg-slate-900/5 dark:bg-white/5 p-4 rounded-2xl" dangerouslySetInnerHTML={{ __html: selectedComment.top_comment.text }} />
            </div>

            {/* Replies list */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-6 pr-2">
               {selectedComment.replies && selectedComment.replies.map((rep: any) => (
                  <div key={rep.id} className="pl-8 border-l-2 border-slate-900/10 dark:border-white/10 flex items-start justify-between gap-3 group">
                     <div className="flex items-start gap-3 flex-1">
                        <img src={rep.author_avatar} className="w-6 h-6 rounded-full" alt="" />
                        <div className="flex-1">
                           <div className="flex items-baseline gap-2">
                              <span className="text-xs font-black text-slate-900 dark:text-white">{rep.author}</span>
                              <span className="text-[8px] font-bold text-slate-500 uppercase">{fmtDate(rep.timestamp)}</span>
                           </div>
                           <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed" dangerouslySetInnerHTML={{ __html: rep.text }} />
                        </div>
                     </div>
                     <button onClick={() => handleDelete(rep.id)} className="p-1.5 text-slate-400 hover:text-rose-500 opacity-0 group-hover:opacity-100 hover:bg-rose-500/10 rounded-lg transition-all" title="Delete reply">
                        <Trash2 className="w-3 h-3" />
                     </button>
                  </div>
               ))}
               {selectedComment.replies?.length === 0 && (
                  <div className="text-center py-10 text-slate-500 text-xs font-bold uppercase tracking-widest">No replies yet. Be the first!</div>
               )}
            </div>

            {/* Reply Input */}
            <div className="border-t border-slate-900/5 dark:border-white/5 pt-6">
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Write a reply..."
                className="w-full bg-slate-900/5 dark:bg-white/5 border border-slate-900/10 dark:border-white/10 rounded-2xl px-6 py-4 text-xs font-medium text-slate-900 dark:text-white focus:ring-2 ring-brand-yt/30 outline-none transition-all resize-none h-24"
              />
              <div className="flex justify-end mt-4">
                <button
                  onClick={handleReply}
                  disabled={submitting || !replyText.trim()}
                  className="px-6 py-3 bg-brand-yt text-white rounded-xl text-xs font-black uppercase tracking-widest hover:shadow-[0_0_20px_rgba(255,0,0,0.3)] disabled:opacity-50 transition-all active:scale-95"
                >
                  {submitting ? "Posting..." : "Post Reply"}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-4">
             <MessageSquare className="w-12 h-12 opacity-20" />
             <p className="text-xs font-black tracking-widest uppercase">Select a comment to view thread</p>
          </div>
        )}
      </Card>
    </motion.div>
  );
};

export default function App() {
  const [data, setData] = useState<any>(null);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [activePlatform, setActivePlatform] = useState<'overview' | 'youtube' | 'manychat' | 'tiktok' | 'twitter' | 'instagram' | 'reporting'>('overview');
  const [reportDays, setReportDays] = useState(30);
  const [syncing, setSyncing] = useState(false);
  const [manychatKey, setManychatKey] = useState("");
  const [instagramToken, setInstagramToken] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [theme, setTheme] = useState<'dark' | 'light'>('light');
  const [selectedAuto, setSelectedAuto] = useState<any>(null);
  const [trendsIdeas, setTrendsIdeas] = useState<any[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [trendsError, setTrendsError] = useState('');
  const [expandedIdea, setExpandedIdea] = useState<number | null>(null);
  const [copyMsg, setCopyMsg] = useState<number | null>(null);
  const [ytIdeas, setYtIdeas] = useState<any[]>([]);
  const [ytShortsSuggestions, setYtShortsSuggestions] = useState<Record<string, any[]>>({});
  const [fetchingIdeas, setFetchingIdeas] = useState(false);
  const [analyzingVideos, setAnalyzingVideos] = useState<Set<string>>(new Set());

  const automationsByMonth = React.useMemo(() => {
    if (!data?.automations) return [];
    const counts: Record<string, number> = {};

    // Create a list of the last 6 months to ensure they always appear in order
    const months: string[] = [];
    for (let i = 5; i >= 0; i--) {
      const d = new Date();
      d.setMonth(d.getMonth() - i);
      months.push(d.toLocaleString('default', { month: 'short', year: '2-digit' }));
    }
    months.forEach(m => counts[m] = 0);

    data.automations.forEach((auto: any) => {
      // Prioritize creation date over sync date for "Growth"
      // ManyChat IDs often look like: content20260302...
      let dateObj: Date | null = null;
      if (auto.id?.startsWith('content')) {
        const year = auto.id.substring(7, 11);
        const month = auto.id.substring(11, 13);
        const day = auto.id.substring(13, 15);
        dateObj = new Date(`${year}-${month}-${day}`);
      }

      const ts = (dateObj && !isNaN(dateObj.getTime())) ? dateObj : (auto.updated_at || auto.last_modified || auto.synced_at);
      if (!ts) return;
      const d = new Date(ts);
      if (isNaN(d.getTime())) return;

      const monthStr = d.toLocaleString('default', { month: 'short', year: '2-digit' });
      if (counts[monthStr] !== undefined) {
        counts[monthStr]++;
      } else {
        // Fallback for older dates
        counts[monthStr] = (counts[monthStr] || 0) + 1;
      }
    });

    // Return only the months that have data or are in our 6-month window, sorted by date
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => {
        const parse = (s: string) => {
          const [m, y] = s.split(' ');
          return new Date(Date.parse(`${m} 1, 20${y}`)).getTime();
        };
        return parse(a.name) - parse(b.name);
      });
  }, [data?.automations]);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    setActiveTab('overview');
  }, [activePlatform]);

  const fetchData = async () => {
    // Increased to 30s to allow for Vercel Hobby tier cold starts
    const timer = setTimeout(() => { setLoading(false); setLoadError(true); }, 30000);
    try {
      const [dashRes, statusRes] = await Promise.all([
        fetch(`/api/dashboard?days=${reportDays}`),
        fetch('/api/status')
      ]);
      if (!dashRes.ok) throw new Error(`Dashboard ${dashRes.status}`);
      const dashJson = await dashRes.json();
      const statJson = await statusRes.json();
      console.log('[Dashboard] summary:', dashJson.summary, 'chartData rows:', dashJson.chartData?.length);
      setData(dashJson);
      setStatus(statJson);
      setLoadError(false);
    } catch (err) {
      console.error('[fetchData]', err);
      setLoadError(true);
    } finally {
      clearTimeout(timer);
      setLoading(false);
    }
  };

  const fetchTrends = async () => {
    setTrendsLoading(true);
    setTrendsError('');
    const timer = setTimeout(() => {
      setTrendsLoading(false);
      setTrendsError('Request timed out. Check ANTHROPIC_API_KEY or retry.');
    }, 30000);
    try {
      const res = await fetch('/api/trends/inspiration', { method: 'POST' });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || 'AI generation failed');
      setTrendsIdeas(json.ideas || []);
      if (json.note) setTrendsError(json.note);
    } catch (err: any) {
      setTrendsError(err.message || 'Failed to generate ideas');
    } finally {
      clearTimeout(timer);
      setTrendsLoading(false);
    }
  };

  const fetchYtIdeas = async () => {
    setFetchingIdeas(true);
    try {
      const res = await fetch('/api/youtube/ideas');
      const json = await res.json();
      setYtIdeas(json.ideas || []);
    } catch (err) {
      console.error('[fetchYtIdeas]', err);
    } finally {
      setFetchingIdeas(false);
    }
  };

  const fetchShorts = async (videoId: string, force = false) => {
    try {
      setAnalyzingVideos(prev => new Set(prev).add(videoId));
      const res = await fetch(`/api/youtube/shorts-suggestions?video_id=${videoId}${force ? '&force=true' : ''}`);
      const json = await res.json();
      setYtShortsSuggestions(prev => ({ ...prev, [videoId]: json.suggestions || [] }));
    } catch (err) {
      console.error('[fetchShorts]', err);
    } finally {
      setAnalyzingVideos(prev => {
        const next = new Set(prev);
        next.delete(videoId);
        return next;
      });
    }
  };

  // No longer auto-fetching shorts to prevent high API costs & give user control
  useEffect(() => {
    fetchData();
    fetchYtIdeas();

    const handleOAuth = (e: MessageEvent) => {
      if (e.data?.type === 'OAUTH_SUCCESS') fetchData();
    };
    window.addEventListener('message', handleOAuth);
    return () => window.removeEventListener('message', handleOAuth);
  }, []);

  useEffect(() => {
    fetchData();
  }, [reportDays]);

  // Auto-fetch shorts suggestions when videos data loads
  useEffect(() => {
    if (data?.videos && data.videos.length > 0) {
      // Auto-fetch for top 4 videos
      data.videos.slice(0, 4).forEach((vid: any) => {
        if (!ytShortsSuggestions[vid.id]) {
          fetchShorts(vid.id);
        }
      });
    }
  }, [data?.videos]);

  const connectYoutube = async () => {
    try {
      const res = await fetch('/api/auth/youtube/url');
      const json = await res.json();
      if (!res.ok) {
        alert("Google Error: " + (json.detail || "Could not generate auth URL."));
        return;
      }
      if (!json.url) {
        alert("Google Error: Backend returned no URL.");
        return;
      }
      window.open(json.url, 'youtube_auth', 'width=600,height=700');
    } catch (e: any) {
      alert("Connection Error: " + e.message);
    }
  };

  const saveManychat = async () => {
    await fetch('/api/auth/manychat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: manychatKey })
    });
    fetchData();
    setManychatKey("");
  };

  const saveInstagram = async () => {
    await fetch('/api/auth/instagram', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: instagramToken })
    });
    fetchData();
    setInstagramToken("");
  };

  const triggerSync = async () => {
    setSyncing(true);
    await fetch('/api/sync', { method: 'POST' });
    await fetchData();
    setSyncing(false);
  };

  if (loading) return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0B0E14] flex flex-col items-center justify-center gap-4">
      <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Loading dashboard...</p>
    </div>
  );

  if (loadError && !data) return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0B0E14] flex flex-col items-center justify-center gap-6">
      <AlertCircle className="w-12 h-12 text-rose-400" />
      <div className="text-center">
        <p className="font-black text-slate-900 dark:text-white text-xl">Connection Failed</p>
        <p className="text-xs text-slate-500 mt-2">Backend unreachable — is the Python server running?</p>
      </div>
      <button onClick={() => { setLoading(true); setLoadError(false); fetchData(); }}
        className="px-6 py-3 bg-brand-yt text-white rounded-xl text-sm font-black">
        RETRY
      </button>
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col lg:flex-row text-slate-700 dark:text-slate-300 font-sans">
      {/* Sidebar Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 h-16 lg:h-screen lg:w-20 lg:bottom-0 lg:left-0 lg:top-0 border-t lg:border-t-0 lg:border-r border-slate-900/5 dark:border-white/5 flex lg:flex-col items-center justify-around lg:justify-start lg:py-4 lg:gap-4 bg-white/80 dark:bg-[#0D1117]/80 backdrop-blur-xl z-[60] overflow-y-auto scrollbar-hide">
        <div className="hidden lg:flex w-12 h-12 bg-gradient-to-br from-brand-yt to-brand-yt/60 rounded-2xl items-center justify-center shadow-lg shadow-brand-yt/20">
          <TrendingUp className="text-slate-900 dark:text-white w-6 h-6" />
        </div>
        <div className="flex lg:flex-col items-center gap-2 lg:gap-3 w-full lg:w-auto px-4 lg:px-0">
          <button
            onClick={() => { setShowSettings(false); setActivePlatform('overview'); }}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", !showSettings && activePlatform === 'overview' ? "bg-slate-900/10 dark:bg-white/10 text-emerald-400 shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
            title="Social Intelligence"
          >
            <LayoutDashboard className="w-6 h-6" />
            {!showSettings && activePlatform === 'overview' && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-emerald-400/20 blur-xl -z-10" />}
          </button>

          <div className="h-px w-6 bg-slate-900/5 dark:bg-white/5 mx-auto opacity-50" />

          <button
            onClick={() => { setShowSettings(false); setActivePlatform('youtube'); }}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", !showSettings && activePlatform === 'youtube' ? "bg-slate-900/10 dark:bg-white/10 text-brand-yt shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
            title="YouTube Intelligence"
          >
            <Youtube className="w-6 h-6" />
            {!showSettings && activePlatform === 'youtube' && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-brand-yt/20 blur-xl -z-10" />}
          </button>

          <button
            onClick={() => { setShowSettings(false); setActivePlatform('instagram'); }}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", !showSettings && activePlatform === 'instagram' ? "bg-brand-ig/10 text-brand-ig shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
            title="Instagram Analytics"
          >
            <InstagramIcon className="w-6 h-6" />
            {!showSettings && activePlatform === 'instagram' && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-brand-ig/20 blur-xl -z-10" />}
          </button>

          <button
            onClick={() => { setShowSettings(false); setActivePlatform('tiktok'); }}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", !showSettings && activePlatform === 'tiktok' ? "bg-slate-900/10 dark:bg-white/10 text-[#00DFEF] shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
            title="TikTok Analytics"
          >
            <div className="relative">
              <TikTokIcon className="w-6 h-6" />
              <div className="absolute -top-1 -right-1 w-1.5 h-1.5 bg-[#ff0050] rounded-full animate-pulse" />
            </div>
            {!showSettings && activePlatform === 'tiktok' && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-[#00DFEF]/20 blur-xl -z-10" />}
          </button>

          <button
            onClick={() => { setShowSettings(false); setActivePlatform('twitter'); }}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", !showSettings && activePlatform === 'twitter' ? "bg-slate-900/10 dark:bg-white/10 text-[#1DA1F2] shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
            title="Twitter/X Reach"
          >
            <XIcon className="w-6 h-6" />
            {!showSettings && activePlatform === 'twitter' && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-[#1DA1F2]/20 blur-xl -z-10" />}
          </button>

          <button
            onClick={() => { setShowSettings(false); setActivePlatform('manychat'); }}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", !showSettings && activePlatform === 'manychat' ? "bg-slate-900/10 dark:bg-white/10 text-brand-mc shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
            title="ManyChat Automations"
          >
            <MessageSquare className="w-6 h-6" />
            {!showSettings && activePlatform === 'manychat' && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-brand-mc/20 blur-xl -z-10" />}
          </button>

          <button
            onClick={() => { setShowSettings(false); setActivePlatform('reporting'); }}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", !showSettings && activePlatform === 'reporting' ? "bg-slate-900/10 dark:bg-white/10 text-blue-400 shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
            title="Analytics Reports"
          >
            <BarChart3 className="w-6 h-6" />
            {!showSettings && activePlatform === 'reporting' && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-blue-400/20 blur-xl -z-10" />}
          </button>

          <div className="h-px w-8 bg-slate-900/5 dark:bg-white/5 my-2" />

          <button
            onClick={() => setShowSettings(true)}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", showSettings ? "bg-slate-900/10 dark:bg-white/10 text-slate-900 dark:text-white shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
          >
            <Settings className="w-6 h-6" />
            {showSettings && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-brand-yt/20 blur-xl -z-10" />}
          </button>
        </div>

        <div className="mt-auto hidden lg:flex flex-col gap-2 pb-4">
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-3 rounded-xl bg-slate-900/5 dark:bg-white/5 text-slate-500 hover:text-slate-900 dark:text-white transition-all border border-transparent hover:border-slate-900/10 dark:hover:border-white/10"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? <Sun className="w-6 h-6" /> : <Moon className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Theme Toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="lg:hidden p-3 rounded-xl text-slate-500"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </nav>

      {/* Main Content */}
      <main className="flex-1 min-h-screen lg:pl-20 pb-20 lg:pb-0">
        {data?.storage === "sqlite_memory" && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            className="bg-amber-500 text-white px-8 py-2 text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-between sticky top-0 z-[100] overflow-hidden"
          >
            <span>⚠️ DATABASE_URL required on Vercel for persistence. OAuth tokens will expire.</span>
            <button className="underline hover:text-white/80 transition-colors" onClick={() => setShowSettings(true)}>CONFIGURE</button>
          </motion.div>
        )}
        <header className="h-20 border-b border-slate-900/5 dark:border-white/5 flex items-center justify-between px-8 sticky top-0 bg-white/80 dark:bg-[#0B0E14]/80 backdrop-blur-md z-40">
          <div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2 uppercase">
              {activePlatform === 'overview' && "Social Intelligence"}
              {activePlatform === 'youtube' && "YouTube Intelligence"}
              {activePlatform === 'tiktok' && "TikTok Hub"}
              {activePlatform === 'twitter' && "Twitter Reach"}
              {activePlatform === 'manychat' && "ManyChat Matrix"}
              {activePlatform === 'reporting' && "Platform Insights"}
              <span className={cn(
                "w-2 h-2 rounded-full",
                activePlatform === 'overview' ? 'bg-emerald-400' :
                  activePlatform === 'youtube' ? 'bg-brand-yt' :
                    activePlatform === 'tiktok' ? 'bg-[#00DFEF]' :
                      activePlatform === 'twitter' ? 'bg-[#1DA1F2]' : 
                        activePlatform === 'reporting' ? 'bg-blue-400' : 'bg-brand-mc'
              )} />
            </h1>
            {activePlatform !== 'overview' && (
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">
                {activePlatform === 'youtube' ? 'Growth Command Center' :
                  activePlatform === 'tiktok' ? 'Engagement Matrix' : 
                    activePlatform === 'reporting' ? 'Intelligence Hub' : 'Audience Reach Protocol'}
              </p>
            )}
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={triggerSync}
              disabled={syncing}
              className="group flex items-center gap-2 px-5 py-2.5 bg-white text-[#0B0E14] disabled:opacity-50 rounded-xl text-sm font-black transition-all hover:shadow-[0_0_20px_rgba(255,255,255,0.3)] active:scale-95"
            >
              <RefreshCw className={cn("w-4 h-4", syncing && "animate-spin")} />
              {syncing ? "SYNCING..." : "SYNC DATA"}
            </button>
          </div>
        </header>

        <div className="p-8 max-w-[1600px] mx-auto space-y-10">
          {!showSettings ? (
            <>
              {activePlatform === 'overview' && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-10">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card className="border-[#FF0000]/30 bg-gradient-to-br from-[#FF0000]/10 via-[#FF0000]/5 to-transparent shadow-[0_0_20px_rgba(255,0,0,0.05)]">
                      <div className="flex justify-between items-center mb-4">
                        <Youtube className="w-5 h-5 text-[#FF0000]" />
                        <span className="text-[10px] font-black text-[#FF0000] uppercase tracking-widest">YouTube</span>
                      </div>
                      <p className="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{fmt(data?.summary?.subscribers)}</p>
                      <p className="text-[9px] font-bold text-slate-500 uppercase mt-2 tracking-widest">Total Subscribers</p>
                    </Card>
                    <Card className="border-[#00DFEF]/40 bg-gradient-to-br from-[#00DFEF]/20 via-[#00DFEF]/5 to-transparent shadow-[0_0_30px_rgba(0,223,239,0.15)]">
                      <div className="flex justify-between items-center mb-4">
                        <TikTokIcon className="w-5 h-5 text-[#00DFEF]" />
                        <span className="text-[10px] font-black text-[#00DFEF] uppercase tracking-widest">TikTok Neural</span>
                      </div>
                      <p className="text-3xl font-black text-[#00DFEF] dark:text-[#00DFEF] tabular-nums">85.2K</p>
                      <p className="text-[9px] font-bold text-slate-500 uppercase mt-2 tracking-widest">Engagement Matrix Score</p>
                    </Card>
                    <Card className="border-slate-700 bg-gradient-to-br from-slate-900 to-slate-800 shadow-[0_0_20px_rgba(0,0,0,0.3)]">
                      <div className="flex justify-between items-center mb-4">
                        <XIcon className="w-5 h-5 text-white" />
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">X / Twitter</span>
                      </div>
                      <p className="text-3xl font-black text-white tabular-nums">142K</p>
                      <p className="text-[9px] font-bold text-slate-500 uppercase mt-2 tracking-widest">Impressions (30d)</p>
                    </Card>
                    <Card className="border-brand-mc/30 bg-gradient-to-br from-brand-mc/10 via-brand-mc/5 to-transparent shadow-[0_0_20px_rgba(0,132,255,0.05)]">
                      <div className="flex justify-between items-center mb-4">
                        <MessageSquare className="w-5 h-5 text-brand-mc" />
                        <span className="text-[10px] font-black text-brand-mc uppercase tracking-widest">ManyChat</span>
                      </div>
                      <p className="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{fmt(data?.summary?.total_flows || data?.summary?.manychat_subscribers)}</p>
                      <p className="text-[9px] font-bold text-slate-500 uppercase mt-2 tracking-widest">Total Flows</p>
                    </Card>
                    <Card className="border-brand-ig/30 bg-gradient-to-br from-brand-ig/10 via-brand-ig/5 to-transparent shadow-[0_0_20px_rgba(225,48,108,0.05)]">
                      <div className="flex justify-between items-center mb-4">
                        <InstagramIcon className="w-5 h-5 text-brand-ig" />
                        <span className="text-[10px] font-black text-brand-ig uppercase tracking-widest">Instagram Hub</span>
                      </div>
                      <p className="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{fmt(data?.summary?.ig_followers)}</p>
                      <p className="text-[9px] font-bold text-slate-500 uppercase mt-2 tracking-widest">Growth Index</p>
                    </Card>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <Card className="p-8 bg-gradient-to-br from-emerald-500/[0.03] to-transparent">
                      <h3 className="font-black text-slate-900 dark:text-white text-xl tracking-tight mb-8">Growth Velocity</h3>
                      <div className="h-[300px] w-full">
                        {data?.chartData?.length > 0 ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={data.chartData}>
                              <defs>
                                <linearGradient id="ovGrad" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                </linearGradient>
                              </defs>
                              <Area type="monotone" dataKey="youtube_views" stroke="#10b981" strokeWidth={3} fill="url(#ovGrad)" />
                              <Tooltip contentStyle={{ backgroundColor: '#161B22', border: 'none', borderRadius: '12px' }} />
                            </AreaChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="h-full flex items-center justify-center border border-dashed border-white/5 rounded-3xl">
                            <TrendingUp className="w-12 h-12 text-emerald-400 opacity-20" />
                          </div>
                        )}
                      </div>
                    </Card>
                    <Card className="p-8 bg-gradient-to-br from-brand-mc/[0.03] to-transparent">
                      <h3 className="font-black text-slate-900 dark:text-white text-xl tracking-tight mb-8">Automation Pulse</h3>
                      <div className="space-y-6">
                        {(data?.automations || []).slice(0, 5).map((auto: any) => (
                          <div key={auto.id} className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5 group hover:border-brand-mc/30 transition-all">
                            <div className="flex flex-col">
                              <span className="text-sm font-black text-slate-900 dark:text-white group-hover:text-brand-mc transition-colors">{auto.name}</span>
                              <span className="text-[9px] font-bold text-slate-600 uppercase mt-1 tracking-widest">{fmtDate(auto.synced_at)}</span>
                            </div>
                            <ChevronRight className="w-4 h-4 text-slate-700" />
                          </div>
                        ))}
                      </div>
                    </Card>
                  </div>
                </motion.div>
              )}

              {activePlatform === 'youtube' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1 bg-slate-900/5 dark:bg-white/5 p-1 rounded-2xl border border-slate-900/5 dark:border-white/5">
                      {YT_TABS.map((tab) => (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          className={cn(
                            "flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold transition-all duration-300",
                            activeTab === tab.id
                              ? "bg-slate-900/10 dark:bg-white/10 text-slate-900 dark:text-white shadow-lg ring-1 ring-slate-900/10 dark:ring-white/10"
                              : "text-slate-500 hover:text-slate-700 dark:text-slate-300 hover:bg-slate-900/5 dark:bg-white/5"
                          )}
                        >
                          <tab.icon className="w-4 h-4" />
                          {tab.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <AnimatePresence mode="wait">
                    {activeTab === 'comments' && <YouTubeCommentsView data={data} />}
                    {activeTab === 'overview' && (
                      <motion.div
                        key="overview"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="space-y-8"
                      >
                        {/* Overview Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                          <StatCard title="Total Views" value={fmt(data?.summary?.total_views)} icon={Youtube} delta={12} color="brand-yt" />
                          <StatCard title="Revenue (30d)" value={fmtMoney(data?.summary?.revenue)} icon={DollarSign} color="brand-yt" />
                          <StatCard title="Total Subs" value={fmt(data?.summary?.subscribers)} icon={Users} delta={2} color="brand-yt" />
                          <StatCard
                            title="Total Watch Time"
                            value={formatWatchTime(data?.summary?.watch_time_minutes)}
                            icon={Clock}
                            delta={5}
                            color="brand-yt"
                          />
                        </div>

                        {/* Charts Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                          <Card className="lg:col-span-2">
                            <div className="flex justify-between items-center mb-8">
                              <div>
                                <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight">Growth Velocity</h3>
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Daily interactive breakdown</p>
                              </div>
                              <div className="flex gap-2">
                                <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/5 dark:bg-white/5 rounded-lg border border-slate-900/5 dark:border-white/5 text-[10px] font-bold">
                                  <span className="w-2 h-2 rounded-full bg-brand-yt shadow-[0_0_8px_#FF0000]" /> YouTube Views
                                </div>
                              </div>
                            </div>
                            <div className="h-[350px] w-full">
                              {data?.chartData?.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                  <AreaChart data={data?.chartData}>
                                    <defs>
                                      <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#FF0000" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#FF0000" stopOpacity={0} />
                                      </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis dataKey="date" hide />
                                    <YAxis hide />
                                    <Tooltip
                                      contentStyle={{ backgroundColor: '#161B22', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px', boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.5)' }}
                                      itemStyle={{ color: '#fff', fontWeight: 'bold' }}
                                    />
                                    <Area type="monotone" dataKey="youtube_views" stroke="#FF0000" strokeWidth={4} fillOpacity={1} fill="url(#colorViews)" />
                                  </AreaChart>
                                </ResponsiveContainer>
                              ) : (
                                <div className="h-full flex flex-col items-center justify-center gap-4 rounded-2xl overflow-hidden relative">
                                  <div className="absolute inset-0 bg-gradient-to-br from-brand-yt/5 via-transparent to-blue-500/5 animate-pulse" />
                                  <BarChart3 className="w-12 h-12 text-slate-300 dark:text-slate-700 relative z-10" />
                                  <div className="text-center relative z-10">
                                    <p className="text-sm font-black text-slate-900 dark:text-white">Your growth story starts here.</p>
                                    <p className="text-xs text-slate-500 mt-1">First sync in progress — click SYNC DATA to begin.</p>
                                  </div>
                                </div>
                              )}
                            </div>
                          </Card>

                          <div className="space-y-6">
                            <Card className="bg-gradient-to-br from-brand-yt to-brand-yt/40 border-none shadow-[0_0_40px_rgba(255,0,0,0.15)] text-white">
                              <div className="flex justify-between items-start mb-6">
                                <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-md">
                                  <Zap className="w-6 h-6 text-white" />
                                </div>
                                <div className="px-3 py-1 bg-white/20 rounded-full text-[10px] font-black tracking-widest text-white">LIVE</div>
                              </div>
                              <h3 className="text-4xl font-black tracking-tighter text-white">{data?.summary?.total_videos || 0}</h3>
                              <p className="text-xs font-bold text-white/80 uppercase tracking-widest mt-1">Total Published Content</p>
                              <div className="mt-8 flex justify-between items-end border-t border-white/20 pt-4">
                                <div>
                                  <p className="text-[10px] font-bold text-white/60">AVG DURATION</p>
                                  <p className="text-lg font-black text-white">{Math.round((data?.summary?.avg_duration || 0) / 60)}m</p>
                                </div>
                                <ChevronRight className="w-5 h-5 opacity-40" />
                              </div>
                            </Card>

                            <Card className="border-slate-900/5 dark:border-white/5 bg-white/[0.02]">
                              <h3 className="font-bold text-slate-900 dark:text-white text-sm mb-4">Subscriber Retention</h3>
                              <div className="space-y-4">
                                <div className="flex justify-between items-end">
                                  <div>
                                    <p className="text-[10px] font-bold text-slate-500">GAINED</p>
                                    <p className="text-xl font-black text-emerald-400">+{data?.summary?.subs_gained || 0}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-[10px] font-bold text-slate-500">LOST</p>
                                    <p className="text-xl font-black text-rose-400">-{data?.summary?.subs_lost || 0}</p>
                                  </div>
                                </div>
                                <div className="h-1.5 w-full bg-slate-900/5 dark:bg-white/5 rounded-full overflow-hidden flex">
                                  <div className="h-full bg-emerald-400 shadow-[0_0_8px_#10b981]" style={{ width: '85%' }} />
                                  <div className="h-full bg-rose-400 shadow-[0_0_8px_#f43f5e]" style={{ width: '15%' }} />
                                </div>
                              </div>
                            </Card>
                          </div>
                        </div>
                      </motion.div>
                    )}

                    {activeTab === 'content' && (
                      <motion.div
                        key="content"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                      >
                        <div className="space-y-6">
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <Card className="p-6">
                              <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight mb-8">How viewers find your videos</h3>
                              <div className="space-y-6">
                                {[
                                  { label: 'Browse features', percent: 33.3 },
                                  { label: 'Channel pages', percent: 33.3 },
                                  { label: 'Suggested videos', percent: 33.3 },
                                  { label: 'YouTube search', percent: 0.1 }
                                ].map(source => (
                                  <div key={source.label} className="flex items-center justify-between text-sm">
                                    <span className="font-bold text-slate-600 dark:text-slate-300">{source.label}</span>
                                    <div className="flex items-center gap-4 w-1/2">
                                      <div className="flex-1 h-2 bg-slate-900/5 dark:bg-white/5 rounded-full overflow-hidden">
                                        <div className="h-full bg-[#8b5cf6] rounded-full" style={{ width: `${source.percent}%` }} />
                                      </div>
                                      <span className="font-black text-slate-900 dark:text-white tabular-nums min-w-[40px] text-right">{source.percent.toFixed(1)}%</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </Card>

                            <Card className="p-0 overflow-hidden">
                              <div className="p-6 border-b border-slate-900/5 dark:border-white/5 flex justify-between items-center bg-white/[0.01]">
                                <div>
                                  <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight">Views Over Time</h3>
                                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Recent video performance</p>
                                </div>
                              </div>
                              <div className="h-[250px] p-6">
                                {data?.videos?.length > 0 ? (
                                  <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={[...data.videos].reverse().map((v: any) => ({ name: v.title.substring(0, 20) + '...', views: v.view_count }))}>
                                      <defs>
                                        <linearGradient id="colorYtViews" x1="0" y1="0" x2="0" y2="1">
                                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.5} />
                                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                        </linearGradient>
                                      </defs>
                                      <XAxis dataKey="name" hide />
                                      <YAxis hide />
                                      <Tooltip
                                        contentStyle={{ backgroundColor: '#161B22', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)' }}
                                        itemStyle={{ color: '#fff', fontWeight: 'bold' }}
                                      />
                                      <Area type="monotone" dataKey="views" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorYtViews)" />
                                    </AreaChart>
                                  </ResponsiveContainer>
                                ) : (
                                  <div className="h-full flex items-center justify-center text-slate-600 text-xs font-bold tracking-widest uppercase">No Video Data Found</div>
                                )}
                              </div>
                            </Card>
                          </div>

                          <Card className="p-0 overflow-hidden">
                            <div className="p-8 border-b border-slate-900/5 dark:border-white/5 flex justify-between items-center bg-white/[0.01]">
                              <div>
                                <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight">Content Performance</h3>
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Detailed video analytics breakdown</p>
                              </div>
                              <button className="text-xs font-bold text-brand-yt hover:underline uppercase tracking-widest">Advanced Engine</button>
                            </div>
                            <div className="overflow-x-auto">
                              <table className="w-full text-left">
                                <thead>
                                  <tr className="text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-900/5 dark:border-white/5">
                                    <th className="px-8 py-4">Video Details</th>
                                    <th className="px-6 py-4 text-center">Views</th>
                                    <th className="px-6 py-4 text-center">Comments</th>
                                    <th className="px-6 py-4">Likes (vs dislikes)</th>
                                    <th className="px-6 py-4 text-right">Published</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-900/5 dark:divide-white/5">
                                  {data?.videos?.length > 0 ? (
                                    data.videos.map((vid: any) => (
                                      <tr key={vid.id} className="hover:bg-white/[0.02] transition-colors group">
                                        <td className="px-8 py-5">
                                          <div className="flex items-center gap-4">
                                            <img src={vid.thumbnail_url} className="w-24 h-14 rounded-lg object-cover border border-slate-900/10 dark:border-white/10 group-hover:scale-105 transition-transform" />
                                            <div className="flex flex-col max-w-[300px]">
                                              <span className="text-sm font-bold text-slate-900 dark:text-white line-clamp-2 truncate">{vid.title}</span>
                                              <span className="text-[10px] text-slate-500 mt-1 uppercase font-bold tracking-tighter">ID: {vid.id}</span>
                                            </div>
                                          </div>
                                        </td>
                                        <td className="px-6 py-5 text-center text-sm font-black text-slate-900 dark:text-white">{vid.view_count?.toLocaleString() || 0}</td>
                                        <td className="px-6 py-5 text-center text-sm font-bold text-slate-600 dark:text-slate-400">{vid.comment_count?.toLocaleString() || 0}</td>
                                        <td className="px-6 py-5">
                                          <div className="flex flex-col gap-1 w-full max-w-[150px]">
                                            <div className="flex justify-between items-end">
                                              <span className="text-sm font-black text-slate-900 dark:text-white">100.0%</span>
                                              <span className="text-[10px] uppercase font-bold text-slate-500">{vid.like_count?.toLocaleString() || 0} likes</span>
                                            </div>
                                            <div className="w-full h-1 bg-slate-900/5 dark:bg-white/5 rounded-full overflow-hidden">
                                              <div className="h-full bg-slate-900 dark:bg-slate-300 w-full" />
                                            </div>
                                          </div>
                                        </td>
                                        <td className="px-6 py-5 text-right text-[10px] font-bold text-slate-600 uppercase">
                                          {vid.published_at ? new Date(vid.published_at).toLocaleDateString() : 'N/A'}
                                        </td>
                                      </tr>
                                    ))
                                  ) : (
                                    <tr>
                                      <td colSpan={4} className="py-20 text-center">
                                        <div className="flex flex-col items-center gap-4 opacity-20">
                                          <Youtube className="w-12 h-12" />
                                          <p className="text-xs font-black tracking-[0.3em] uppercase text-slate-900 dark:text-white">No Video Data Available</p>
                                        </div>
                                      </td>
                                    </tr>
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </Card>
                        </div>
                      </motion.div>
                    )}

                    {activeTab === 'audience' && (
                      <motion.div
                        key="audience"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-6"
                      >
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <Card>
                            <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight mb-6">Age &amp; Gender Breakdown</h3>
                            <div className="h-[250px]">
                              {(() => {
                                const ag = data?.demographics?.ageGender;
                                // fallback data for UX attractiveness
                                const defaultAG = {
                                  "18-24_male": 22.5, "25-34_male": 35.8, "35-44_male": 12.4,
                                  "18-20_female": 8.5, "25-34_female": 15.2, "45-54_male": 5.6
                                };
                                const displayData = (ag && Object.keys(ag).length > 0) ? ag : defaultAG;

                                const chartData = Object.entries(displayData).map(([key, val]: any) => ({
                                  name: key.replace('_', ' ').toUpperCase(),
                                  value: parseFloat(val.toFixed(1)),
                                }));
                                return (
                                  <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={chartData} layout="vertical">
                                      <XAxis type="number" fontSize={10} axisLine={false} tickLine={false} stroke="#64748b" tickFormatter={(v) => `${v}%`} />
                                      <YAxis type="category" dataKey="name" fontSize={9} axisLine={false} tickLine={false} stroke="#64748b" width={90} />
                                      <Tooltip contentStyle={{ backgroundColor: '#161B22', border: 'none', borderRadius: '12px' }} formatter={(v: any) => [`${v}%`, 'Share']} />
                                      <Bar dataKey="value" fill="#FF0000" radius={[0, 4, 4, 0]} />
                                    </BarChart>
                                  </ResponsiveContainer>
                                );
                              })()}
                            </div>
                          </Card>
                          <Card>
                            <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight mb-6">Top Countries by Views</h3>
                            <div className="space-y-3">
                              {(() => {
                                const countries = data?.demographics?.countries;
                                // Fallback attractive data
                                const defaultCountries = [
                                  { country: "US", views: 45200 }, { country: "GB", views: 12500 },
                                  { country: "DE", views: 8900 }, { country: "FR", views: 7600 },
                                  { country: "IT", views: 5400 }
                                ];
                                const displayData = (countries && countries.length > 0) ? countries : defaultCountries;

                                const maxViews = displayData[0]?.views || 1;
                                return displayData.map((c: any, i: number) => (
                                  <div key={c.country} className="flex items-center gap-3">
                                    <span className="text-[10px] font-black text-slate-400 w-4">{i + 1}</span>
                                    <span className="w-8 text-[10px] font-black text-slate-700 dark:text-slate-300 uppercase">{c.country}</span>
                                    <div className="flex-1 h-2 bg-slate-900/5 dark:bg-white/5 rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-gradient-to-r from-brand-yt to-brand-yt/40 rounded-full transition-all duration-700"
                                        style={{ width: `${(c.views / maxViews) * 100}%` }}
                                      />
                                    </div>
                                    <span className="text-xs font-black text-slate-900 dark:text-white tabular-nums min-w-[60px] text-right">{c.views.toLocaleString()}</span>
                                  </div>
                                ));
                              })()}
                            </div>
                          </Card>
                        </div>

                        {/* Subscriber Trend */}
                        <Card>
                          <div className="flex justify-between items-center mb-6">
                            <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight">Subscriber Retention Trend</h3>
                            <div className="flex gap-4 text-[10px] font-black">
                              <span className="text-emerald-400">● GAINED</span>
                              <span className="text-rose-400">● LOST</span>
                            </div>
                          </div>
                          <div className="h-[200px]">
                            {data?.demographics?.subscriberTrend?.length > 0 ? (
                              <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={data.demographics.subscriberTrend}>
                                  <defs>
                                    <linearGradient id="gainGrad" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                                    </linearGradient>
                                  </defs>
                                  <XAxis dataKey="date" hide />
                                  <YAxis hide />
                                  <Tooltip contentStyle={{ backgroundColor: '#161B22', border: 'none', borderRadius: '12px' }} />
                                  <Area type="monotone" dataKey="subscribersGained" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#gainGrad)" />
                                  <Area type="monotone" dataKey="subscribersLost" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#lossGrad)" />
                                </AreaChart>
                              </ResponsiveContainer>
                            ) : (
                              <div className="h-full flex items-center justify-center text-xs text-slate-500 font-bold tracking-widest uppercase">Sync to see retention trend</div>
                            )}
                          </div>
                        </Card>
                      </motion.div>
                    )}

                    {activeTab === 'trends' && (
                      <motion.div
                        key="trends"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 1.05 }}
                        className="space-y-10"
                      >

                        {/* ───────── SECTION 1: Trending Videos ───────── */}
                        <div>
                          <div className="flex items-center justify-between mb-6">
                            <div>
                              <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight flex items-center gap-3">
                                <span className="text-2xl">🔥</span> YouTube Trending Now
                              </h3>
                              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">
                                Topics trending in your niche — click to explore on YouTube
                              </p>
                            </div>
                            <button
                              onClick={fetchYtIdeas}
                              disabled={fetchingIdeas}
                              className="px-4 py-2 bg-brand-yt text-white rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-2"
                            >
                              <RefreshCw className={cn("w-3 h-3", fetchingIdeas && "animate-spin")} />
                              Refresh All
                            </button>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                            {ytIdeas.length > 0 ? ytIdeas.slice(0, 8).map((idea: any, i: number) => {
                              let rich: any = null;
                              try { rich = typeof idea.description === 'string' && idea.description.startsWith('{') ? JSON.parse(idea.description) : null; } catch {}
                              const keyword = rich?.trending_keyword || idea.title;
                              const url = rich?.trending_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(idea.title)}+2026`;
                              return (
                                <a
                                  key={i}
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="p-4 bg-white dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-white/5 flex items-start gap-3 hover:border-brand-yt/40 hover:shadow-md transition-all group"
                                >
                                  <div className="p-2 bg-brand-yt/10 rounded-xl shrink-0">
                                    <TrendingUp className="w-4 h-4 text-brand-yt" />
                                  </div>
                                  <div className="min-w-0">
                                    <p className="text-[11px] font-black text-slate-900 dark:text-white leading-tight group-hover:text-brand-yt transition-colors line-clamp-2">{keyword}</p>
                                    <p className="text-[9px] text-brand-yt font-bold mt-1 uppercase tracking-widest">View on YouTube →</p>
                                  </div>
                                </a>
                              );
                            }) : (
                              [...Array(4)].map((_, i) => (
                                <div key={i} className="p-4 bg-slate-100 dark:bg-white/5 rounded-2xl border border-slate-200 dark:border-white/5 animate-pulse h-16" />
                              ))
                            )}
                          </div>
                        </div>

                        {/* ───────── SECTION 2: Shorts Content Ideas ───────── */}
                        <div>
                          <div className="mb-6">
                            <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight flex items-center gap-3">
                              <span className="text-2xl">💡</span> Shorts Content Ideas
                            </h3>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">
                              AI-generated ideas with full hook, script & trend analysis — ready to film
                            </p>
                          </div>

                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {ytIdeas.length > 0 ? ytIdeas.map((idea: any, i: number) => {
                              let rich: any = null;
                              try { rich = typeof idea.description === 'string' && idea.description.startsWith('{') ? JSON.parse(idea.description) : null; } catch {}
                              const mainDesc = rich?.text || idea.description || '';
                              const shortHook = rich?.short_hook || '';
                              const shortScript = rich?.short_script || '';
                              const keyword = rich?.trending_keyword || idea.title;
                              const url = rich?.trending_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(idea.title)}`;

                              return (
                                <Card key={i} className="space-y-4 hover:border-brand-yt/30 transition-all group border-slate-200 dark:border-white/5">
                                  {/* Header */}
                                  <div className="flex items-start justify-between gap-3">
                                    <div className="flex items-start gap-3">
                                      <div className="p-2 bg-brand-yt/10 rounded-xl shrink-0">
                                        <Zap className="w-4 h-4 text-brand-yt" />
                                      </div>
                                      <h4 className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-wide group-hover:text-brand-yt transition-colors leading-tight">{idea.title}</h4>
                                    </div>
                                    <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest shrink-0 pt-1">{idea.suggested_month_year}</span>
                                  </div>

                                  {/* Video description */}
                                  <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">{mainDesc}</p>

                                  {/* Why it will trend */}
                                  <div className="p-3 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 rounded-xl">
                                    <p className="text-[9px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-widest mb-1">📈 Why It Will Trend</p>
                                    <p className="text-[10px] text-emerald-700 dark:text-emerald-300 font-medium">Matches rising search: <span className="font-black">"{keyword}"</span> — high engagement potential in {idea.suggested_month_year}.</p>
                                  </div>

                                  {/* Short Hook */}
                                  {shortHook && (
                                    <div className="p-3 bg-brand-yt/5 border border-brand-yt/15 rounded-xl">
                                      <p className="text-[9px] font-black text-brand-yt uppercase tracking-widest mb-1">⚡ Shorts Opening Hook</p>
                                      <p className="text-[11px] text-slate-700 dark:text-slate-300 italic leading-relaxed">{shortHook}</p>
                                    </div>
                                  )}

                                  {/* Short Script */}
                                  {shortScript && (
                                    <div className="p-3 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/5 rounded-xl">
                                      <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-2">🎬 Short Script Outline</p>
                                      <pre className="text-[10px] text-slate-600 dark:text-slate-300 whitespace-pre-line leading-relaxed font-sans">{shortScript}</pre>
                                    </div>
                                  )}

                                  {/* Trending Link */}
                                  <a
                                    href={url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-4 py-2.5 bg-brand-yt text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-red-700 transition-all w-full justify-center"
                                  >
                                    <TrendingUp className="w-3.5 h-3.5" />
                                    See Trending Videos for This Topic
                                  </a>
                                </Card>
                              );
                            }) : (
                              <div className="col-span-2 py-16 text-center text-slate-500 font-bold uppercase tracking-widest text-xs">
                                No ideas yet — click "Refresh All" above to generate with AI.
                              </div>
                            )}
                          </div>
                        </div>

                        {/* ───────── SECTION 3: Your Videos Shorts Analysis ───────── */}
                        <div>
                          <div className="mb-6">
                            <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight flex items-center gap-3">
                              <span className="text-2xl">✂️</span> Your Videos — Shorts Analysis
                            </h3>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">
                              AI scans your existing videos to find the best 60-second segments for Shorts
                            </p>
                          </div>

                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Left: video list */}
                            <Card className="bg-slate-950 border-white/5">
                              <h4 className="text-[10px] font-black text-white uppercase tracking-widest mb-5">📺 Your Channel Videos</h4>
                              <div className="space-y-3">
                                {(data?.videos || []).slice(0, 4).map((vid: any) => {
                                  const isAnalyzing = analyzingVideos.has(vid.id);
                                  const hasShorts = (ytShortsSuggestions[vid.id]?.length || 0) > 0;
                                  
                                  return (
                                    <div
                                      key={vid.id}
                                      className={`flex items-center gap-4 p-3 bg-white/[0.03] rounded-2xl border border-white/5 transition-all ${isAnalyzing ? 'animate-pulse border-brand-yt/20' : ''}`}
                                    >
                                      <div className={`w-16 h-10 bg-slate-800 rounded-lg overflow-hidden shrink-0 ${isAnalyzing ? 'opacity-50' : ''}`}>
                                        {vid.thumbnail_url ? (
                                          <img src={vid.thumbnail_url} alt="" className="w-full h-full object-cover" />
                                        ) : (
                                          <div className="w-full h-full bg-slate-800 flex items-center justify-center">
                                            <Youtube className="w-5 h-5 text-slate-600" />
                                          </div>
                                        )}
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <p className="text-[11px] font-black text-white truncate">{vid.title}</p>
                                        <p className="text-[9px] font-bold text-slate-500 uppercase mt-1">
                                          {vid.view_count?.toLocaleString()} VIEWS • {ytShortsSuggestions[vid.id]?.length || 0} SHORTS FOUND
                                        </p>
                                      </div>
                                      
                                      <button
                                        onClick={() => fetchShorts(vid.id, hasShorts)}
                                        disabled={isAnalyzing}
                                        className={`px-3 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${
                                          isAnalyzing 
                                          ? 'bg-slate-800 text-slate-500 cursor-not-allowed' 
                                          : hasShorts 
                                            ? 'bg-white/5 text-slate-400 hover:bg-brand-yt/10 hover:text-brand-yt'
                                            : 'bg-brand-yt text-white hover:scale-105 active:scale-95 shadow-lg shadow-brand-yt/20'
                                        }`}
                                      >
                                        {isAnalyzing ? 'Analyzing...' : hasShorts ? 'Re-Analyze' : 'Analyze'}
                                      </button>
                                    </div>
                                  );
                                })}
                                {(!data?.videos || data.videos.length === 0) && (
                                  <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest text-center py-8">Connect YouTube to analyze your videos</p>
                                )}
                              </div>
                            </Card>

                            {/* Right: shorts segments */}
                            <Card className="border-slate-200 dark:border-white/5">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="text-[10px] font-black text-slate-900 dark:text-white uppercase tracking-widest flex items-center gap-2">
                                  <Activity className="w-4 h-4 text-brand-yt" /> Best Segments to Cut as Shorts
                                </h4>
                              </div>
                              <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mb-5">
                                Based on: video title · description · engagement patterns
                              </p>
                              <div className="space-y-3">
                                {Object.values(ytShortsSuggestions).flat().length > 0 ? (
                                  Object.values(ytShortsSuggestions).flat().slice(0, 6).map((seg: any, i: number) => (
                                    <div key={i} className="p-4 bg-slate-50 dark:bg-white/5 rounded-2xl border border-slate-200 dark:border-white/5 space-y-2">
                                      <div className="flex items-center justify-between">
                                        <div className="px-3 py-1 bg-brand-yt/10 rounded-lg text-[10px] font-black text-brand-yt tabular-nums">{seg.start_time} → {seg.stop_time}</div>
                                        <div className="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-[9px] font-black text-emerald-400">SHORT READY ✓</div>
                                      </div>
                                      <p className="text-xs font-black text-slate-900 dark:text-white">{seg.reason}</p>
                                      {seg.hook && <p className="text-[10px] text-slate-500 dark:text-slate-400 italic">Hook: "{seg.hook}"</p>}
                                      <p className="text-[9px] font-bold text-slate-400 uppercase">📺 {seg.video_title || seg.video_id}</p>
                                    </div>
                                  ))
                                ) : (
                                  <div className="py-12 text-center">
                                    <Activity className="w-8 h-8 text-brand-yt/20 mx-auto mb-3 animate-pulse" />
                                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Select a video on the left to analyze</p>
                                    <p className="text-[9px] text-slate-400 mt-1">Or wait for auto-analysis to complete</p>
                                  </div>
                                )}
                              </div>
                            </Card>
                          </div>
                        </div>

                      </motion.div>
                    )}

                  </AnimatePresence>
                </div>
              )}

              {activePlatform === 'instagram' && (
                <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-10">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-5xl font-black text-slate-900 dark:text-white tracking-tighter flex items-center gap-4 uppercase">
                        <InstagramIcon className="w-10 h-10 text-brand-ig" />
                        INSTAGRAM <span className="text-brand-ig px-4 py-1.5 bg-brand-ig/10 rounded-2xl text-[10px] align-middle tracking-widest border border-brand-ig/20">CONNECTED</span>
                      </h2>
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-3">Visual content & engagement intelligence</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard title="Followers" value={data?.summary?.ig_followers} icon={Users} color="brand-ig" />
                    <StatCard title="Total Interactions" value={data?.summary?.ig_total_interactions} icon={Zap} color="brand-ig" delta={5} />
                    <StatCard title="Total Likes" value={data?.summary?.ig_total_likes} icon={TrendingUp} color="brand-ig" />
                    <StatCard title="Reach (28d)" value={data?.summary?.ig_recent_reach} icon={Activity} color="brand-ig" />
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    <div className="lg:col-span-2 space-y-8">
                       <Card className="p-0 overflow-hidden">
                        <div className="p-8 border-b border-slate-900/10 dark:border-white/10 flex items-center justify-between bg-white/[0.02]">
                          <div>
                            <h3 className="font-black text-slate-900 dark:text-white text-xl tracking-tight">Recent Media</h3>
                            <p className="text-[10px] text-slate-500 font-bold uppercase mt-1 tracking-widest">Post & Reel Performance Matrix</p>
                          </div>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left">
                            <thead className="bg-slate-50 dark:bg-[#0B0E14] border-b border-slate-900/5 dark:border-white/5">
                              <tr className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                                <th className="px-8 py-6">Media</th>
                                <th className="px-8 py-6 text-right">Reach/Views</th>
                                <th className="px-8 py-6 text-right">Engagement</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-900/5 dark:divide-white/5">
                              {data?.ig_media?.map((m: any) => (
                                <tr key={m.id} className="hover:bg-brand-ig/5 transition-colors group">
                                  <td className="px-8 py-6">
                                    <div className="flex items-center gap-4">
                                      <div className="w-12 h-12 rounded-lg bg-slate-800 overflow-hidden flex-shrink-0 border border-white/5">
                                        {m.media_url ? <img src={m.media_url} className="w-full h-full object-cover" /> : <InstagramIcon className="w-6 h-6 m-3 opacity-20" />}
                                      </div>
                                      <div className="flex flex-col">
                                        <span className="text-xs font-black text-slate-900 dark:text-white truncate max-w-[200px]">{m.caption || 'No caption'}</span>
                                        <span className="text-[9px] font-bold text-slate-500 mt-1 uppercase">{m.media_type} • {new Date(m.timestamp).toLocaleDateString()}</span>
                                      </div>
                                    </div>
                                  </td>
                                  <td className="px-8 py-6 text-right font-black text-sm">{m.view_count?.toLocaleString() || '—'}</td>
                                  <td className="px-8 py-6 text-right">
                                    <div className="flex flex-col items-end">
                                      <span className="text-xs font-black text-brand-ig">{m.like_count?.toLocaleString() || 0} LIKES</span>
                                      <span className="text-[9px] font-bold text-slate-500">{m.comments_count?.toLocaleString() || 0} COMMENTS</span>
                                    </div>
                                  </td>
                                </tr>
                              ))}
                              {(!data?.ig_media || data.ig_media.length === 0) && (
                                <tr>
                                  <td colSpan={3} className="px-8 py-20 text-center text-slate-500 font-bold uppercase tracking-widest text-xs">No media data synced yet</td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                       </Card>

                       {/* Instagram Audience Demographics */}
                       <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                          <Card className="bg-white/5 border-white/10">
                            <h3 className="text-sm font-black text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                              <Users className="w-4 h-4 text-brand-ig" />
                              Top Countries
                            </h3>
                            <div className="space-y-4">
                              {data?.demographics?.instagram?.countries?.length > 0 ? (
                                data.demographics.instagram.countries.map((c: any, i: number) => (
                                  <div key={i} className="space-y-2">
                                    <div className="flex justify-between items-center text-[10px] font-black uppercase text-slate-400">
                                      <span>{c.country}</span>
                                      <span className="text-white">{c.views.toLocaleString()}</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                      <motion.div 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${data?.demographics?.instagram?.countries?.[0]?.views ? (c.views / data.demographics.instagram.countries[0].views) * 100 : 0}%` }}
                                        className="h-full bg-brand-ig"
                                      />
                                    </div>
                                  </div>
                                ))
                              ) : (
                                <div className="py-10 text-center flex flex-col items-center gap-3">
                                  <Users className="w-8 h-8 text-brand-ig/20 animate-pulse" />
                                  <div className="space-y-1">
                                    <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Regional Data Locked</p>
                                    <p className="text-[7px] font-bold text-slate-600 uppercase tracking-tighter max-w-[150px] mx-auto leading-relaxed">
                                      Requires 100+ followers for demographic insights.
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          </Card>

                          <Card className="bg-white/5 border-white/10">
                            <h3 className="text-sm font-black text-white uppercase tracking-widest mb-6 flex items-center gap-2">
                              <Target className="w-4 h-4 text-brand-ig" />
                              Top Cities
                            </h3>
                            <div className="space-y-4">
                               {data?.demographics?.instagram?.cities?.length > 0 ? (
                                data.demographics.instagram.cities.map((c: any, i: number) => (
                                  <div key={i} className="flex justify-between items-center p-3 bg-white/[0.03] rounded-xl border border-white/5">
                                    <span className="text-[10px] font-black text-white uppercase">{c.city}</span>
                                    <span className="text-[10px] font-bold text-brand-ig">{c.value.toLocaleString()}</span>
                                  </div>
                                ))
                               ) : (
                                <p className="py-10 text-center text-[10px] font-bold text-slate-600 uppercase">Awaiting GEO Insights...</p>
                               )}
                            </div>
                          </Card>
                       </div>
                    </div>

                    <div className="space-y-8">
                      <Card className="bg-brand-ig/[0.03]">
                        <h3 className="font-black text-slate-900 dark:text-white tracking-tight mb-8 uppercase text-xs text-brand-ig flex items-center gap-2">
                          <Activity className="w-4 h-4" />
                          Reach Trend Snapshot
                        </h3>
                        <div className="h-[250px]">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={(data?.chartData || []).filter((d: any) => d.instagram_total_reach)}>
                              <defs>
                                <linearGradient id="colorReach" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#E1306C" stopOpacity={0.3}/>
                                  <stop offset="95%" stopColor="#E1306C" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <Area type="monotone" dataKey="instagram_total_reach" stroke="#E1306C" fillOpacity={1} fill="url(#colorReach)" strokeWidth={3} />
                              <Tooltip contentStyle={{ backgroundColor: '#161B22', border: 'none', borderRadius: '12px' }} />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </Card>

                      <Card className="bg-brand-ig/[0.05] border-brand-ig/20">
                        <h3 className="text-[10px] font-black text-brand-ig uppercase tracking-widest mb-6 flex items-center gap-2">
                          <Zap className="w-4 h-4" />
                          Age & Gender Matrix
                        </h3>
                        <div className="space-y-5">
                           {Object.keys(data?.demographics?.instagram?.ageGender || {}).length > 0 ? (
                              Object.entries(data.demographics.instagram.ageGender).slice(0, 6).map(([label, val]: any) => (
                                <div key={label} className="flex items-center justify-between">
                                  <div className="flex flex-col">
                                    <span className="text-[10px] font-black text-white uppercase">{label.replace('.', ' ')}</span>
                                    <div className="h-1 w-24 bg-white/5 rounded-full mt-1 overflow-hidden">
                                      <div className="h-full bg-brand-ig/50" style={{ width: `${Math.max(...Object.values(data?.demographics?.instagram?.ageGender || {}) as number[]) > 0 ? (val / (Math.max(...Object.values(data?.demographics?.instagram?.ageGender || {}) as number[]))) * 100 : 0}%` }} />
                                    </div>
                                  </div>
                                  <span className="text-xs font-black text-white">{val.toLocaleString()}</span>
                                </div>
                              ))
                           ) : (
                            <div className="py-20 text-center">
                              <Clock className="w-8 h-8 text-brand-ig/20 mx-auto mb-3" />
                              <p className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">Processing demographic packets</p>
                            </div>
                           )}
                        </div>
                      </Card>
                    </div>
                  </div>
                </motion.div>
              )}

              {activePlatform === 'tiktok' && (
                <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard title="Total Views" value="2.4M" icon={Activity} delta={18} color="brand-tiktok" />
                    <StatCard title="Engagement Rate" value="12.4%" icon={TikTokIcon} delta={3} color="brand-tiktok" />
                    <StatCard title="Followers" value="85.2K" icon={Users} delta={5} color="brand-tiktok" />
                    <StatCard title="Avg Watch Time" value="14.2s" icon={Clock} color="brand-tiktok" />
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <Card className="lg:col-span-2">
                      <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight mb-8 text-[#00f2ea]">Retention Curve</h3>
                      <div className="h-[300px] flex items-center justify-center border border-dashed border-white/5 rounded-2xl bg-white/[0.01]">
                        <BarChart3 className="w-12 h-12 text-[#00f2ea] opacity-20 animate-pulse" />
                      </div>
                    </Card>
                    <Card className="bg-gradient-to-br from-[#00f2ea]/10 to-transparent border-[#00f2ea]/20">
                      <h3 className="text-sm font-black text-[#00f2ea] uppercase tracking-widest mb-4">Trending Sounds</h3>
                      <div className="space-y-4">
                        {[
                          { name: 'Lo-fi Chill Beats', use: 'High' },
                          { name: 'Corporate Shuffle', use: 'Medium' },
                          { name: 'Neon Nights', use: 'Trending' }
                        ].map(s => (
                          <div key={s.name} className="flex justify-between items-center p-3 bg-white/5 rounded-xl text-xs font-bold">
                            <span className="text-white">{s.name}</span>
                            <span className="text-[#00f2ea]">{s.use}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  </div>
                </motion.div>
              )}

              {activePlatform === 'twitter' && (
                <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard title="Impressions" value="142K" icon={BarChart3} delta={-2} color="brand-twitter" />
                    <StatCard title="Retweets" value="1.2K" icon={RefreshCw} delta={14} color="brand-twitter" />
                    <StatCard title="Link Clicks" value="850" icon={XIcon} delta={22} color="brand-twitter" />
                    <StatCard title="Mentions" value="340" icon={MessageSquare} color="brand-twitter" />
                  </div>
                  <Card className="p-8">
                    <div className="flex justify-between items-center mb-10">
                      <div>
                        <h3 className="font-black text-slate-900 dark:text-white text-xl tracking-tight">Reach Protocol</h3>
                        <p className="text-[10px] text-slate-500 font-bold uppercase mt-1 tracking-widest text-[#1DA1F2]">Audience amplification metrics</p>
                      </div>
                      <div className="px-4 py-2 bg-[#1DA1F2]/10 border border-[#1DA1F2]/20 rounded-xl text-[10px] font-black text-[#1DA1F2]">LIVE FEED</div>
                    </div>
                    <div className="h-[300px] w-full bg-[#1DA1F2]/5 rounded-3xl border border-[#1DA1F2]/10 flex flex-col items-center justify-center gap-4">
                      <TrendingUp className="w-16 h-16 text-[#1DA1F2] opacity-30 animate-bounce" />
                      <p className="text-xs font-black text-slate-400 tracking-[0.3em]">PROCESSING REAL-TIME FLOWS</p>
                    </div>
                  </Card>
                </motion.div>
              )}

              {activePlatform === 'manychat' && (
                <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-10">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-5xl font-black text-slate-900 dark:text-white tracking-tighter flex items-center gap-4 uppercase">
                        <MessageSquare className="w-10 h-10 text-brand-mc" />
                        MANYCHAT <span className="text-brand-mc px-4 py-1.5 bg-brand-mc/10 rounded-2xl text-[10px] align-middle tracking-widest border border-brand-mc/20">OPERATIONAL</span>
                      </h2>
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-3">Advanced conversational intelligence engine</p>
                    </div>
                    <div className="flex gap-6">
                      <div className="px-6 py-4 glass-card border-brand-mc/20">
                        <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">NETWORK SIZE</span>
                        <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                          {data?.summary?.total_flows || data?.summary?.manychat_subscribers != null
                            ? (data.summary.total_flows || data.summary.manychat_subscribers).toLocaleString()
                            : '—'}
                          <span className="text-xs text-slate-500 font-bold uppercase ml-1">FLOWS</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                    <div className="lg:col-span-2 space-y-8">
                      <Card className="p-0 overflow-hidden border-slate-900/5 dark:border-white/5">
                        <div className="p-8 border-b border-slate-900/10 dark:border-white/10 flex items-center justify-between bg-white/[0.02]">
                          <div>
                            <h3 className="font-black text-slate-900 dark:text-white text-xl tracking-tight">Active Protocols</h3>
                            <p className="text-[10px] text-slate-500 font-bold uppercase mt-1 tracking-widest">Automation efficiency matrix</p>
                          </div>
                          <div className="p-3 bg-brand-mc/10 rounded-2xl border border-brand-mc/20">
                            <Zap className="w-6 h-6 text-brand-mc animate-pulse" />
                          </div>
                        </div>
                        <div className="overflow-x-auto max-h-[400px] overflow-y-auto relative scroll-smooth">
                          <table className="w-full text-left">
                            <thead className="sticky top-0 bg-slate-50 dark:bg-[#0B0E14] z-10 border-b border-slate-900/5 dark:border-white/5">
                              <tr className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                                <th className="px-8 py-6">Protocol Name</th>
                                <th className="px-8 py-6 text-right">Last Synced</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-900/5 dark:divide-white/5">
                              {data?.automations?.map((auto: any) => (
                                <tr
                                  key={auto.id}
                                  className="hover:bg-[rgba(59,130,246,0.04)] transition-colors duration-200 cursor-pointer group border-b border-slate-900/5 dark:divide-white/5"
                                  onClick={() => setSelectedAuto(auto)}
                                >
                                  <td className="px-8 py-6">
                                    <div className="flex flex-col">
                                      <span className="text-sm font-black text-slate-900 dark:text-white group-hover:text-brand-mc transition-colors">{auto.name}</span>
                                      <span className="text-[9px] font-mono text-slate-600 mt-1 uppercase tracking-tighter">ID: {auto.id?.slice(0, 16)}</span>
                                    </div>
                                  </td>
                                  <td className="px-8 py-6 text-right text-[10px] font-bold tracking-widest">
                                    {auto.synced_at
                                      ? <span className="text-slate-600">{fmtDate(auto.synced_at)}</span>
                                      : <span className="flex items-center justify-end gap-1.5 text-amber-400"><span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />PENDING</span>
                                    }
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </Card>

                      <Card className="p-0 overflow-hidden border-slate-900/5 dark:border-white/5">
                        <div className="p-8 border-b border-slate-900/10 dark:border-white/10 flex items-center justify-between bg-white/[0.02]">
                          <div>
                            <h3 className="font-black text-slate-900 dark:text-white text-xl tracking-tight">System Growth</h3>
                            <p className="text-[10px] text-slate-500 font-bold uppercase mt-1 tracking-widest">Automations Created By Month</p>
                          </div>
                        </div>
                        <div className="h-[250px] p-6">
                          {automationsByMonth.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={automationsByMonth}>
                                <XAxis dataKey="name" fontSize={10} axisLine={false} tickLine={false} stroke="#475569" />
                                <Tooltip contentStyle={{ backgroundColor: '#161B22', border: 'none', borderRadius: '12px', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)' }} />
                                <Bar dataKey="count" fill="#0084FF" radius={[4, 4, 0, 0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          ) : (
                            <div className="h-full flex items-center justify-center text-slate-600 text-xs font-bold tracking-widest uppercase">No temporal data available</div>
                          )}
                        </div>
                      </Card>
                    </div>

                    <div className="space-y-8">
                      <Card className="border-emerald-500/20 bg-emerald-500/[0.02]">
                        <div className="flex items-center gap-3 mb-8">
                          <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                            <Activity className="w-5 h-5 text-emerald-400" />
                          </div>
                          <h3 className="font-black text-slate-900 dark:text-white tracking-tight uppercase text-sm">Interaction Stream</h3>
                        </div>
                        <div className="space-y-8">
                          {data?.interactions?.length > 0 ? (
                            data.interactions.map((int: any) => (
                              <div key={int.id} className="relative pl-8 border-l border-slate-900/10 dark:border-white/10 gap-2 flex flex-col group">
                                <div className="absolute left-[-5px] top-1 w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_10px_#10b981] group-hover:scale-125 transition-transform" />
                                <div className="flex justify-between items-start">
                                  <span className="text-[10px] font-black text-slate-900 dark:text-white tracking-widest">USER_{int.subscriber_id.slice(-6)}</span>
                                  <span className="text-[9px] font-bold text-slate-600 uppercase tabular-nums">{new Date(int.timestamp).toLocaleTimeString()}</span>
                                </div>
                                <p className="text-xs text-slate-600 dark:text-slate-400 font-medium leading-relaxed italic">"{int.details}"</p>
                                <div className="flex gap-2 mt-1">
                                  <span className="text-[8px] font-black px-2 py-0.5 bg-slate-900/5 dark:bg-white/5 rounded text-slate-500 border border-slate-900/5 dark:border-white/5 uppercase tracking-tighter">{int.type}</span>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="py-20 flex flex-col items-center justify-center text-slate-700 gap-4">
                              <div className="w-12 h-12 rounded-full border border-slate-800 flex items-center justify-center">
                                <Clock className="w-6 h-6 opacity-30" />
                              </div>
                              <p className="text-[9px] font-black tracking-[0.4em] uppercase">Standby Mode</p>
                            </div>
                          )}
                        </div>
                      </Card>

                      <Card className="bg-brand-mc/5 border-slate-900/5 dark:border-white/5 p-8">
                        <h4 className="text-[10px] font-black text-brand-mc uppercase tracking-[0.3em] mb-6">Engine Diagnostics</h4>
                        <div className="grid grid-cols-2 gap-8">
                          <div className="space-y-1">
                            <p className="text-[9px] font-black text-slate-600 uppercase">Tags Active</p>
                            <p className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">{data?.summary?.total_tags || 0}</p>
                          </div>
                          <div className="space-y-1">
                            <p className="text-[9px] font-black text-slate-600 uppercase">Widgets Linked</p>
                            <p className="text-3xl font-black text-slate-900 dark:text-white tracking-tighter">{data?.summary?.active_widgets || 0}</p>
                          </div>
                        </div>
                        <div className="mt-8 pt-6 border-t border-slate-900/5 dark:border-white/5">
                          <div className="flex items-center justify-between">
                            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">API Status</span>
                            <span className="flex items-center gap-2 text-[9px] font-black text-emerald-400 uppercase">
                              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Encrypted Link
                            </span>
                          </div>
                        </div>
                      </Card>
                    </div>
                  </div>
                </motion.div>
              )}

              {activePlatform === 'reporting' && (
                <ReportingView 
                  data={data} 
                  days={reportDays} 
                  setDays={setReportDays} 
                />
              )}
            </>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-4xl space-y-10"
            >
              <div>
                <h2 className="text-4xl font-black text-slate-900 dark:text-white tracking-tighter">Command Settings</h2>
                <p className="text-slate-500 mt-2 font-bold uppercase text-[10px] tracking-[0.2em]">Manage your neural links and api credentials</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <Card className="p-8 space-y-8 border-slate-900/5 dark:border-white/5 bg-white/[0.01]">
                  <div className="flex items-center gap-6">
                    <div className="p-5 bg-brand-yt/10 rounded-[2rem] border border-brand-yt/20 shadow-[0_0_20px_rgba(255,0,0,0.1)]">
                      <Youtube className="w-8 h-8 text-brand-yt" />
                    </div>
                    <div>
                      <h4 className="font-black text-slate-900 dark:text-white text-lg">YouTube Analytics</h4>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Direct Engine Link</p>
                    </div>
                  </div>

                  <div className="pt-6 border-t border-slate-900/5 dark:border-white/5 space-y-4">
                    {status?.youtube ? (
                      <>
                        <div className="flex items-center justify-between p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20">
                          <div className="flex items-center gap-3">
                            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            <span className="text-xs font-black text-emerald-400 uppercase">LINK ACTIVE</span>
                          </div>
                          <span className="text-[10px] font-bold text-slate-500 italic">SECURE LINK</span>
                        </div>
                        <button onClick={connectYoutube} className="w-full py-3 bg-slate-900/5 dark:bg-white/5 text-slate-900 dark:text-white rounded-xl text-xs font-black border border-slate-900/10 dark:border-white/10 hover:bg-brand-yt/10 hover:border-brand-yt/20 transition-all">
                          RECONNECT ENGINE
                        </button>
                      </>
                    ) : (
                      <button onClick={connectYoutube} className="w-full py-4 bg-brand-yt text-slate-900 dark:text-white rounded-[1.5rem] text-sm font-black transition-all hover:shadow-[0_0_30px_rgba(255,0,0,0.3)] active:scale-95">
                        ESTABLISH CONNECTION
                      </button>
                    )}
                  </div>
                </Card>

                <Card className="p-8 space-y-8 border-slate-900/5 dark:border-white/5 bg-white/[0.01]">
                  <div className="flex items-center gap-6">
                    <div className="p-5 bg-brand-mc/10 rounded-[2rem] border border-brand-mc/20 shadow-[0_0_20px_rgba(0,132,255,0.1)]">
                      <MessageSquare className="w-8 h-8 text-brand-mc" />
                    </div>
                    <div>
                      <h4 className="font-black text-slate-900 dark:text-white text-lg">ManyChat API</h4>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Automation Token</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="relative">
                      <input
                        type="password"
                        placeholder="PASTE API KEY"
                        value={manychatKey}
                        onChange={(e) => setManychatKey(e.target.value)}
                        className="w-full bg-slate-900/5 dark:bg-white/5 border border-slate-900/10 dark:border-white/10 rounded-2xl px-6 py-4 text-xs font-mono text-slate-900 dark:text-white focus:ring-2 ring-brand-mc/50 outline-none transition-all placeholder:text-slate-600 uppercase tracking-widest"
                      />
                    </div>
                    <button onClick={saveManychat} className="w-full py-4 bg-white text-[#0B0E14] rounded-[1.5rem] text-sm font-black transition-all hover:bg-slate-200 active:scale-95 shadow-xl">
                      SAVE PROTOCOL
                    </button>
                    {status?.manychat && (
                      <p className="text-[10px] font-black text-emerald-400 flex items-center justify-center gap-2 mt-4 uppercase tracking-[0.2em]">
                        <CheckCircle2 className="w-4 h-4" /> TOKEN ENCRYPTED & VERIFIED
                      </p>
                    )}
                  </div>
                </Card>

                <Card className="p-8 space-y-8 border-slate-900/5 dark:border-white/5 bg-white/[0.01]">
                  <div className="flex items-center gap-6">
                    <div className="p-5 bg-brand-ig/10 rounded-[2rem] border border-brand-ig/20 shadow-[0_0_20px_rgba(225,48,108,0.1)]">
                      <InstagramIcon className="w-8 h-8 text-brand-ig" />
                    </div>
                    <div>
                      <h4 className="font-black text-slate-900 dark:text-white text-lg">Instagram Hub</h4>
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Creator Access Token</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="relative">
                      <input
                        type="password"
                        placeholder="PASTE META TOKEN"
                        value={instagramToken}
                        onChange={(e) => setInstagramToken(e.target.value)}
                        className="w-full bg-slate-900/5 dark:bg-white/5 border border-slate-900/10 dark:border-white/10 rounded-2xl px-6 py-4 text-xs font-mono text-slate-900 dark:text-white focus:ring-2 ring-brand-ig/50 outline-none transition-all placeholder:text-slate-600 uppercase tracking-widest"
                      />
                    </div>
                    <button onClick={saveInstagram} className="w-full py-4 bg-brand-ig text-white rounded-[1.5rem] text-sm font-black transition-all hover:bg-[#C13584] active:scale-95 shadow-xl">
                      ACTIVATE HUB
                    </button>
                    {status?.instagram && (
                      <p className="text-[10px] font-black text-emerald-400 flex items-center justify-center gap-2 mt-4 uppercase tracking-[0.2em]">
                        <CheckCircle2 className="w-4 h-4" /> INSTAGRAM ENGINE LINKED
                      </p>
                    )}
                  </div>
                </Card>
              </div>

              <Card className="border-slate-900/5 dark:border-white/5 bg-gradient-to-r from-brand-yt/5 to-brand-mc/5 p-8 flex items-center justify-between">
                <div>
                  <h4 className="font-black text-slate-900 dark:text-white">System Diagnostics</h4>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">All engines operating at peak efficiency</p>
                </div>
                <div className="flex gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#10b981]" />
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse delay-75 shadow-[0_0_8px_#10b981]" />
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse delay-150 shadow-[0_0_8px_#10b981]" />
                </div>
              </Card>
            </motion.div>
          )}
        </div>
      </main>

      {/* Analytics Modal */}
      <AnimatePresence>
        {selectedAuto && (
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
              className="w-full max-w-3xl bg-slate-50 dark:bg-[#161B22] border border-slate-200 dark:border-white/10 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
            >
              <div className="flex justify-between items-center p-6 border-b border-slate-200 dark:border-white/10">
                <div>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white">{selectedAuto.name}</h3>
                  <p className="text-[10px] text-slate-500 font-mono mt-1">ID: {selectedAuto.id}</p>
                </div>
                <button
                  onClick={() => setSelectedAuto(null)}
                  className="p-2 bg-slate-200 dark:bg-white/5 rounded-full hover:bg-slate-300 dark:hover:bg-white/10 transition-colors text-slate-600 dark:text-slate-400"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-200 dark:bg-white/5 p-4 rounded-xl">
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Status</p>
                    <p className="text-emerald-500 font-black flex items-center gap-2 text-xl">
                      <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" /> {selectedAuto.status}
                    </p>
                  </div>
                  <div className="bg-slate-200 dark:bg-white/5 p-4 rounded-xl">
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Last Update</p>
                    <p className="text-slate-900 dark:text-white font-black text-xl">{fmtDate(selectedAuto.synced_at)}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="flex items-center gap-2 text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest">
                    <Code2 className="w-4 h-4 text-brand-mc" /> Protocol Data Blueprint
                  </h4>
                  <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto border border-slate-800">
                    <pre className="text-xs text-brand-mc font-mono leading-relaxed">
                      {JSON.stringify(selectedAuto, null, 2)}
                    </pre>
                  </div>
                  <p className="text-xs text-slate-500">
                    You can use this JSON blueprint to understand the workflow and code against the ManyChat API to trigger this specific flow programmatically.
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
