<script lang="ts">
    import { onMount } from "svelte";
    import { fetchPolymarket, type Prediction } from "$lib/api/misc";

    let predictions: Prediction[] = [];
    let loading = true;

    onMount(async () => {
        try {
            predictions = await fetchPolymarket();
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    });

    function formatVolume(v: string | number): string {
        if (typeof v === "string") return "$" + v;
        return "$" + v;
    }
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
            Polymarket Watch
        </h3>
    </div>

    <div
        class="flex-1 overflow-y-auto p-4 space-y-3 no-scrollbar max-h-[300px]"
    >
        {#if loading}
            <div class="animate-pulse space-y-4">
                <div class="h-4 bg-neutral-800 rounded w-3/4"></div>
                <div class="h-4 bg-neutral-800 rounded w-full"></div>
            </div>
        {:else if predictions.length === 0}
            <div class="text-center text-xs text-neutral-500 py-4">
                No predictions available
            </div>
        {:else}
            {#each predictions as pred}
                <div
                    class="border-b border-neutral-800/50 pb-2 last:border-0 last:pb-0 flex items-center justify-between"
                >
                    <div class="flex-1 min-w-0 pr-4">
                        <div
                            class="text-xs font-medium text-neutral-300 leading-snug"
                        >
                            {pred.question}
                        </div>
                        <div class="text-[10px] text-neutral-500 mt-0.5">
                            Vol: {formatVolume(pred.volume)}
                        </div>
                    </div>
                    <div class="flex-shrink-0 text-right">
                        <span class="text-base font-bold text-green-500"
                            >{pred.yes}%</span
                        >
                    </div>
                </div>
            {/each}
        {/if}
    </div>
</div>
