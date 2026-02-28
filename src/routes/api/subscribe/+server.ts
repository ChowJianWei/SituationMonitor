import { json } from '@sveltejs/kit';
import { supabaseAdmin } from '$lib/server/supabase';
import { sendConfirmationEmail } from '$lib/server/email';

const ipCache = new Map<string, { count: number, resetAt: number }>();

// Simple email validation
function isValidEmail(email: string) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function generateToken() {
    return crypto.randomUUID();
}

export async function POST({ request, url, getClientAddress }) {
    try {
        const ip = getClientAddress();
        const now = Date.now();
        const record = ipCache.get(ip) || { count: 0, resetAt: now + 60000 };

        if (now > record.resetAt) {
            record.count = 0;
            record.resetAt = now + 60000;
        }

        record.count += 1;
        ipCache.set(ip, record);

        if (record.count > 5) {
            return json({ error: 'Too many requests. Try again later.' }, { status: 429 });
        }

        const body = await request.json();
        const { email } = body;

        if (!email || !isValidEmail(email)) {
            return json({ error: 'Valid email is required.' }, { status: 400 });
        }

        // Check if subscriber exists
        const { data: existing, error: fetchErr } = await supabaseAdmin
            .from('subscribers')
            .select('id, status')
            .eq('email', email)
            .maybeSingle();

        if (fetchErr) {
            console.error('Supabase fetch error:', fetchErr);
            return json({ error: 'Database error.' }, { status: 500 });
        }

        if (existing) {
            if (existing.status === 'confirmed') {
                return json({ message: 'You are already subscribed!' });
            } else if (existing.status === 'pending') {
                return json({ message: 'Please check your email to confirm your subscription.' });
            } else if (existing.status === 'unsubscribed') {
                // Re-subscribe them
                const confirm_token = generateToken();
                const unsub_token = generateToken();
                await supabaseAdmin
                    .from('subscribers')
                    .update({ status: 'pending', confirm_token, unsub_token })
                    .eq('id', existing.id);

                await sendConfirmationEmail(email, confirm_token, url.origin);
                return json({ message: 'Welcome back! Please check your email to confirm.' });
            }
        }

        // New subscriber
        const confirm_token = generateToken();
        const unsub_token = generateToken();

        const { error: insertErr } = await supabaseAdmin
            .from('subscribers')
            .insert({ email, status: 'pending', confirm_token, unsub_token });

        if (insertErr) {
            console.error('Supabase insert error:', insertErr);
            return json({ error: 'Could not subscribe at this time.' }, { status: 500 });
        }

        await sendConfirmationEmail(email, confirm_token, url.origin);

        return json({ message: 'Success! Please check your email to confirm.' });

    } catch (e) {
        console.error('API Error:', e);
        return json({ error: 'Server error occurred.' }, { status: 500 });
    }
}
