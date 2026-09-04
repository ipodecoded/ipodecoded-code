-- ====================================================================
-- IPODecoded - Optional Supabase pg_cron & Edge Function Setup
-- ====================================================================
-- If you have pg_cron enabled on your Supabase PostgreSQL instance,
-- you can trigger an Edge Function or external webhook directly from PostgreSQL!

-- 1. Enable pg_cron and pg_net extensions
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- 2. Schedule a cron job to call the ingestion webhook every 2 hours
-- Replace with your deployed backend URL or Supabase Edge Function URL:
/*
SELECT cron.schedule(
    'invoke-ipodecoded-pipeline',
    '0 * /2 * * *', -- Every 2 hours
    $$
    SELECT net.http_post(
        url := 'https://api.ipodecoded.journaldecoded.in/api/pipeline/run',
        headers := '{"Content-Type": "application/json"}'::jsonb
    );
    $$
);
*/

-- To view active scheduled jobs:
-- SELECT * FROM cron.job;

-- To unschedule a job:
-- SELECT cron.unschedule('invoke-ipodecoded-pipeline');
