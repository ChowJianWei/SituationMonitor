<script lang="ts">
    import { onMount } from "svelte";
    import {
        fetchWhaleTransactions,
        type WhaleTransaction,
    } from "$lib/api/misc";

    let whales: WhaleTransaction[] = [];
    let loading = true;

    onMount(async () => {
        try {
            whales = await fetchWhaleTransactions();
        } catch (e) {
            console.error(e);
        } finally {
            loading = false;
        }
    });

    function formatAmount(amt: number): string {
        return amt >= 1000 ? (amt / 1000).toFixed(1) + "K" : amt.toFixed(2);
    }

    function formatUSD(usd: number): string {
        if (usd >= 1e9) return "$" + (usd / 1e9).toFixed(1) + "B";
        if (usd >= 1e6) return "$" + (usd / 1e6).toFixed(1) + "M";
        return "$" + (usd / 1e3).toFixed(0) + "K";
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
            Whale Watch
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
        {:else if whales.length === 0}
            <div class="text-center text-xs text-neutral-500 py-4">
                No whale transactions detected
            </div>
        {:else}
            {#each whales as whale}
                <div
                    class="border-b border-neutral-800/50 pb-2 last:border-0 last:pb-0"
                >
                    <div class="flex justify-between items-center mb-1">
                        <span
                            class="text-[10px] font-bold text-blue-400 bg-blue-500/10 px-1 rounded"
                            >{whale.coin}</span
                        >
                        <span class="text-[11px] text-neutral-300 font-mono"
                            >{formatAmount(whale.amount)} {whale.coin}</span
                        >
                    </div>
                    <div class="flex items-center gap-2 text-[10px]">
                        <span
                            class="text-green-500 font-medium font-mono border border-green-500/20 bg-green-500/5 px-1 py-0.5 rounded"
                            >{formatUSD(whale.usd)}</span
                        >
                        <span class="text-neutral-600">→</span>
                        <span class="text-neutral-500 font-mono tracking-wider"
                            >{whale.hash}</span
                        >
                    </div>
                </div>
            {/each}
        {/if}
    </div>
</div>
