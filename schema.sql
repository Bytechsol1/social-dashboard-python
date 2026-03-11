-- Social Intelligence Dashboard - PostgreSQL Schema (Supabase/Neon Compatible)

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    yt_refresh_token TEXT,
    manychat_key TEXT,
    youtube_channel_id TEXT,
    ig_access_token TEXT,
    ig_user_id TEXT,
    ig_audience_json TEXT, -- Migration column added
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    date TEXT,
    source TEXT,
    metric_name TEXT,
    dimension TEXT DEFAULT 'none',
    value REAL,
    UNIQUE(user_id, date, source, metric_name, dimension)
);

-- 3. ManyChat Interactions
CREATE TABLE IF NOT EXISTS manychat_interactions (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    subscriber_id TEXT,
    type TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Sync Logs
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    status TEXT,
    message TEXT,
    flow_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. ManyChat Automations
CREATE TABLE IF NOT EXISTS manychat_automations (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    name TEXT,
    status TEXT,
    runs INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    last_modified TEXT,
    synced_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. ManyChat Pings
CREATE TABLE IF NOT EXISTS manychat_pings (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    automation_id TEXT,
    type TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. YouTube Videos
CREATE TABLE IF NOT EXISTS youtube_videos (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    published_at TEXT,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    thumbnail_url TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Instagram Media
CREATE TABLE IF NOT EXISTS instagram_media (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    caption TEXT,
    media_type TEXT,
    media_url TEXT,
    permalink TEXT,
    timestamp TIMESTAMP,
    like_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
