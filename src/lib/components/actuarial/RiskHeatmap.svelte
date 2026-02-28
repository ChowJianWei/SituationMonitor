<script lang="ts">
    // Mock Heatmap Data for Actuarial correlations
    // Rows: Macro Drivers, Columns: Insurance Lines
    const rows = [
        "Inflation",
        "Supply Chain",
        "Labor Cost",
        "Climate",
        "Cyber Crime",
    ];
    const cols = ["Auto", "Property", "Health", "Cyber", "D&O"];

    // 0.0 to 1.0 correlation severity
    const heatmapData = [
        [0.9, 0.8, 0.6, 0.2, 0.4], // Inflation impact
        [0.8, 0.7, 0.3, 0.1, 0.5], // Supply Chain impact
        [0.4, 0.3, 0.9, 0.6, 0.2], // Labor Cost impact
        [0.1, 0.9, 0.2, 0.0, 0.6], // Climate impact
        [0.3, 0.4, 0.8, 0.9, 0.8], // Cyber Crime impact
    ];

    function getColor(val: number) {
        if (val > 0.8) return "bg-red-500/80 hover:bg-red-400 transition";
        if (val > 0.6) return "bg-orange-500/80 hover:bg-orange-400 transition";
        if (val > 0.4) return "bg-yellow-500/80 hover:bg-yellow-400 transition";
        if (val > 0.2) return "bg-blue-500/50 hover:bg-blue-400 transition";
        return "bg-neutral-800 hover:bg-neutral-700 transition";
    }
</script>

<div
    class="bg-neutral-900 border border-purple-900/40 rounded-xl p-4 sm:p-5 shadow-lg flex flex-col h-full overflow-x-auto no-scrollbar"
>
    <div
        class="flex items-center justify-between mb-4 pb-3 border-b border-neutral-800 min-w-[400px]"
    >
        <h3 class="text-sm font-bold text-white flex items-center gap-2">
            <svg
                class="w-4 h-4 text-purple-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5"
                ></path></svg
            >
            Line Correlation Heatmap
        </h3>
        <span class="text-[10px] text-neutral-500 uppercase tracking-wider"
            >Macro → LOB</span
        >
    </div>

    <div class="min-w-[400px] flex-1">
        <!-- Header row -->
        <div class="flex mb-2">
            <div class="w-24 shrink-0"></div>
            <!-- Empty corner -->
            {#each cols as col}
                <div
                    class="flex-1 text-center text-[10px] text-neutral-400 uppercase tracking-wider font-semibold mr-1"
                >
                    {col}
                </div>
            {/each}
        </div>

        <!-- Heatmap Grid -->
        <div class="space-y-1">
            {#each rows as row, i}
                <div class="flex items-center group">
                    <div
                        class="w-24 shrink-0 text-xs text-neutral-300 font-medium truncate pr-2 group-hover:text-white transition"
                    >
                        {row}
                    </div>
                    {#each cols as col, j}
                        <div
                            class="flex-1 mr-1 h-8 rounded relative {getColor(
                                heatmapData[i][j],
                            )}"
                        >
                            <!-- Tooltip on hover -->
                            <div
                                class="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-neutral-950 border border-neutral-700 text-white text-[10px] py-1 px-2 rounded whitespace-nowrap z-10 pointer-events-none transition-opacity"
                            >
                                Corr: {(heatmapData[i][j] * 100).toFixed(0)}%
                            </div>
                        </div>
                    {/each}
                </div>
            {/each}
        </div>

        <!-- Legend -->
        <div
            class="mt-6 flex items-center gap-2 justify-end text-[9px] text-neutral-500 uppercase tracking-wider border-t border-neutral-800 pt-3"
        >
            <span>Low</span>
            <div class="w-3 h-3 rounded bg-neutral-800"></div>
            <div class="w-3 h-3 rounded bg-blue-500/50"></div>
            <div class="w-3 h-3 rounded bg-yellow-500/80"></div>
            <div class="w-3 h-3 rounded bg-orange-500/80"></div>
            <div class="w-3 h-3 rounded bg-red-500/80"></div>
            <span>Critical</span>
        </div>
    </div>
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
