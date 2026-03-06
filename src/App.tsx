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
  Code2
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

const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn("glass-card p-6", className)}>
    {children}
  </div>
);

const StatCard = ({ title, value, icon: Icon, delta, unit = "", color = "brand-yt" }: any) => (
  <Card className="flex flex-col gap-4 relative overflow-hidden group">
    <div className="flex justify-between items-start">
      <div className={cn("p-2 rounded-xl border", color === 'brand-yt' ? 'bg-brand-yt/10 border-brand-yt/20 text-brand-yt' : 'bg-brand-mc/10 border-brand-mc/20 text-brand-mc')}>
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
        {unit}{value != null && value !== '' && value !== 0 ? (typeof value === 'number' ? value.toLocaleString() : value) : (value === 0 ? '—' : (value || '—'))}
      </h3>
    </div>
  </Card>
);

const YT_TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'content', label: 'Content', icon: Youtube },
  { id: 'audience', label: 'Audience', icon: Users },
  { id: 'trends', label: 'Trends', icon: TrendingUp },
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
  if (value === 0) return '—';
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

function ctrBadgeClass(ctr: number | null | undefined): string {
  if (ctr == null) return 'bg-slate-100 dark:bg-white/5 text-slate-500 border-slate-200 dark:border-white/10';
  if (ctr < 2) return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
  if (ctr < 4) return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
  return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
}

