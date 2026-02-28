-- Migration: 0001_initial_schema.sql
-- Description: Creates the baseline tables for the Situation Monitor app.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- SUBSCRIBERS
CREATE TABLE public.subscribers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'confirmed', 'unsubscribed'
    confirm_token TEXT,
    unsub_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed_at TIMESTAMP WITH TIME ZONE
);

-- EVENTS
CREATE TABLE public.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    summary JSONB, -- what_happened (bullets), why_it_matters (bullets)
    severity INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- EVENT_SOURCES (Articles that triggered the event)
CREATE TABLE public.event_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES public.events(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    published_at TIMESTAMP WITH TIME ZONE
);

-- EVENT_IMPACTS (Affected markets)
CREATE TABLE public.event_impacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES public.events(id) ON DELETE CASCADE,
    sectors TEXT[],
    tickers TEXT[],
    confidence TEXT,
    rationale TEXT,
    market_snapshot JSONB -- stores indices/ETF prices at the time
);

-- EMAIL_LOGS
CREATE TABLE public.email_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES public.events(id) ON DELETE CASCADE,
    subscriber_id UUID REFERENCES public.subscribers(id) ON DELETE CASCADE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT, -- 'sent', 'failed'
    provider_id TEXT
);

-- Row Level Security (RLS) basics (assuming mostly Service Role usage for the cron jobs)
ALTER TABLE public.subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_impacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_logs ENABLE ROW LEVEL SECURITY;

-- Allow public inserts for subscribing (status 'pending')
CREATE POLICY "Allow public insert to subscribers" ON public.subscribers FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public read own subscriber" ON public.subscribers FOR SELECT USING (true); -- Filtered in application by token

-- Rest are purely service-role operated, so they don't need public policies. Service role bypasses RLS.
