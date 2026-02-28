<script lang="ts">
    import { onMount } from "svelte";
    import NewsPanel from "$lib/components/panels/NewsPanel.svelte";
    import SituationPanel from "$lib/components/panels/SituationPanel.svelte";
    import EconomicMatrix from "$lib/components/actuarial/EconomicMatrix.svelte";
    import CatastropheMatrix from "$lib/components/actuarial/CatastropheMatrix.svelte";
    import RiskHeatmap from "$lib/components/actuarial/RiskHeatmap.svelte";

    // Live Feed State
    let liveNews = $state<any>({
        mhit: [],
        property_casualty: [],
        life_pension: [],
        auto: [],
        cyber: [],
        raw: [],
    });
    let liveNewsLoading = $state(true);

    // Tab State
    type Tab =
        | "Overview"
        | "Life & Health"
        | "Property & Casualty"
        | "Cyber & Specialty";
    let activeTab = $state<Tab>("Overview");

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
    <title>Actuarial Intelligence Center | Situation Monitor</title>
</svelte:head>

<div
    class="min-h-screen bg-neutral-900 text-neutral-100 font-sans tracking-wide pb-12"
>
    <!-- Navbar / Market Bar -->
    <header
        class="border-b border-purple-900/50 bg-neutral-950 sticky top-0 z-50"
    >
        <div
            class="max-w-[2000px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-14"
        >
            <div class="flex items-center gap-4">
                <a href="/" class="text-neutral-500 hover:text-white transition"
                    >← Main Dashboard</a
                >
                <div class="w-px h-6 bg-neutral-800"></div>
                <div class="font-bold text-xl tracking-tighter text-white">
                    ActuarialIntelligence<span class="text-purple-500">.</span>
                </div>
            </div>

            <div class="flex items-center gap-2">
                <div
                    class="px-2 py-1 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded text-[10px] font-bold uppercase tracking-wider animate-pulse"
                >
                    Live Telemetry
                </div>
            </div>
        </div>
    </header>

    <main class="w-full px-4 py-8 max-w-[2000px] mx-auto">
        <div
            class="mb-8 border-b border-neutral-800 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6"
        >
            <div>
                <h1
                    class="text-3xl font-extrabold text-white mb-2 leading-tight"
                >
                    Advanced Underwriting Matrix
                </h1>
                <p class="text-sm text-neutral-400 max-w-2xl leading-relaxed">
                    Cross-referencing global macro events, weather anomalies,
                    and economic yield data against specific insurance lines of
                    business. Select a domain below to filter the signal.
                </p>
            </div>

            <!-- Tabs -->
            <div
                class="flex p-1 bg-neutral-950 border border-neutral-800 rounded-lg overflow-x-auto no-scrollbar max-w-full"
            >
                {#each ["Overview", "Life & Health", "Property & Casualty", "Cyber & Specialty"] as tab}
                    <button
                        class="px-4 py-2 text-sm font-semibold rounded-md transition whitespace-nowrap {activeTab ===
                        tab
                            ? 'bg-purple-600 text-white shadow'
                            : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900'}"
                        onclick={() => (activeTab = tab as Tab)}
                    >
                        {tab}
                    </button>
                {/each}
            </div>
        </div>

        <!-- Render Content based on active tab using Masonry columns -->
        <div
            class="columns-1 md:columns-2 lg:columns-3 xl:columns-4 gap-5 space-y-5"
        >
            {#if activeTab === "Overview"}
                <!-- OVERVIEW TAB -->
                <div class="break-inside-avoid">
                    <RiskHeatmap />
                </div>

                <div class="break-inside-avoid">
                    <SituationPanel
                        title="Global Catastrophe Risk"
                        subtitle="Hurricane & Wildfire escalation"
                        keywords={[
                            "hurricane",
                            "wildfire",
                            "flood",
                            "disaster",
                            "climate risk",
                        ]}
                        newsItems={[
                            ...liveNews.property_casualty,
                            ...liveNews.auto,
                        ]}
                    />
                </div>

                <div class="break-inside-avoid">
                    <SituationPanel
                        title="Healthcare Policy Shift"
                        subtitle="Medicare & Liability Regulation"
                        keywords={[
                            "medicare",
                            "billing",
                            "hospital",
                            "regulation",
                            "fda",
                        ]}
                        newsItems={[...liveNews.mhit, ...liveNews.life_pension]}
                    />
                </div>

                <div class="break-inside-avoid">
                    <NewsPanel
                        category="intel"
                        title="Systemic Risk Intel"
                        newsItems={liveNews.raw}
                        loading={liveNewsLoading}
                    />
                </div>
            {:else if activeTab === "Life & Health"}
                <!-- LIFE & HEALTH TAB -->
                <div class="break-inside-avoid">
                    <EconomicMatrix />
                </div>

                <div class="break-inside-avoid">
                    <NewsPanel
                        category="gov"
                        title="MHIT & Medical Costs"
                        newsItems={liveNews.mhit}
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
                    <!-- Generic News for extra volume if needed -->
                    <NewsPanel
                        category="intel"
                        title="General Healthcare Trends"
                        newsItems={liveNews.raw.filter((i: any) =>
                            i.title.toLowerCase().includes("health"),
                        )}
                        loading={liveNewsLoading}
                    />
                </div>
            {:else if activeTab === "Property & Casualty"}
                <!-- P&C TAB -->
                <div class="break-inside-avoid">
                    <CatastropheMatrix />
                </div>

                <div class="break-inside-avoid">
                    <NewsPanel
                        category="tech"
                        title="Property & Climate Risk"
                        newsItems={liveNews.property_casualty}
                        loading={liveNewsLoading}
                    />
                </div>

                <div class="break-inside-avoid">
                    <NewsPanel
                        category="politics"
                        title="Auto & Transport Liability"
                        newsItems={liveNews.auto}
                        loading={liveNewsLoading}
                    />
                </div>
            {:else if activeTab === "Cyber & Specialty"}
                <!-- CYBER & SPECIALTY TAB -->
                <div class="break-inside-avoid">
                    <!-- Put heatmap here as well since it's relevant to specialty lines mixing -->
                    <RiskHeatmap />
                </div>

                <div class="break-inside-avoid">
                    <NewsPanel
                        category="ai"
                        title="Cyber Security & Ransomware"
                        newsItems={liveNews.cyber}
                        loading={liveNewsLoading}
                    />
                </div>

                <div class="break-inside-avoid">
                    <SituationPanel
                        title="D&O / Executive Liability"
                        subtitle="Corporate litigation & SEC probes"
                        keywords={[
                            "sec",
                            "litigation",
                            "fraud",
                            "lawsuit",
                            "class action",
                            "scandal",
                        ]}
                        newsItems={liveNews.raw}
                    />
                </div>
            {/if}
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
