import { createClient } from '@supabase/supabase-js';
import { env } from '$env/dynamic/private';
import { env as publicEnv } from '$env/dynamic/public';

export const supabaseAdmin = createClient(
    publicEnv.PUBLIC_SUPABASE_URL || process.env.PUBLIC_SUPABASE_URL || 'https://todrwvtyhvzzidmcvlgv.supabase.co',
    env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRvZHJ3dHZ5aHZ6aWlkbWN2bGd2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjIyODExMywiZXhwIjoyMDg3ODA0MTEzfQ.FxipatPBOkYX_ZColWSaTUOcKkeSC27BXRkDxwniuD4',
    {
        auth: {
            autoRefreshToken: false,
            persistSession: false
        }
    }
);
