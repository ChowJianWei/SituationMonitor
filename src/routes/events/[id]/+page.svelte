<script lang="ts">
    let { data } = $props();
    let event = $derived(data.event);
    let sources = $derived(data.sources);
    let impacts = $derived(data.impacts);
</script>

<svelte:head>
    <title>{event.title} | Situation Monitor</title>
</svelte:head>

<div
    class="min-h-screen bg-neutral-900 text-neutral-100 font-sans tracking-wide"
>
    <!-- Navbar (simplified) -->
    <header class="border-b border-neutral-800 bg-neutral-950">
        <div
            class="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between"
        >
            <a
                href="/"
                class="font-bold text-lg text-white hover:text-blue-400 transition-colors"
                >← Back to Dashboard</a
            >
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 sm:px-6 py-8 md:py-12">
        <article>
            <div class="mb-8 border-b border-neutral-800 pb-8">
                <div class="flex items-center space-x-3 mb-4">
                    <span
                        class="px-2.5 py-1 text-xs font-semibold rounded-md {event.severity >
                        150
                            ? 'bg-red-500/10 text-red-500 border border-red-500/20'
                            : 'bg-orange-500/10 text-orange-400 border border-orange-500/20'}"
                    >
                        Severity Score: {event.severity}
                    </span>
                    <span class="text-sm text-neutral-500"
                        >{new Date(event.created_at).toLocaleString()}</span
                    >
                </div>
                <h1
                    class="text-3xl md:text-4xl font-extrabold text-white mb-6 leading-tight"
                >
                    {event.title}
                </h1>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-10">
                <div class="md:col-span-2 space-y-10">
                    <!-- Summary block -->
                    <section class="prose prose-invert max-w-none">
                        <h2
                            class="text-2xl font-bold border-b border-neutral-800 pb-2 mb-4"
                        >
                            What Happened
                        </h2>
                        <ul class="space-y-2 text-neutral-300">
                            {#each event.summary?.what_happened || [] as point}
                                <li>{point}</li>
                            {/each}
                        </ul>

                        <h2
                            class="text-2xl font-bold border-b border-neutral-800 pb-2 mb-4 mt-8"
                        >
                            Why it Matters
                        </h2>
                        <ul class="space-y-2 text-neutral-300">
                            {#each event.summary?.why_it_matters || [] as point}
                                <li>{point}</li>
                            {/each}
                        </ul>
                    </section>
                </div>

                <!-- Sidebar -> Affected Markets -->
                <div class="space-y-8">
                    <div
                        class="p-6 rounded-2xl bg-neutral-950 border border-neutral-800"
                    >
                        <h3 class="text-lg font-bold mb-4 text-white">
                            Impacted Markets
                        </h3>
                        {#if impacts}
                            <div class="mb-6">
                                <h4
                                    class="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2"
                                >
                                    Confidence
                                </h4>
                                <span class="text-blue-400 font-bold"
                                    >{impacts.confidence}</span
                                >
                            </div>

                            <div class="mb-6">
                                <h4
                                    class="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2"
                                >
                                    Affected Sectors
                                </h4>
                                <div class="flex flex-wrap gap-2">
                                    {#each impacts.sectors || [] as sector}
                                        <span
                                            class="px-2 py-1 bg-neutral-800 text-neutral-300 text-xs rounded border border-neutral-700"
                                            >{sector}</span
                                        >
                                    {/each}
                                </div>
                            </div>

                            <div class="mb-6">
                                <h4
                                    class="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-2"
                                >
                                    Tickers to Watch
                                </h4>
                                <div class="grid grid-cols-2 gap-2">
                                    {#each impacts.tickers || [] as ticker}
                                        {#if impacts.market_snapshot && impacts.market_snapshot[ticker]}
                                            <div
                                                class="bg-neutral-900 border border-neutral-800 rounded p-2 text-center flex flex-col items-center"
                                            >
                                                <span
                                                    class="font-bold text-sm bg-blue-900/20 text-blue-400 px-1 py-0.5 rounded w-full border border-blue-900/30"
                                                    >${ticker}</span
                                                >
                                                <span
                                                    class="text-xs mt-1 {impacts
                                                        .market_snapshot[ticker]
                                                        .changePercent >= 0
                                                        ? 'text-green-400'
                                                        : 'text-red-400'}"
                                                >
                                                    {impacts.market_snapshot[
                                                        ticker
                                                    ].changePercent > 0
                                                        ? "+"
                                                        : ""}{impacts.market_snapshot[
                                                        ticker
                                                    ].changePercent.toFixed(2)}%
                                                </span>
                                            </div>
                                        {:else}
                                            <div
                                                class="bg-blue-900/20 text-blue-400 border border-blue-900/30 rounded p-2 text-center text-sm font-bold"
                                            >
                                                ${ticker}
                                            </div>
                                        {/if}
                                    {/each}
                                </div>
                            </div>
                        {:else}
                            <p class="text-sm text-neutral-500">
                                No specific market impacts calculated.
                            </p>
                        {/if}
                    </div>
                </div>
            </div>

            <!-- Sources list -->
            <div class="mt-16 pt-8 border-t border-neutral-800">
                <h3 class="text-lg font-bold mb-6 text-white">
                    Sources Verified
                </h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {#each sources as source}
                        <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            class="flex flex-col p-4 rounded-xl border border-neutral-800 bg-neutral-950 hover:bg-neutral-800 transition-colors group"
                        >
                            <span
                                class="text-xs font-semibold text-blue-500 mb-2 uppercase tracking-wide"
                                >{source.source ||
                                    new URL(source.url).hostname.replace(
                                        "www.",
                                        "",
                                    )}</span
                            >
                            <span
                                class="text-sm text-neutral-300 group-hover:text-white line-clamp-2"
                                >{source.title || source.url}</span
                            >
                            <span class="text-xs text-neutral-600 mt-2"
                                >{new Date(
                                    source.published_at,
                                ).toLocaleString()}</span
                            >
                        </a>
                    {/each}
                </div>
            </div>
        </article>
    </main>
</div>