export default function App() {
  const [data, setData] = useState<any>(null);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [manychatKey, setManychatKey] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [theme, setTheme] = useState<'dark' | 'light'>('light');
  const [selectedAuto, setSelectedAuto] = useState<any>(null);
  const [trendsIdeas, setTrendsIdeas] = useState<any[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(false);
  const [trendsError, setTrendsError] = useState('');
  const [expandedIdea, setExpandedIdea] = useState<number | null>(null);
  const [copyMsg, setCopyMsg] = useState<number | null>(null);

  const automationsByMonth = React.useMemo(() => {
    if (!data?.automations) return [];
    const counts: Record<string, number> = {};
    [...data.automations].reverse().forEach((auto: any) => {
      // Use synced_at first, fall back to updated_at, then last_modified
      const ts = auto.synced_at || auto.updated_at || auto.last_modified;
      if (!ts) return;
      const d = new Date(ts);
      if (isNaN(d.getTime())) return;
      const month = d.toLocaleString('default', { month: 'short', year: '2-digit' });
      counts[month] = (counts[month] || 0) + 1;
    });
    return Object.entries(counts).map(([name, count]) => ({ name, count }));
  }, [data?.automations]);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const fetchData = async () => {
    const timer = setTimeout(() => { setLoading(false); setLoadError(true); }, 10000);
    try {
      const [dashRes, statusRes] = await Promise.all([
        fetch('/api/dashboard'),
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
    }, 10000);
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

  useEffect(() => {
    fetchData();

    const handleOAuth = (e: MessageEvent) => {
      if (e.data?.type === 'OAUTH_SUCCESS') fetchData();
    };
    window.addEventListener('message', handleOAuth);
    return () => window.removeEventListener('message', handleOAuth);
  }, []);

  const connectYoutube = async () => {
    const res = await fetch('/api/auth/youtube/url');
    const { url } = await res.json();
    window.open(url, 'youtube_auth', 'width=600,height=700');
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
    <div className="min-h-screen flex text-slate-700 dark:text-slate-300 font-sans">
      {/* Sidebar Navigation */}
      <nav className="fixed left-0 top-0 bottom-0 w-20 border-r border-slate-900/5 dark:border-white/5 flex flex-col items-center py-8 gap-8 bg-white/80 dark:bg-[#0D1117]/80 backdrop-blur-xl z-50">
        <div className="w-12 h-12 bg-gradient-to-br from-brand-yt to-brand-yt/60 rounded-2xl flex items-center justify-center shadow-lg shadow-brand-yt/20">
          <TrendingUp className="text-slate-900 dark:text-white w-6 h-6" />
        </div>
        <div className="flex flex-col gap-6">
          <button
            onClick={() => setShowSettings(false)}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", !showSettings ? "bg-slate-900/10 dark:bg-white/10 text-slate-900 dark:text-white shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
          >
            <LayoutDashboard className="w-6 h-6" />
            {!showSettings && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-brand-yt/20 blur-xl -z-10" />}
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className={cn("p-3 rounded-xl transition-all duration-300 group relative", showSettings ? "bg-slate-900/10 dark:bg-white/10 text-slate-900 dark:text-white shadow-xl" : "text-slate-500 hover:text-slate-900 dark:text-white hover:bg-slate-900/5 dark:bg-white/5")}
          >
            <Settings className="w-6 h-6" />
            {showSettings && <motion.div layoutId="nav-glow" className="absolute inset-0 bg-brand-yt/20 blur-xl -z-10" />}
          </button>
        </div>

        <div className="mt-auto flex flex-col gap-4">
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-3 rounded-xl bg-slate-900/5 dark:bg-white/5 text-slate-500 hover:text-slate-900 dark:text-white transition-all border border-transparent hover:border-slate-900/10 dark:hover:border-white/10"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? <Sun className="w-6 h-6" /> : <Moon className="w-6 h-6" />}
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pl-20 flex-1 min-h-screen">
        <header className="h-20 border-b border-slate-900/5 dark:border-white/5 flex items-center justify-between px-8 sticky top-0 bg-white/80 dark:bg-[#0B0E14]/80 backdrop-blur-md z-40">
          <div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              Social Intelligence <span className="text-brand-yt">.</span>
            </h1>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">Growth Command Center</p>
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
              {/* YouTube Section Container */}
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
                              if (!ag || Object.keys(ag).length === 0) return (
                                <div className="h-full flex flex-col items-center justify-center gap-3 text-slate-500">
                                  <Users className="w-10 h-10 opacity-20" />
                                  <p className="text-xs font-bold tracking-widest uppercase">Sync to populate audience data</p>
                                </div>
                              );
                              const chartData = Object.entries(ag).map(([key, val]: any) => ({
                                name: key.replace('_', ' '),
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
                              if (!countries || countries.length === 0) return (
                                <div className="py-10 flex flex-col items-center gap-3 text-slate-500">
                                  <Target className="w-8 h-8 opacity-20" />
                                  <p className="text-xs font-bold tracking-widest uppercase">No geo data yet</p>
                                </div>
                              );
                              const maxViews = countries[0]?.views || 1;
                              return countries.map((c: any, i: number) => (
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
                      className="space-y-8"
                    >
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* AI Inspiration Panel */}
                        <Card className="lg:col-span-2 bg-gradient-to-br from-brand-yt/5 to-transparent border-brand-yt/10">
                          <div className="flex items-center justify-between mb-6">
                            <div>
                              <h3 className="font-black text-slate-900 dark:text-white text-lg tracking-tight">AI Content Inspiration</h3>
                              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">Based on your top videos &amp; automations</p>
                            </div>
                            <button
                              onClick={fetchTrends}
                              disabled={trendsLoading}
                              className="flex items-center gap-2 px-4 py-2 bg-brand-yt/10 border border-brand-yt/20 text-brand-yt rounded-xl text-xs font-black hover:bg-brand-yt/20 transition-all disabled:opacity-50"
                            >
                              <RefreshCw className={cn('w-3 h-3', trendsLoading && 'animate-spin')} />
                              {trendsLoading ? 'GENERATING...' : 'GENERATE IDEAS'}
                            </button>
                          </div>
                          {trendsError && (
                            <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs text-amber-400 font-bold">{trendsError}</div>
                          )}
                          {trendsIdeas.length > 0 ? (
                            <div className="space-y-3">
                              {trendsIdeas.map((idea: any, i: number) => (
                                <div
                                  key={i}
                                  className="group p-4 bg-slate-900/5 dark:bg-white/5 rounded-xl border border-slate-900/5 dark:border-white/5 cursor-pointer hover:border-brand-yt/20 transition-all"
                                  onClick={() => setExpandedIdea(expandedIdea === i ? null : i)}
                                >
                                  <div className="flex items-start justify-between gap-4">
                                    <p className="text-sm font-black text-slate-900 dark:text-white">{idea.title}</p>
                                    <span className="shrink-0 text-[10px] font-black px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg">{idea.estimated_ctr} CTR</span>
                                  </div>
                                  {expandedIdea === i && (
                                    <div className="mt-3 pt-3 border-t border-slate-900/5 dark:border-white/5">
                                      <p className="text-xs text-slate-600 dark:text-slate-400 italic leading-relaxed">&quot;{idea.hook}&quot;</p>
                                      <button
                                        className="mt-3 text-[10px] font-black text-brand-yt hover:underline"
                                        onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(`${idea.title}\n\n${idea.hook}`); setCopyMsg(i); setTimeout(() => setCopyMsg(null), 2000); }}
                                      >
                                        {copyMsg === i ? '✓ COPIED!' : '⎘ COPY IDEA'}
                                      </button>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="py-12 flex flex-col items-center gap-4 text-slate-500">
                              <Zap className="w-10 h-10 opacity-20" />
                              <p className="text-xs font-bold tracking-widest uppercase text-center">Click &quot;Generate Ideas&quot; to get AI-powered content<br />ideas based on your real channel data.</p>
                            </div>
                          )}
                        </Card>

                        {/* Performance Matrix (replaces infinite spinner) */}
                        <Card>
                          <h3 className="font-black text-slate-900 dark:text-white tracking-tight mb-6">Performance Matrix</h3>
                          <div className="space-y-5">
                            {[
                              { label: 'Views (30d)', value: fmt(data?.summary?.recent_views), color: 'bg-brand-yt' },
                              { label: 'Watch Time', value: formatWatchTime(data?.summary?.watch_time_minutes), color: 'bg-blue-400' },
                              { label: 'Subscribers', value: fmt(data?.summary?.subscribers), color: 'bg-emerald-400' },
                              { label: 'Total Videos', value: fmt(data?.summary?.total_videos), color: 'bg-purple-400' },
                              { label: 'Recent Likes', value: fmt(data?.summary?.recent_likes), color: 'bg-amber-400' },
                            ].map((row) => (
                              <div key={row.label} className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <div className={cn('w-2 h-2 rounded-full', row.color)} />
                                  <span className="text-xs font-bold text-slate-600 dark:text-slate-400">{row.label}</span>
                                </div>
                                <span className="text-sm font-black text-slate-900 dark:text-white">{row.value}</span>
                              </div>
                            ))}
                          </div>
                          <div className="mt-6 pt-4 border-t border-slate-900/5 dark:border-white/5">
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Connect competitor channels to unlock competitive analysis</p>
                            <button className="mt-3 w-full py-2 border border-dashed border-slate-300 dark:border-white/10 rounded-xl text-xs font-black text-slate-500 hover:border-brand-yt/30 hover:text-brand-yt transition-all">+ Add Channel</button>
                          </div>
                        </Card>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Enhanced ManyChat Section */}
              <div className="pt-16 border-t border-slate-900/5 dark:border-white/5 space-y-10">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-5xl font-black text-slate-900 dark:text-white tracking-tighter flex items-center gap-4">
                      <MessageSquare className="w-10 h-10 text-brand-mc" />
                      MANYCHAT <span className="text-brand-mc px-4 py-1.5 bg-brand-mc/10 rounded-2xl text-[10px] align-middle tracking-widest border border-brand-mc/20">OPERATIONAL</span>
                    </h2>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.4em] mt-3">Advanced conversational intelligence engine</p>
                  </div>
                  <div className="flex gap-6">
                    <div className="px-6 py-4 glass-card border-brand-mc/20">
                      <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">NETWORK SIZE</span>
                      <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                        {data?.summary?.manychat_subscribers != null
                          ? data.summary.manychat_subscribers.toLocaleString()
                          : '—'}
                        <span className="text-xs text-slate-500 font-bold uppercase ml-1">CONTACTS</span>
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
                              <th className="px-6 py-6 text-center">Executions</th>
                              <th className="px-6 py-6 text-center">CTR</th>
                              <th className="px-8 py-6 text-right">Last Synced</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-900/5 dark:divide-white/5">
                            {data?.automations?.map((auto: any) => (
                              <tr
                                key={auto.id}
                                className="hover:bg-[rgba(59,130,246,0.04)] transition-colors duration-200 cursor-pointer group border-b border-slate-900/5 dark:border-white/5"
                                onClick={() => setSelectedAuto(auto)}
                              >
                                <td className="px-8 py-6">
                                  <div className="flex flex-col">
                                    <span className="text-sm font-black text-slate-900 dark:text-white group-hover:text-brand-mc transition-colors">{auto.name}</span>
                                    <span className="text-[9px] font-mono text-slate-600 mt-1 uppercase tracking-tighter">ID: {auto.id?.slice(0, 16)}</span>
                                  </div>
                                </td>
                                <td className="px-6 py-6 text-center text-sm font-black text-slate-900 dark:text-white">
                                  {auto.runs != null ? auto.runs.toLocaleString() : <span className="text-slate-400">—</span>}
                                </td>
                                <td className="px-6 py-6 text-center">
                                  <div className={cn('inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-black', ctrBadgeClass(auto.ctr))}>
                                    <Target className="w-3 h-3" />
                                    <span>{auto.ctr != null ? `${auto.ctr}%` : '—'}</span>
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
              </div>
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
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-slate-200 dark:bg-white/5 p-4 rounded-xl">
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Status</p>
                    <p className="text-emerald-500 font-black flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> {selectedAuto.status}
                    </p>
                  </div>
                  <div className="bg-slate-200 dark:bg-white/5 p-4 rounded-xl">
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Total Executions</p>
                    <p className="text-slate-900 dark:text-white font-black text-xl">{selectedAuto.runs}</p>
                  </div>
                  <div className="bg-brand-mc/10 p-4 rounded-xl border border-brand-mc/20">
                    <p className="text-[10px] text-brand-mc font-bold uppercase tracking-widest mb-1">Conversion Rate</p>
                    <p className="text-brand-mc font-black text-xl">{selectedAuto.ctr != null ? `${selectedAuto.ctr}%` : "—"}</p>
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
