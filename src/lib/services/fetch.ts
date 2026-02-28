// A simple resilient fetch service with rudimentary cache, retries, and circuit breaker concepts.

interface FetchOptions extends RequestInit {
    retries?: number;
    retryDelayMs?: number;
    timeoutMs?: number;
}

const cache = new Map<string, { data: any, expiry: number }>();

export async function resilientFetch(url: string, options: FetchOptions = {}, useCache: boolean = true, cacheTtlMs: number = 60000): Promise<any> {
    if (useCache && cache.has(url)) {
        const cached = cache.get(url)!;
        if (Date.now() < cached.expiry) {
            return cached.data;
        }
        cache.delete(url);
    }

    let retries = options.retries ?? 3;
    let delay = options.retryDelayMs ?? 1000;

    while (retries > 0) {
        try {
            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), options.timeoutMs ?? 10000);

            const response = await fetch(url, { ...options, signal: controller.signal });
            clearTimeout(id);

            if (!response.ok) {
                // If it's a 429 or 5xx, we might want to retry
                if (response.status === 429 || response.status >= 500) {
                    throw new Error(`HTTP Error: ${response.status}`);
                }
                // For 4xx (client errors), fail fast
                const errData = await response.text();
                throw new Error(`HTTP Error ${response.status}: ${errData}`);
            }

            const isJson = response.headers.get('content-type')?.includes('application/json');
            const data = isJson ? await response.json() : await response.text();

            if (useCache) {
                cache.set(url, { data, expiry: Date.now() + cacheTtlMs });
            }

            return data;

        } catch (error) {
            retries -= 1;
            if (retries === 0) throw error;
            // Exponential backoff
            await new Promise((resolve) => setTimeout(resolve, delay));
            delay *= 2;
        }
    }
}
