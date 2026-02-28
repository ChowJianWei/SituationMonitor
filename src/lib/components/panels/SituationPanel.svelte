<script lang="ts">
    export let title: string;
    export let subtitle: string;
    export let keywords: string[] = [];
    export let newsItems: any[] = [];

    // Simple mock risk level calculation based on keywords and volume
    $: isCritical =
        newsItems.length > 5 ||
        newsItems.some((n) =>
            keywords.some((k) => n.title.toLowerCase().includes(k)),
        );
    $: statusColor = isCritical
        ? "bg-red-500 text-red-500"
        : newsItems.length > 0
          ? "bg-orange-500 text-orange-500"
          : "bg-neutral-500 text-neutral-500";
    $: statusText = isCritical
        ? "CRITICAL"
        : newsItems.length > 0
          ? "ELEVATED"
          : "MONITORING";
</script>

<div
    class="h-full flex flex-col border border-neutral-800 bg-neutral-900 rounded-xl overflow-hidden shadow-sm shadow-neutral-950"
>
    <div
        class="px-4 py-3 border-b border-neutral-800 text-center relative overflow-hidden"
    >
        <!-- Subtle background glow -->
        <div
            class="absolute inset-x-0 top-0 h-1 {statusColor} opacity-20"
        ></div>

        <h3 class="text-sm font-bold text-neutral-100">{title}</h3>
        <p class="text-[10px] text-neutral-400 mt-0.5">{subtitle}</p>

        <div
            class="mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-neutral-800 bg-neutral-950/50"
        >
            <div
                class="w-1.5 h-1.5 rounded-full {statusColor} animate-pulse"
            ></div>
            <span
                class="text-[9px] font-bold tracking-widest {statusColor} bg-clip-text {isCritical
                    ? 'animate-pulse'
                    : ''}">{statusText}</span
            >
        </div>
    </div>

    <div
        class="flex-1 overflow-y-auto p-4 space-y-3 no-scrollbar max-h-[300px]"
    >
        {#if newsItems.length === 0}
            <div class="text-center text-xs text-neutral-500 py-4">
                No anomalies detected
            </div>
        {:else}
            {#each newsItems.slice(0, 5) as item}
                <div
                    class="border-b border-neutral-800/50 pb-2 last:border-0 last:pb-0"
                >
                    <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        class="block text-xs font-medium text-neutral-300 hover:text-red-400 transition-colors leading-snug"
                    >
                        {item.title}
                    </a>
                </div>
            {/each}
        {/if}
    </div>
</div>
