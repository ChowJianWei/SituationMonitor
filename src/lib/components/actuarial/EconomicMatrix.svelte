<script lang="ts">
    // Mock Economic Data for Life/Pension actuaries
    const yieldCurve = [
        { tenor: "1 Mo", rate: 5.38 },
        { tenor: "6 Mo", rate: 5.32 },
        { tenor: "1 Yr", rate: 5.01 },
        { tenor: "2 Yr", rate: 4.67 },
        { tenor: "5 Yr", rate: 4.25 },
        { tenor: "10 Yr", rate: 4.28 },
        { tenor: "30 Yr", rate: 4.41 },
    ];

    const inflation = {
        cpi_yoy: 3.1,
        core_cpi: 3.8,
        medical_trend: 7.2,
    };
</script>

<div
    class="bg-neutral-900 border border-emerald-900/40 rounded-xl p-4 sm:p-5 shadow-lg flex flex-col h-full"
>
    <div
        class="flex items-center justify-between mb-4 pb-3 border-b border-neutral-800"
    >
        <h3 class="text-sm font-bold text-white flex items-center gap-2">
            <svg
                class="w-4 h-4 text-emerald-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                ></path></svg
            >
            Economic & Discount Matrix
        </h3>
        <span class="text-[10px] text-neutral-500 uppercase tracking-wider"
            >Live</span
        >
    </div>

    <!-- Yield Curve -->
    <div class="mb-5">
        <h4
            class="text-xs text-neutral-400 font-semibold mb-3 uppercase tracking-wider"
        >
            US Treasury Yield Curve
        </h4>
        <div class="flex items-end h-24 gap-1.5 sm:gap-2">
            {#each yieldCurve as point}
                <div
                    class="flex-1 flex flex-col items-center justify-end group relative"
                >
                    <!-- Tooltip -->
                    <div
                        class="opacity-0 group-hover:opacity-100 absolute -top-8 transition-opacity bg-neutral-800 text-white text-[10px] py-1 px-2 rounded whitespace-nowrap z-10 pointer-events-none"
                    >
                        {point.tenor}: {point.rate}%
                    </div>
                    <!-- Bar -->
                    <div
                        class="w-full bg-emerald-500/80 rounded-t-sm transition-all group-hover:bg-emerald-400"
                        style="height: {(point.rate / 6) * 100}%"
                    ></div>
                    <span
                        class="text-[9px] text-neutral-500 mt-2 truncate w-full text-center"
                        >{point.tenor}</span
                    >
                </div>
            {/each}
        </div>
        <!-- Inverted warning -->
        <div
            class="mt-3 flex items-center gap-1.5 text-[10px] text-orange-400/80 bg-orange-500/10 px-2 py-1 rounded border border-orange-500/20"
        >
            <svg
                class="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                ><path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                ></path></svg
            >
            Curve is currently inverted (2Y > 10Y)
        </div>
    </div>

    <div
        class="grid grid-cols-2 gap-3 mt-auto border-t border-neutral-800 pt-4"
    >
        <div>
            <div
                class="text-[10px] text-neutral-500 uppercase tracking-wider mb-1"
            >
                Headline CPI (YoY)
            </div>
            <div class="text-xl font-mono text-white flex items-end gap-1">
                {inflation.cpi_yoy}%
                <span class="text-xs text-green-400 mb-1">↓0.1</span>
            </div>
        </div>
        <div>
            <div
                class="text-[10px] text-neutral-500 uppercase tracking-wider mb-1"
            >
                Medical Cost Trend
            </div>
            <div class="text-xl font-mono text-white flex items-end gap-1">
                {inflation.medical_trend}%
                <span class="text-xs text-red-400 mb-1">↑0.4</span>
            </div>
        </div>
    </div>
</div>
