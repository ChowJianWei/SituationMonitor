<script lang="ts">
    import { enhance } from "$app/forms";
    import { fade } from "svelte/transition";

    let { data } = $props();
    let events = $derived(data.events);
    let marketSnapshot = $derived(data.marketSnapshot);

    let subEmail = $state("");
    let subStatus = $state<"idle" | "loading" | "success" | "error">("idle");
    let subMessage = $state("");

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

    <main
        class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 grid grid-cols-1 lg:grid-cols-3 gap-12"
    >
        <!-- Feed Section -->
        <div class="col-span-1 lg:col-span-2 space-y-8">
            <div
                class="flex items-center justify-between border-b border-neutral-800 pb-4"
            >
                <h2 class="text-2xl font-semibold">Latest Situations</h2>
                <div
                    class="flex items-center space-x-2 text-sm text-neutral-400"
                >
                    <span class="relative flex h-3 w-3">
                        <span
                            class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"
                        ></span>
                        <span
                            class="relative inline-flex rounded-full h-3 w-3 bg-blue-500"
                        ></span>
                    </span>
                    <span>Live Monitoring</span>
                </div>
            </div>

            {#if events.length === 0}
                <div
                    class="py-12 text-center text-neutral-500 border border-neutral-800 border-dashed rounded-xl"
                >
                    No high-severity events detected recently. The baseline is
                    quiet.
                </div>
            {:else}
                <div class="space-y-6">
                    {#each events as event}
                        <a href="/events/{event.id}" class="block group">
                            <article
                                class="p-6 rounded-2xl border border-neutral-800 bg-neutral-900/50 hover:bg-neutral-800/50 hover:border-neutral-700 transition-all duration-300"
                            >
                                <div class="flex items-center space-x-3 mb-4">
                                    <span
                                        class="px-2.5 py-1 text-xs font-semibold rounded-md {event.severity >
                                        150
                                            ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                            : 'bg-orange-500/10 text-orange-400 border border-orange-500/20'}"
                                    >
                                        Severity: {event.severity}
                                    </span>
                                    <span class="text-sm text-neutral-500"
                                        >{new Date(
                                            event.created_at,
                                        ).toLocaleDateString(undefined, {
                                            month: "short",
                                            day: "numeric",
                                            hour: "2-digit",
                                            minute: "2-digit",
                                        })}</span
                                    >
                                </div>
                                <h3
                                    class="text-xl font-bold mb-3 text-neutral-100 group-hover:text-blue-400 transition-colors"
                                >
                                    {event.title}
                                </h3>

                                <!-- Bullet points snippet -->
                                <ul class="space-y-2 mb-6">
                                    {#each (event.summary?.what_happened || []).slice(0, 2) as point}
                                        <li
                                            class="text-neutral-400 text-sm flex items-start"
                                        >
                                            <span
                                                class="text-blue-500 mr-2 mt-0.5"
                                                >•</span
                                            >
                                            <span class="line-clamp-2"
                                                >{point}</span
                                            >
                                        </li>
                                    {/each}
                                </ul>

                                <!-- Impact Tags -->
                                {#if Array.isArray(event.event_impacts) ? event.event_impacts[0] : event.event_impacts}
                                    {@const impact = Array.isArray(
                                        event.event_impacts,
                                    )
                                        ? event.event_impacts[0]
                                        : event.event_impacts}
                                    <div
                                        class="flex flex-wrap gap-2 mt-4 pt-4 border-t border-neutral-800/50"
                                    >
                                        {#each impact.sectors || [] as sector}
                                            <span
                                                class="px-2 py-1 bg-neutral-800 text-neutral-300 text-xs rounded border border-neutral-700"
                                                >{sector}</span
                                            >
                                        {/each}
                                        {#each (impact.tickers || []).slice(0, 4) as ticker}
                                            <span
                                                class="px-2 py-1 bg-blue-900/20 text-blue-400 text-xs rounded border border-blue-800/30"
                                                >${ticker}</span
                                            >
                                        {/each}
                                    </div>
                                {/if}
                            </article>
                        </a>
                    {/each}
                </div>
            {/if}
        </div>

        <!-- Sidebar / Widget -->
        <div class="col-span-1 space-y-8">
            <div
                class="p-8 rounded-2xl bg-gradient-to-b from-blue-900/20 to-neutral-900 border border-blue-900/30 sticky top-24"
            >
                <h3 class="text-xl font-bold mb-2">High-Signal Alerts</h3>
                <p class="text-sm text-neutral-400 mb-6 line-height-relaxed">
                    Get instantly notified when breaking geopolitics and macro
                    events impact specific sectors and tickers. Zero noise, just
                    signal.
                </p>

                <form onsubmit={handleSubscribe} class="space-y-4">
                    <div>
                        <input
                            type="email"
                            bind:value={subEmail}
                            placeholder="Enter your email"
                            required
                            class="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-4 py-3 text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={subStatus === "loading"}
                        class="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                        {#if subStatus === "loading"}
                            <svg
                                class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                            >
                                <circle
                                    class="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    stroke-width="4"
                                ></circle>
                                <path
                                    class="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                ></path>
                            </svg>
                            Subscribing...
                        {:else}
                            Subscribe to Alerts
                        {/if}
                    </button>

                    {#if subMessage}
                        <p
                            transition:fade
                            class="text-sm mt-3 {subStatus === 'error'
                                ? 'text-red-400'
                                : 'text-green-400'}"
                        >
                            {subMessage}
                        </p>
                    {/if}
                </form>
                <p class="text-xs text-neutral-500 mt-6 text-center">
                    Situational awareness only. Not guaranteed financial advice.
                    One-click unsubscribe.
                </p>
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
