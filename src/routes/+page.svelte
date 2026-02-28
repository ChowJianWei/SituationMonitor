<script lang="ts">
    import { enhance } from "$app/forms";
    import { fade } from "svelte/transition";
    import { onMount } from "svelte";
    import NewsPanel from "$lib/components/panels/NewsPanel.svelte";
    import SituationPanel from "$lib/components/panels/SituationPanel.svelte";
    import MapPanel from "$lib/components/panels/MapPanel.svelte";
    import PolymarketPanel from "$lib/components/panels/PolymarketPanel.svelte";
    import WhalePanel from "$lib/components/panels/WhalePanel.svelte";

    let { data } = $props();
    let events = $derived(data.events);
    let marketSnapshot = $derived(data.marketSnapshot);

    let subEmail = $state("");
    let subStatus = $state<"idle" | "loading" | "success" | "error">("idle");
    let subMessage = $state("");

    // Live Feed State
    let liveNews = $state<any>({
        politics: [],
        tech: [],
        finance: [],
        gov: [],
        ai: [],
        raw: [],
    });
    let liveNewsLoading = $state(true);

    onMount(async () => {
        try {
            const res = await fetch("/api/news/live");
            if (res.ok) {
                const data = await res.json();
                liveNews = data.news;
            }
        } catch (e) {
            console.error("Failed to load live feed", e);
        } finally {
            liveNewsLoading = false;
        }
    });

    async function handleSubscribe(e: Event) {
        e.preventDefault();
        subStatus = "loading";
        try {
            const res = await fetch("/api/subscribe", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: subEmail }),
            });
            const result = await res.json();
            if (res.ok) {
                subStatus = "success";
                subMessage = result.message;
                subEmail = "";
            } else {
                subStatus = "error";
                subMessage = result.error || "Failed to subscribe.";
            }
        } catch (err) {
            subStatus = "error";
            subMessage = "Network error occurred.";
        }
    }
</script>

<svelte:head>
    <title>Situation Monitor | Market impact alerts</title>
</svelte:head>

<div
    class="min-h-screen bg-neutral-900 text-neutral-100 font-sans tracking-wide"
