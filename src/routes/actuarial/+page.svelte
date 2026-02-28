<script lang="ts">
    import { onMount } from "svelte";
    import NewsPanel from "$lib/components/panels/NewsPanel.svelte";
    import SituationPanel from "$lib/components/panels/SituationPanel.svelte";

    // Live Feed State
    let liveNews = $state<any>({
        mhit: [],
        property_casualty: [],
        life_pension: [],
        raw: [],
    });
    let liveNewsLoading = $state(true);

    onMount(async () => {
        try {
            const res = await fetch("/api/news/actuarial");
            if (res.ok) {
                const data = await res.json();
                liveNews = data.news;
            }
        } catch (e) {
            console.error("Failed to load actuarial feed", e);
        } finally {
            liveNewsLoading = false;
        }
    });
</script>

<svelte:head>
    <title>Actuarial Monitor | Risk & Liability Feed</title>
</svelte:head>

<div
    class="min-h-screen bg-neutral-900 text-neutral-100 font-sans tracking-wide"
>
    <!-- Navbar / Market Bar -->
    <header
        class="border-b border-emerald-900/50 bg-neutral-950 sticky top-0 z-50"
    >
        <div
            class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-14"
        >
            <div class="flex items-center gap-4">
                <a href="/" class="text-neutral-500 hover:text-white transition"
                    >← Main Dashboard</a
                >
                <div class="w-px h-6 bg-neutral-800"></div>
                <div class="font-bold text-xl tracking-tighter text-white">
                    ActuarialMonitor<span class="text-emerald-500">.</span>
                </div>
            </div>

            <div class="flex items-center gap-2">
                <div
                    class="px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded text-[10px] font-bold uppercase tracking-wider"
                >
                    Risk Assessment Live Mode
                </div>
            </div>
        </div>
    </header>

    <main class="w-full px-2 py-4 sm:px-4 sm:py-6 max-w-[2000px] mx-auto">
        <div class="mb-6">
            <h1 class="text-2xl font-bold text-white mb-2">
                Live Underwriting Factors Monitor
            </h1>
            <p class="text-sm text-neutral-400 max-w-2xl">
                This specialized dashboard filters the global information stream
                specifically for actuarial risk variables: MHIT (Medical/Health
                Insurance), P&C (Property & Casualty), and Life/Pension
                liabilities.
            </p>
        </div>

        <!-- Masonry Grid Layout -->
        <div
            class="columns-1 md:columns-2 lg:columns-3 xl:columns-4 gap-4 space-y-4"
        >
            <!-- 1. Situation Panels (Specific Risk Monitors) -->
            <div class="break-inside-avoid">
                <SituationPanel
                    title="Extreme Weather & Cat Bonds"
                    subtitle="Monitoring property damage risk"
                    keywords={[
                        "hurricane",
                        "wildfire",
                        "flood",
                        "disaster",
                        "climate risk",
                    ]}
                    newsItems={[...liveNews.property_casualty, ...liveNews.raw]}
                />
            </div>

            <div class="break-inside-avoid">
                <SituationPanel
                    title="Healthcare Policy Shift"
                    subtitle="Medicare & Billing Regulation"
                    keywords={[
                        "medicare",
                        "billing",
                        "hospital",
                        "regulation",
                        "fda",
                    ]}
                    newsItems={[...liveNews.mhit, ...liveNews.raw]}
                />
            </div>

            <!-- 2. Category News Panels (Live Stream) -->
            <div class="break-inside-avoid">
                <!-- Inline custom style for emerald to differentiate from main dashboard -->
                <NewsPanel
                    category="gov"
                    title="MHIT / Medical Cost Trends"
                    newsItems={liveNews.mhit}
                    loading={liveNewsLoading}
                />
            </div>

            <div class="break-inside-avoid">
                <NewsPanel
                    category="tech"
                    title="Property & Casualty"
                    newsItems={liveNews.property_casualty}
                    loading={liveNewsLoading}
                />
            </div>

            <div class="break-inside-avoid">
                <NewsPanel
                    category="finance"
                    title="Life & Pension Risk"
                    newsItems={liveNews.life_pension}
                    loading={liveNewsLoading}
                />
            </div>

            <div class="break-inside-avoid">
                <NewsPanel
                    category="intel"
                    title="Raw Actuarial Intel"
                    newsItems={liveNews.raw}
                    loading={liveNewsLoading}
                />
            </div>
        </div>
    </main>
</div>
