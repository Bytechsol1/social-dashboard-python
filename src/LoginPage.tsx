import React, { useState } from 'react';
import { Zap, Mail, Lock, AlertCircle, Loader2 } from 'lucide-react';

interface LoginPageProps {
  onLogin: () => void;
}

// Simple hardcoded credentials — no email confirmation needed
const ADMIN_EMAIL = 'admin@gmail.com';
const ADMIN_PASS = 'admin';

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Small delay for UX feel
    await new Promise(r => setTimeout(r, 600));

    if (email.trim().toLowerCase() === ADMIN_EMAIL && password === ADMIN_PASS) {
      localStorage.setItem('dashboard_auth', 'true');
      onLogin();
    } else {
      setError('Invalid email or password.');
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-red-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl" />
      </div>

      {/* Dot grid */}
      <div className="absolute inset-0 opacity-[0.015]" style={{
        backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
        backgroundSize: '28px 28px'
      }} />

      <div className="relative z-10 w-full max-w-md px-6">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-3xl bg-gradient-to-br from-red-500 to-orange-500 shadow-[0_0_40px_rgba(239,68,68,0.4)] mb-6">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Social Intel</h1>
          <p className="text-slate-500 text-sm font-medium mt-2 tracking-wide">COMMAND CENTER ACCESS</p>
        </div>

        {/* Card */}
        <div className="bg-white/[0.03] border border-white/10 rounded-3xl p-8 backdrop-blur-xl shadow-[0_25px_50px_-12px_rgba(0,0,0,0.8)]">
          <h2 className="text-xl font-black text-white mb-1">Welcome back</h2>
          <p className="text-slate-500 text-sm font-medium mb-8">Sign in to access your dashboard</p>

          {error && (
            <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl mb-6">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <p className="text-red-400 text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            {/* Email */}
            <div>
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="admin@gmail.com"
                  required
                  className="w-full pl-11 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl text-white placeholder-slate-600 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-red-500/40 focus:border-red-500/40 transition-all"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-11 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl text-white placeholder-slate-600 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-red-500/40 focus:border-red-500/40 transition-all"
                />
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 mt-2 bg-gradient-to-r from-red-600 to-red-500 text-white rounded-2xl text-sm font-black uppercase tracking-widest transition-all hover:shadow-[0_0_30px_rgba(239,68,68,0.4)] hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Authenticating...
                </>
              ) : 'Enter Command Center →'}
            </button>
          </form>
        </div>

        <p className="text-center text-slate-700 text-xs mt-6 font-medium">
          Social Intelligence Dashboard · {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}
