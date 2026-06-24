/**
 * Server-side proxy to the Python actuarial-quant backend (FastAPI).
 *
 * The Python engine runs as its own 24/7 service (it can't live on Vercel
 * serverless — native numpy/scipy + background loops). The browser never talks
 * to it directly; it calls these same-origin routes, which forward to the
 * backend. This avoids CORS and keeps the backend URL server-side.
 *
 * Set ACTUARIAL_API_URL to the deployed engine in production (e.g. Railway).
 */

const BASE = process.env.ACTUARIAL_API_URL ?? 'http://localhost:8200';

async function proxy(
    method: 'GET' | 'POST',
    path: string,
    search: string,
    request: Request | null
): Promise<Response> {
    const target = `${BASE}/api/v1/${path}${search}`;
    try {
        const init: RequestInit = {
            method,
            headers: { 'content-type': 'application/json' },
            signal: AbortSignal.timeout(45_000) // cycles run several model fits
        };
        if (method === 'POST' && request) {
            const body = await request.text();
            if (body) init.body = body;
        }
        const res = await fetch(target, init);
        const text = await res.text();
        return new Response(text, {
            status: res.status,
            headers: { 'content-type': 'application/json' }
        });
    } catch (e) {
        // Fail soft so the page can render an "engine offline" state.
        return new Response(
            JSON.stringify({ error: 'actuarial_engine_unreachable', detail: String(e) }),
            { status: 503, headers: { 'content-type': 'application/json' } }
        );
    }
}

export async function GET({ params, url }) {
    return proxy('GET', params.path, url.search, null);
}

export async function POST({ params, url, request }) {
    return proxy('POST', params.path, url.search, request);
}