>
    <!-- Navbar / Market Bar -->
    <header
        class="border-b border-neutral-800 bg-neutral-950 sticky top-0 z-50"
    >
        <div
            class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-14"
        >
            <div class="font-bold text-xl tracking-tighter text-white">
                SituationMonitor<span class="text-blue-500">.</span>
            </div>
            <div class="flex space-x-6 text-sm overflow-x-auto no-scrollbar">
                {#each Object.entries(marketSnapshot) as [ticker, md]}
                    <div class="flex items-center space-x-2 whitespace-nowrap">
                        <span class="font-mono text-neutral-400">{ticker}</span>
                        <span
                            class="font-mono {md.changePercent >= 0
                                ? 'text-green-400'
                                : 'text-red-400'}"
                        >
                            {md.changePercent > 0
                                ? "+"
                                : ""}{md.changePercent?.toFixed(2)}%
                        </span>
                    </div>
                {/each}
            </div>
        </div>
    </header>

    <main class="w-full px-2 py-4 sm:px-4 sm:py-6 max-w-[2000px] mx-auto">
        <!-- Global Map -->
        <div class="mb-4 break-inside-avoid">
            <MapPanel />
        </div>

        <!-- Masonry Grid Layout -->
        <div
            class="columns-1 md:columns-2 lg:columns-3 xl:columns-4 2xl:columns-5 gap-4 space-y-4"
        >
            <!-- 1. Subscription Widget -->
            <div class="break-inside-avoid">
                <div
                    class="p-6 rounded-xl bg-gradient-to-b from-blue-900/40 to-neutral-900 border border-blue-900/50 shadow-lg relative overflow-hidden"
                >
                    <div
                        class="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-neutral-900/0 to-transparent"
                    ></div>
                    <div class="relative z-10">
                        <h3
                            class="text-xl font-bold mb-2 flex items-center gap-2"
                        >
                            <div
                                class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"
                            ></div>
                            High-Signal Alerts
                        </h3>
                        <p
                            class="text-xs text-neutral-400 mb-5 leading-relaxed"
                        >
                            Geopolitics and macro alerts delivered when
                            thresholds are breached. Zero noise.
                        </p>
                        <form onsubmit={handleSubscribe} class="space-y-3">
                            <input
                                type="email"
                                bind:value={subEmail}
                                placeholder="Enter your email"
                                required
                                class="w-full bg-neutral-950/80 border border-neutral-800 rounded-lg px-3 py-2.5 text-sm text-white focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition"
                            />
                            <button
                                type="submit"
                                disabled={subStatus === "loading"}
                                class="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 px-4 rounded-lg transition text-sm flex items-center justify-center disabled:opacity-50"
                            >
                                {#if subStatus === "loading"}
                                    Subscribing...
                                {:else}
                                    Subscribe
                                {/if}
                            </button>
                            {#if subMessage}
                                <p
                                    class="text-xs text-center {subStatus ===
                                    'error'
                                        ? 'text-red-400'
                                        : 'text-green-400'}"
                                >
                                    {subMessage}
                                </p>
                            {/if}
                        </form>
                    </div>
                </div>
            </div>

            <!-- 2. Main Alert Feed (The Supabase data) -->
            <div class="break-inside-avoid">
                <div
                    class="flex flex-col border border-neutral-800 bg-neutral-900/80 rounded-xl overflow-hidden shadow-lg h-full max-h-[600px]"
                >
                    <div
                        class="bg-neutral-800/80 px-4 py-3 border-b border-neutral-800 flex items-center justify-between sticky top-0 backdrop-blur-sm z-10"
                    >
                        <h2
                            class="text-sm font-bold text-neutral-100 flex items-center gap-2"
                        >
                            <div
                                class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"
                            ></div>
                            Critical Alerts
                        </h2>
                    </div>
                    <div
                        class="flex-1 overflow-y-auto p-4 space-y-4 no-scrollbar"
                    >
                        {#if events.length === 0}
                            <div
                                class="py-8 text-center text-xs text-neutral-500 border border-neutral-800 border-dashed rounded-lg"
                            >
                                Baseline is quiet.
                            </div>
                        {:else}
                            {#each events as event}
                                <a
                                    href="/events/{event.id}"
                                    class="block group bg-neutral-950/50 p-4 rounded-lg border border-neutral-800/60 hover:border-neutral-700 transition"
                                >
                                    <div
                                        class="flex items-center justify-between mb-2"
                                    >
                                        <span
                                            class="px-2 py-0.5 text-[10px] font-bold rounded bg-red-500/10 text-red-400 border border-red-500/20 uppercase tracking-wider"
                                        >
                                            Sev: {event.severity}
                                        </span>
                                    </div>
                                    <h3
                                        class="text-sm font-bold mb-2 text-neutral-200 group-hover:text-blue-400 transition leading-snug"
                                    >
                                        {event.title}
                                    </h3>
                                    <p
                                        class="text-[11px] text-neutral-400 line-clamp-2 leading-relaxed"
                                    >
                                        {event.summary?.why_it_matters?.[0] ||
                                            "Triggered alert threshold."}
                                    </p>
                                </a>
                            {/each}
                        {/if}
                    </div>
                </div>
            </div>

            <!-- 3. Situation Panels (Specific Monitors) -->
            <div class="break-inside-avoid">
                <SituationPanel
                    title="Taiwan Strait Watch"
                    subtitle="Monitoring maritime & air activity"
                    keywords={["taiwan", "china", "strait", "pla", "taipei"]}
                    newsItems={liveNews.raw}
                />
            </div>

            <div class="break-inside-avoid">
                <SituationPanel
                    title="Middle East Crisis"
                    subtitle="Regional escalation monitor"
                    keywords={["israel", "iran", "gaza", "lebanon", "strike"]}
                    newsItems={liveNews.raw}
                />
            </div>

            <!-- 4. Market Data Panels -->
            <div class="break-inside-avoid">
                <PolymarketPanel />
            </div>

            <div class="break-inside-avoid">
                <WhalePanel />
            </div>

            <!-- 5. Category News Panels (Live Stream) -->
            <div class="break-inside-avoid">
                <NewsPanel
                    category="politics"
                    title="Geopolitics"
                    newsItems={liveNews.politics}
                    loading={liveNewsLoading}
                />
            </div>

            <div class="break-inside-avoid">
                <NewsPanel
                    category="finance"
                    title="Macro & Markets"
                    newsItems={liveNews.finance}
                    loading={liveNewsLoading}
                />
            </div>

            <div class="break-inside-avoid">
                <NewsPanel
                    category="tech"
                    title="Tech Sector"
                    newsItems={liveNews.tech}
                    loading={liveNewsLoading}
                />
            </div>

            <div class="break-inside-avoid">
                <NewsPanel
                    category="ai"
                    title="AI & Cyber"
                    newsItems={liveNews.ai}
                    loading={liveNewsLoading}
                />
            </div>

            <div class="break-inside-avoid">
                <NewsPanel
                    category="gov"
                    title="Gov & Policy"
                    newsItems={liveNews.gov}
                    loading={liveNewsLoading}
                />
            </div>

            <div class="break-inside-avoid">
                <NewsPanel
                    category="intel"
                    title="Raw Intel Stream"
                    newsItems={liveNews.raw}
                    loading={liveNewsLoading}
                />
            </div>
        </div>
    </main>
</div>

<style>
    /* basic utility */
    .no-scrollbar::-webkit-scrollbar {
        display: none;
    }
    .no-scrollbar {
        -ms-overflow-style: none; /* IE and Edge */
        scrollbar-width: none; /* Firefox */
    }
</style>
