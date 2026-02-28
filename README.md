# Situation Monitor

A "Situation + Market Impact Alert" website designed for high-signal geopolitical and macro monitoring. The site aggregates breaking news from GDELT and RSS feeds, clusters them into actionable events, maps them to impacted sectors and tickers, and emails subscribers when severity thresholds are met.

## Tech Stack
* SvelteKit (TypeScript) + TailwindCSS
* Supabase Postgres (Storage & Pub/Sub)
* Resend (Email Delivery)
* Finnhub & CoinGecko (Market Data)
* GDELT (News Data)
* Vercel Cron (Automated checks)

## Project Setup Local Instructions

### 1. Install Dependencies
\`\`\`bash
npm install
\`\`\`

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in the values:
* `PUBLIC_SUPABASE_URL`: Your Supabase Project URL
* `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase Service Role Key (Keep this secret!)
* `RESEND_API_KEY`: Your Resend API token
* `FINNHUB_API_KEY`: (Optional) Free API key from finnhub.io
* `LLM_API_KEY`: (Optional) API key for summarization capabilities (if using an LLM API)
* `CRON_SECRET`: Secret to secure your webhook endpoint

### 3. Setup Database (Supabase)
Navigate to your Supabase SQL Editor and execute the contents of `supabase/migrations/0001_initial_schema.sql`.

### 4. Run Development Server
\`\`\`bash
npm run dev
\`\`\`
Visit `http://localhost:5173`.

## Triggering the Alert Cron Job Locally

The core engine is driven by a scheduled cron job hitting `/api/alerts/run`.

To test it manually locally (assuming CRON_SECRET is commented out or matched):
\`\`\`bash
curl -X POST http://localhost:5173/api/alerts/run -H "Authorization: Bearer dev-cron-secret"
\`\`\`

## Notes on Architecture
This codebase uses a resilient fetching layer (`src/lib/services/fetch.ts`) to manage network hiccups with upstream data providers like GDELT and Finnhub. Topic and entity extraction leverages internal config files (`topics.ts`), and deduplication logic resides in the cron endpoint (`alerts/run/+server.ts`).
