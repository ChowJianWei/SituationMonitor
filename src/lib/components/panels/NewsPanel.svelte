<script lang="ts">
    export let category: string;
    export let title: string;
    export let newsItems: any[] = [];
    export let loading: boolean = false;
</script>

<div
    class="h-full flex flex-col border border-neutral-800 bg-neutral-900 rounded-xl overflow-hidden shadow-sm shadow-neutral-950"
>
    <div
        class="bg-neutral-800/80 px-4 py-2 border-b border-neutral-800 flex items-center justify-between"
    >
        <h3
            class="text-xs font-bold uppercase tracking-wider text-neutral-300 flex items-center gap-2"
        >
            <div
                class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"
            ></div>
            {title}
        </h3>
        <span class="text-[10px] text-neutral-500 uppercase tracking-widest"
            >{category} feed</span
        >
    </div>

    <div
        class="flex-1 overflow-y-auto p-4 space-y-3 no-scrollbar max-h-[300px]"
    >
        {#if loading}
            <div class="animate-pulse flex space-x-4">
                <div class="flex-1 space-y-3 py-1">
                    <div class="h-2 bg-neutral-800 rounded"></div>
                    <div class="h-2 bg-neutral-800 rounded w-5/6"></div>
                    <div class="h-2 bg-neutral-800 rounded w-3/4"></div>
                </div>
            </div>
        {:else if newsItems.length === 0}
            <div class="text-center text-xs text-neutral-500 py-4">
                No recent signals detected
            </div>
        {:else}
            {#each newsItems as item}
                <div
                    class="border-b border-neutral-800/50 pb-2 last:border-0 last:pb-0"
                >
                    <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        class="block text-sm font-medium text-neutral-300 hover:text-blue-400 transition-colors leading-snug line-clamp-3"
                    >
                        {item.title}
                    </a>
                    <div class="flex items-center gap-2 mt-1.5">
                        <span
                            class="text-[10px] text-blue-500/80 font-mono bg-blue-500/10 px-1 rounded"
                            >{item.source || "Intel"}</span
                        >
                    </div>
                </div>
            {/each}
        {/if}
    </div>
</div>
