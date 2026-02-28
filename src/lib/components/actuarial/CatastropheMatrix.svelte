<script lang="ts">
    // Mock Data for P&C actuaries
    const anomalies = [
        {
            region: "North Atlantic",
            metric: "SST Anomaly",
            value: "+1.2°C",
            threat: "High",
        },
        {
            region: "Global Land",
            metric: "Temp Anomaly",
            value: "+1.05°C",
            threat: "Elevated",
        },
        {
            region: "ENSO region",
            metric: "ONI Index",
            value: "+1.5",
            threat: "El Niño",
        },
    ];

    const stormProbabilities = [
        { basin: "Atlantic", active: 2, namingProb: "80%", cat3Prob: "40%" },
        { basin: "East Pacific", active: 1, namingProb: "20%", cat3Prob: "5%" },
    ];
</script>

<div
    class="bg-neutral-900 border border-blue-900/40 rounded-xl p-4 sm:p-5 shadow-lg flex flex-col h-full"
>
    <div
        class="flex items-center justify-between mb-4 pb-3 border-b border-neutral-800"
    >
        <h3 class="text-sm font-bold text-white flex items-center gap-2">
            <svg
                class="w-4 h-4 text-blue-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064m-12.87-8A8.001 8.001 0 1012 2.054a8.001 8.001 0 00-6.826 6.936z"
                ></path></svg
            >
            Catastrophe & Climate Matrix
        </h3>
        <span class="text-[10px] text-neutral-500 uppercase tracking-wider"
            >NOAA/NHC Sync</span
        >
    </div>

    <!-- Anomalies -->
    <div class="mb-5 flex-1">
        <h4
            class="text-xs text-neutral-400 font-semibold mb-3 uppercase tracking-wider"
        >
            Climate Anomalies
        </h4>
        <div class="space-y-2">
            {#each anomalies as anomaly}
                <div
                    class="flex justify-between items-center bg-neutral-950/50 p-2 rounded-lg border border-neutral-800/50"
                >
                    <div>
                        <div class="text-[10px] text-neutral-500">
                            {anomaly.region}
                        </div>
                        <div class="text-sm text-neutral-200 font-medium">
                            {anomaly.metric}
                        </div>
                    </div>
                    <div class="text-right">
                        <div
                            class="text-sm font-bold {anomaly.threat ===
                                'High' || anomaly.threat === 'El Niño'
                                ? 'text-red-400'
                                : 'text-orange-400'}"
                        >
                            {anomaly.value}
                        </div>
                        <div
                            class="text-[9px] uppercase tracking-wide text-neutral-500"
                        >
                            {anomaly.threat}
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    </div>

    <!-- Storm Probabilities -->
    <div class="border-t border-neutral-800 pt-4">
        <h4
            class="text-xs text-neutral-400 font-semibold mb-3 uppercase tracking-wider"
        >
            Cyclonic Genesis Prob (48h)
        </h4>
        <div class="grid grid-cols-2 gap-3">
            {#each stormProbabilities as basin}
                <div
                    class="bg-neutral-950 p-2.5 rounded border {basin.namingProb ===
                    '80%'
                        ? 'border-red-900/50'
                        : 'border-neutral-800'}"
                >
                    <div
                        class="text-[10px] text-neutral-400 uppercase tracking-wider mb-2 flex justify-between"
                    >
                        {basin.basin}
                        <span class="text-white bg-neutral-800 px-1.5 rounded"
                            >{basin.active} Active</span
                        >
                    </div>
                    <div class="flex justify-between items-end">
                        <span class="text-xs text-neutral-500">Name Prob:</span>
                        <span
                            class="text-lg font-mono {basin.namingProb === '80%'
                                ? 'text-red-400'
                                : 'text-blue-400'}">{basin.namingProb}</span
                        >
                    </div>
                </div>
            {/each}
        </div>
    </div>
</div>
