-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- RUNS Table
CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword TEXT NOT NULL,
    hl TEXT DEFAULT 'id',
    gl TEXT DEFAULT 'ID',
    status TEXT DEFAULT 'queued', -- queued, running, success, partial, failed
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    error_message TEXT
);

-- VIDEOS Table
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL, -- search, people_also_watched, related_fallback
    rank INTEGER NOT NULL,
    title TEXT NOT NULL,
    channel_name TEXT,
    video_id TEXT NOT NULL,
    video_url TEXT NOT NULL,
    views_raw TEXT,
    views_num BIGINT,
    published_raw TEXT,
    duration_raw TEXT,
    collected_from TEXT, -- search, module, watch_page
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TEMPLATES Table
CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    template_text TEXT NOT NULL,
    example_1 TEXT,
    example_2 TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create simple indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_runs_keyword_status ON runs(keyword, status);
CREATE INDEX IF NOT EXISTS idx_videos_run_id ON videos(run_id);
CREATE INDEX IF NOT EXISTS idx_templates_run_id ON templates(run_id);
