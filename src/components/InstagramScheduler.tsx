import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Plus, 
  Trash2, 
  Clock, 
  Image as ImageIcon, 
  Send, 
  AlertCircle, 
  CheckCircle2, 
  X,
  RefreshCw,
  MoreVertical
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface ScheduledPost {
  id: number;
  media_url: string;
  caption: string;
  scheduled_at: string;
  status: 'pending' | 'published' | 'failed';
  error_message?: string;
  created_at: string;
}

export function InstagramScheduler() {
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  // Form State
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [caption, setCaption] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [isQueued, setIsQueued] = useState(false);

  const [dailyPostTime, setDailyPostTime] = useState("18:00");
  const [isVideo, setIsVideo] = useState(false);

  const fetchPosts = async () => {
    try {
      const res = await fetch('/api/instagram/scheduled-posts');
      const json = await res.json();
      setPosts(json.posts || []);
      
      // Also fetch user settings for daily time (mocking it for now or could add endpoint)
      // For now let's just keep it local state or assume it's set
    } catch (err) {
      console.error("Failed to fetch posts", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      setIsVideo(selectedFile.type.startsWith('video/'));
    }
  };

  const handleSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert("Please select an image or video first.");
      return;
    }
    if (!scheduledAt && !isQueued) {
      alert("Please select a date or add to queue.");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('caption', caption);
    
    if (scheduledAt) {
      formData.append('scheduled_at', scheduledAt.replace('T', ' ') + ':00');
    } else {
      formData.append('scheduled_at', '');
    }
    
    formData.append('is_queued', String(isQueued));

    try {
      const res = await fetch('/api/instagram/schedule', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        setIsModalOpen(false);
        setFile(null);
        setPreviewUrl(null);
        setCaption("");
        setScheduledAt("");
        fetchPosts();
      } else {
        const errorData = await res.json();
        console.error("Backend Error:", errorData);
        const detail = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        alert(`Scheduling failed: ${detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Scheduling failed", err);
      alert("Network error occurred during scheduling.");
    } finally {
      setUploading(false);
    }
  };

  const handlePostNow = async () => {
    if (!file) {
      alert("Please select an image or video first.");
      return;
    }
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('caption', caption);

    try {
      const res = await fetch('/api/instagram/publish-now', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        alert("Published successfully!");
        setIsModalOpen(false);
        setFile(null);
        setPreviewUrl(null);
        setCaption("");
        fetchPosts();
      } else {
        const errorData = await res.json();
        console.error("Post Now failed:", errorData);
        const detail = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : JSON.stringify(errorData.detail);
        alert(`Posting failed: ${detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Posting failed", err);
      alert("Network error occurred during posting.");
    } finally {
      setUploading(false);
    }
  };

  const deletePost = async (id: number) => {
    try {
      const res = await fetch(`/api/instagram/scheduled-posts/${id}`, { method: 'DELETE' });
      if (res.ok) fetchPosts();
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Post Scheduler</h2>
          <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">Manage your Instagram content pipeline</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-6 py-3 bg-brand-ig text-white rounded-2xl font-black text-sm shadow-xl shadow-brand-ig/20 hover:scale-105 transition-transform"
        >
          <Plus className="w-5 h-5" />
          CREATE NEW POST
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Scheduled List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-card p-6">
            <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest mb-6 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Upcoming & Recent Posts
            </h3>
            
            {loading ? (
              <div className="py-20 flex justify-center">
                <RefreshCw className="w-8 h-8 text-slate-300 animate-spin" />
              </div>
            ) : posts.length === 0 ? (
              <div className="py-20 text-center border-2 border-dashed border-slate-900/5 dark:border-white/5 rounded-3xl">
                <ImageIcon className="w-12 h-12 text-slate-200 mx-auto mb-4" />
                <p className="text-slate-400 font-bold">No posts scheduled yet.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {posts.map((post) => (
                  <div key={post.id} className="flex gap-4 p-4 bg-slate-900/5 dark:bg-white/5 rounded-2xl border border-white/5 group hover:border-brand-ig/30 transition-all">
                    <img src={post.media_url} alt="Post" className="w-20 h-20 rounded-xl object-cover" />
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start">
                        <span className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter ${
                          post.status === 'published' ? 'bg-emerald-500/10 text-emerald-400' :
                          post.status === 'failed' ? 'bg-rose-500/10 text-rose-400' :
                          'bg-amber-500/10 text-amber-400'
                        }`}>
                          {post.status}
                        </span>
                        <div className="flex items-center gap-2">
                           <span className="text-[10px] font-bold text-slate-500 flex items-center gap-1">
                             <Calendar className="w-3 h-3" />
                             {post.scheduled_at}
                           </span>
                           <button onClick={() => deletePost(post.id)} className="text-slate-500 hover:text-rose-400 transition-colors p-1">
                             <Trash2 className="w-4 h-4" />
                           </button>
                        </div>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-300 mt-2 line-clamp-2">{post.caption}</p>
                      {post.error_message && (
                        <p className="text-[10px] text-rose-400 font-bold mt-1 uppercase tracking-tighter">Error: {post.error_message}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Stats / Queue Side */}
        <div className="space-y-6">
           <div className="glass-card p-6 bg-gradient-to-br from-brand-ig/10 to-transparent">
              <h3 className="text-sm font-black text-brand-ig uppercase tracking-widest mb-4">Daily Queue Settings</h3>
              <p className="text-xs text-slate-500 mb-6 font-bold leading-relaxed">
                Add posts to your queue and we'll automatically publish one every day at your preferred time.
              </p>
              <div className="space-y-4">
                <label className="block">
                  <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Global Posting Time</span>
                  <input 
                    type="time" 
                    value={dailyPostTime}
                    onChange={(e) => setDailyPostTime(e.target.value)}
                    onBlur={async () => {
                      await fetch('/api/settings/instagram', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ daily_post_time: dailyPostTime })
                      });
                    }}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm font-black text-white outline-none focus:ring-2 ring-brand-ig/20"
                  />
                </label>
                <div className="p-4 bg-white/5 rounded-2xl border border-white/5 text-center">
                  <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Queue Status</span>
                  <p className="text-xl font-black text-emerald-400 mt-1">Active</p>
                </div>
              </div>
           </div>
        </div>
      </div>

      {/* Post Creation Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsModalOpen(false)}
              className="absolute inset-0 bg-[#0B0E14]/80 backdrop-blur-md"
            />
            <motion.div 
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="relative w-full max-w-2xl bg-white dark:bg-[#161B22] rounded-[32px] overflow-hidden shadow-2xl border border-white/10"
            >
              <div className="p-8">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">Create Instagram Post</h3>
                  <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-slate-100 dark:hover:bg-white/5 rounded-full transition-colors">
                    <X className="w-6 h-6" />
                  </button>
                </div>

                <form onSubmit={handleSchedule} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Media Upload */}
                    <div className="space-y-4">
                      <label className="block">
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Media (Image/Video)</span>
                        <div className="relative group cursor-pointer h-64 border-2 border-dashed border-slate-900/5 dark:border-white/10 rounded-3xl overflow-hidden hover:border-brand-ig/50 transition-colors">
                          <input type="file" onChange={handleFileChange} className="absolute inset-0 opacity-0 cursor-pointer z-10" />
                          {previewUrl ? (
                            isVideo ? (
                              <video src={previewUrl} className="w-full h-full object-cover" controls />
                            ) : (
                              <img src={previewUrl} className="w-full h-full object-cover" />
                            )
                          ) : (
                            <div className="h-full flex flex-col items-center justify-center gap-3 text-slate-400">
                              <Plus className="w-8 h-8" />
                              <span className="text-xs font-bold uppercase tracking-widest">Select Media</span>
                            </div>
                          )}
                        </div>
                      </label>
                    </div>

                    {/* Meta Data */}
                    <div className="space-y-4">
                      <label className="block">
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Caption</span>
                        <textarea 
                          className="w-full h-32 bg-slate-100 dark:bg-white/5 border border-slate-900/5 dark:border-white/10 rounded-2xl p-4 text-sm focus:ring-2 ring-brand-ig/20 transition-all resize-none outline-none"
                          placeholder="Write something engaging..."
                          value={caption}
                          onChange={(e) => setCaption(e.target.value)}
                        />
                      </label>

                      <label className="block">
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2 block">Schedule Time</span>
                        <div className="space-y-4">
                          <input 
                            type="datetime-local" 
                            disabled={isQueued}
                            className="w-full bg-slate-100 dark:bg-white/5 border border-slate-900/5 dark:border-white/10 rounded-2xl p-4 text-sm focus:ring-2 ring-brand-ig/20 transition-all outline-none disabled:opacity-30"
                            value={scheduledAt}
                            onChange={(e) => setScheduledAt(e.target.value)}
                          />
                          <div 
                            onClick={() => setIsQueued(!isQueued)}
                            className={`flex items-center gap-3 p-4 rounded-2xl border cursor-pointer transition-all ${
                              isQueued ? 'bg-brand-ig/10 border-brand-ig' : 'bg-slate-100 dark:bg-white/5 border-transparent'
                            }`}
                          >
                            <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-colors ${
                              isQueued ? 'bg-brand-ig border-brand-ig' : 'border-slate-400'
                            }`}>
                              {isQueued && <CheckCircle2 className="w-4 h-4 text-white" />}
                            </div>
                            <div>
                               <p className="text-xs font-black text-slate-900 dark:text-white uppercase tracking-tight">Add to Daily Queue</p>
                               <p className="text-[10px] text-slate-500 font-bold">Auto-posts at {dailyPostTime}</p>
                            </div>
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>

                  <div className="flex gap-4 pt-4 border-t border-slate-900/5 dark:border-white/5">
                    <button 
                      type="button"
                      onClick={handlePostNow}
                      disabled={uploading || !file}
                      className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 text-slate-900 dark:text-white rounded-2xl font-black text-sm transition-all disabled:opacity-50"
                    >
                      <Send className="w-5 h-5" />
                      POST NOW
                    </button>
                    <button 
                      type="submit"
                      disabled={uploading || !file || (!scheduledAt && !isQueued)}
                      className="flex-[2] flex items-center justify-center gap-2 px-6 py-4 bg-brand-ig text-white rounded-2xl font-black text-sm shadow-xl shadow-brand-ig/20 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50"
                    >
                      {uploading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Calendar className="w-5 h-5" />}
                      {uploading ? "SCHEDULING..." : "SCHEDULE POST"}
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
