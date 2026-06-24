<script lang="ts">
    import { onMount } from "svelte";

    type Tab = "Briefing" | "Performance" | "Allocation" | "Intelligence";
    let activeTab = $state<Tab>("Briefing");

    let briefing = $state<any>(null);
    let performance = $state<any>(null);
    let allocation = $state<any[]>([]);
    let macro = $state<any>(null);
    let online = $state(true);
    let busy = $state(false);
    let loading = $state(true);

    async function get(path: string) {
        const r = await fetch(`/api/quant/${path}`);
        if (!r.ok) throw new Error(`${path} ${r.status}`);
        return r.json();
    }

    async function loadAll() {
        try {
            briefing = await get("daily-briefing");
            performance = await get("performance");
            const a = await get("fund-allocation");
            allocation = a.allocations ?? [];
            macro = await get("macro-propagation");
            online = true;
        } catch (e) {
            online = false;
        } finally {
            loading = false;
        }
    }

    async function runCycle() {
        busy = true;
        try {
            await fetch("/api/quant/cycle/run", { method: "POST" });
            await loadAll();
        } finally {
            busy = false;
        }
    }

    onMount(loadAll);

    const fmtUsd = (n: number | null | undefined) =>
        n == null
            ? "—"
            : n.toLocaleString("en-US", {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0,
              });
    const fmtPct = (n: number | null | undefined) =>
        n == null ? "—" : `${(n * 100).toFixed(2)}%`;

    // Equity-curve sparkline points.
    let sparkPoints = $derived.by(() => {
        const data: number[] = performance?.equity_curve ?? [];
        if (data.length < 2) return "";
        const w = 600,
            h = 120,
            pad = 8;
        const min = Math.min(...data),
            max = Math.max(...data);
        const span = max - min || 1;
        return data
            .map((v, i) => {
                const x = pad + (i / (data.length - 1)) * (w - 2 * pad);
                const y = h - pad - ((v - min) / span) * (h - 2 * pad);
                return `${x.toFixed(1)},${y.toFixed(1)}`;
            })
            .join(" ");
    });
    let sparkUp = $derived(
        (performance?.equity_curve?.at(-1) ?? 0) >=
            (performance?.equity_curve?.[0] ?? 0),
    );

    function regimeTone(r: string) {
        if (r === "TAIL_STRESS") return "text-red-400";
        if (r === "TRENDING") return "text-emerald-400";
        return "text-amber-400";
    }
</script>

<svelte:head><title>Quant Desk | Situation Monitor</title></svelte:head>

<div class="min-h-screen bg-neutral-900 text-neutral-100 font-sans pb-12">
    <header class="border-b border-blue-900/40 bg-neutral-950 sticky top-0 z-50">
        <div
            class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-14"
        >
            <div class="flex items-center gap-4">
                <a href="/" class="text-neutral-500 hover:text-white transition"
                    >← Main Dashboard</a
                >
                <div class="w-px h-6 bg-neutral-800"></div>
                <div class="font-bold text-xl tracking-tighter text-white">
                    QuantDesk<span class="text-blue-500">.</span>
                </div>
                <span
                    class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider {online
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-red-500/10 text-red-400 border border-red-500/20'}"
                >
                    {online ? "Engine Online" : "Engine Offline"}
                </span>
            </div>
            <button
                onclick={runCycle}
                disabled={busy || !online}
                class="px-3 py-1.5 rounded-md text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40"
            >
                {busy ? "Running…" : "Run underwriting cycle"}
            </button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8">
        {#if !online}
            <div
                class="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200"
            >
                <p class="font-semibold">Actuarial engine unreachable.</p>
                <p class="mt-1 text-red-300/80">
                    Start the Python backend and point <code
                        >ACTUARIAL_API_URL</code
                    > at it:
                </p>
                <pre
                    class="mt-2 overflow-x-auto rounded bg-neutral-950 p-2 text-xs text-neutral-300">cd actuarial_quant_system
.venv/bin/python -m uvicorn src.api_dashboard.main:app --port 8200</pre>
            </div>
        {/if}

        <!-- Tabs -->
        <div
            class="mb-6 flex gap-1 border-b border-neutral-800 overflow-x-auto no-scrollbar"
        >
            {#each ["Briefing", "Performance", "Allocation", "Intelligence"] as tab}
                <button
                    class="px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap {activeTab ===
                    tab
                        ? 'border-blue-500 text-white'
                        : 'border-transparent text-neutral-400 hover:text-neutral-200'}"
                    onclick={() => (activeTab = tab as Tab)}>{tab}</button
                >
            {/each}
        </div>

        {#if loading}
            <p class="text-neutral-500">Loading…</p>
        {:else if activeTab === "Briefing"}
            <!-- ===== BRIEFING ===== -->
            {#if briefing}
                <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    <div
                        class="rounded-xl border border-neutral-800 bg-neutral-950 p-5 flex flex-col items-center justify-center"
                    >
                        <div class="text-5xl font-extrabold text-white">
                            {briefing.surplus_health_index?.toFixed(0)}
                        </div>
                        <div
                            class="mt-1 text-[10px] uppercase tracking-widest text-neutral-500"
                        >
                            Surplus Health Index
                        </div>
                    </div>
                    <div class="lg:col-span-3 grid grid-cols-2 gap-4">
                        <div
                            class="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                        >
                            <div
                                class="text-[10px] uppercase tracking-wider text-neutral-500"
                            >
                                Net 24h Earnings
                            </div>
                            <div
                                class="text-2xl font-semibold {(briefing.net_earnings_24h_usd ??
                                    0) >= 0
                                    ? 'text-emerald-400'
                                    : 'text-red-400'}"
                            >
                                {fmtUsd(briefing.net_earnings_24h_usd)}
                            </div>
                        </div>
                        <div
                            class="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                        >
                            <div
                                class="text-[10px] uppercase tracking-wider text-neutral-500"
                            >
                                Active Regime
                            </div>
                            <div
                                class="text-2xl font-semibold {regimeTone(
                                    briefing.regime,
                                )}"
                            >
                                {briefing.regime?.replace(/_/g, " ")}
                            </div>
                        </div>
                        <div
                            class="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                        >
                            <div
                                class="text-[10px] uppercase tracking-wider text-neutral-500"
                            >
                                Ruin Probability (10k-step)
                            </div>
                            <div class="text-2xl font-semibold text-white">
                                {fmtPct(briefing.ruin_probability)}
                            </div>
                        </div>
                        <div
                            class="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                        >
                            <div
                                class="text-[10px] uppercase tracking-wider text-neutral-500"
                            >
                                Expected Shortfall (99%)
                            </div>
                            <div class="text-2xl font-semibold text-amber-400">
                                {fmtPct(briefing.expected_shortfall_99)}
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    class="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-5"
                >
                    <h4
                        class="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-400"
                    >
                        Executive Narrative
                    </h4>
                    <ul class="space-y-2">
                        {#each briefing.executive_narrative ?? [] as line}
                            <li class="flex gap-2 text-sm text-neutral-300">
                                <span class="text-emerald-500">•</span>
                                {line}
                            </li>
                        {/each}
                    </ul>
                </div>
            {/if}
        {:else if activeTab === "Performance"}
            <!-- ===== PERFORMANCE ===== -->
            {#if performance}
                <p class="mb-4 text-xs text-amber-300/80">{performance.note}</p>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div
                        class="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                    >
                        <div
                            class="text-[10px] uppercase tracking-wider text-neutral-500"
                        >
                            Estimated Equity
                        </div>
                        <div class="text-2xl font-semibold text-white">
                            {fmtUsd(performance.estimated_equity_usd)}
                        </div>
                    </div>
                    <div
                        class="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                    >
                        <div
                            class="text-[10px] uppercase tracking-wider text-neutral-500"
                        >
                            Estimated P&L
                        </div>
                        <div
                            class="text-2xl font-semibold {(performance.estimated_pnl_usd ??
                                0) >= 0
                                ? 'text-emerald-400'
                                : 'text-red-400'}"
                        >
                            {fmtUsd(performance.estimated_pnl_usd)}
                        </div>
                    </div>
                    <div
                        class="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                    >
                        <div
                            class="text-[10px] uppercase tracking-wider text-neutral-500"
                        >
                            Paper Fills
                        </div>
                        <div class="text-2xl font-semibold text-white">
                            {performance.total_paper_fills}
                        </div>
                    </div>
                    <div
                        class="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
                    >
                        <div
                            class="text-[10px] uppercase tracking-wider text-neutral-500"
                        >
                            Rejected by Gate
                        </div>
                        <div
                            class="text-2xl font-semibold {performance.rejected_by_gate >
                            0
                                ? 'text-red-400'
                                : 'text-white'}"
                        >
                            {performance.rejected_by_gate}
                        </div>
                    </div>
                </div>

                <div
                    class="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-5"
                >
                    <h4
                        class="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-400"
                    >
                        Estimated Paper Equity Curve
                    </h4>
                    {#if sparkPoints}
                        <svg viewBox="0 0 600 120" class="w-full">
                            <polyline
                                fill="none"
                                stroke={sparkUp ? "#10b981" : "#ef4444"}
                                stroke-width="2"
                                points={sparkPoints}
                            />
                        </svg>
                    {:else}
                        <p class="text-sm text-neutral-500">
                            No fills yet — run a cycle.
                        </p>
                    {/if}
                    <div
                        class="mt-2 flex flex-wrap justify-between gap-2 text-xs text-neutral-500"
                    >
                        <span
                            >Premium: <span class="text-emerald-400"
                                >{fmtUsd(
                                    performance.estimated_premium_collected_usd,
                                )}</span
                            ></span
                        >
                        <span
                            >Costs: <span class="text-red-400"
                                >{fmtUsd(performance.total_costs_usd)}</span
                            ></span
                        >
                        <span
                            >Reserves locked: <span class="text-amber-400"
                                >{fmtUsd(performance.reserves_locked_usd)}</span
                            ></span
                        >
                    </div>
                </div>

                <div
                    class="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-5"
                >
                    <h4
                        class="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-400"
                    >
                        Activity Feed
                    </h4>
                    {#if (performance.recent_activity ?? []).length === 0}
                        <p class="text-sm text-neutral-500">No fills yet.</p>
                    {:else}
                        <ul class="space-y-2">
                            {#each performance.recent_activity as t}
                                <li
                                    class="flex flex-wrap items-center gap-2 rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm"
                                >
                                    <span
                                        class="rounded px-2 py-0.5 text-xs font-semibold {t.risk_verdict ===
                                        'APPROVED'
                                            ? 'bg-emerald-500/15 text-emerald-400'
                                            : 'bg-red-500/15 text-red-400'}"
                                        >{t.risk_verdict}</span
                                    >
                                    <span class="font-semibold text-white"
                                        >{t.symbol}</span
                                    >
                                    <span class="text-neutral-400"
                                        >{t.structure}</span
                                    >
                                    <span
                                        class={t.side === "SELL"
                                            ? "text-amber-400"
                                            : "text-sky-400"}>{t.side}</span
                                    >
                                    <span class="text-neutral-300"
                                        >{fmtUsd(Number(t.notional_usd))}</span
                                    >
                                    <span
                                        class="ml-auto truncate text-xs text-neutral-500"
                                        >{t.rationale}</span
                                    >
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </div>
            {/if}
        {:else if activeTab === "Allocation"}
            <!-- ===== ALLOCATION ===== -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                {#each allocation as a}
                    <div
                        class="rounded-xl border border-neutral-800 bg-neutral-950 p-5"
                    >
                        <div class="mb-3 text-lg font-bold text-white">
                            {a.asset}
                        </div>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-neutral-400"
                                    >Yield Generation</span
                                >
                                <span class="text-emerald-400"
                                    >{fmtUsd(a.yield_generation_usd)}</span
                                >
                            </div>
                            <div class="flex justify-between">
                                <span class="text-neutral-400">Loss Reserve</span
                                >
                                <span class="text-amber-400"
                                    >{fmtUsd(a.loss_reserve_usd)}</span
                                >
                            </div>
                            <div class="flex justify-between">
                                <span class="text-neutral-400">Delta Hedge</span>
                                <span class="text-sky-400"
                                    >{fmtUsd(a.delta_hedge_usd)}</span
                                >
                            </div>
                        </div>
                    </div>
                {/each}
                {#if allocation.length === 0}
                    <p class="text-sm text-neutral-500">
                        No allocations yet — run a cycle.
                    </p>
                {/if}
            </div>
        {:else if activeTab === "Intelligence"}
            <!-- ===== INTELLIGENCE ===== -->
            {#if macro?.links?.length}
                <div
                    class="rounded-xl border border-neutral-800 bg-neutral-950 p-5"
                >
                    <h4
                        class="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-400"
                    >
                        Macro Shock Propagation — VAR(1) Impulse Response
                    </h4>
                    <ul class="space-y-2 text-sm">
                        {#each macro.links as l}
                            <li class="flex flex-wrap items-center gap-2">
                                <span class="font-mono text-xs text-amber-300"
                                    >{l.source}</span
                                >
                                <span class="text-neutral-600">→</span>
                                <span class="font-mono text-xs text-sky-300"
                                    >{l.channel}</span
                                >
                                <span class="text-neutral-600">→</span>
                                <span class="font-mono text-xs text-emerald-300"
                                    >{l.target}</span
                                >
                                <span
                                    class="ml-auto text-xs {l.credibility > 0.7
                                        ? 'text-emerald-400'
                                        : 'text-amber-400'}"
                                    >credibility {(l.credibility * 100).toFixed(
                                        0,
                                    )}%</span
                                >
                            </li>
                        {/each}
                    </ul>
                </div>
            {/if}
            <div
                class="mt-4 overflow-hidden rounded-xl border border-neutral-800"
            >
                <table class="w-full text-left text-sm">
                    <thead class="bg-neutral-900 text-neutral-400">
                        <tr>
                            <th class="px-4 py-3 font-medium">Model</th>
                            <th class="px-4 py-3 font-medium">Purpose</th>
                            <th class="px-4 py-3 font-medium">Why Trusted</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-neutral-800 bg-neutral-950">
                        <tr>
                            <td class="px-4 py-3 font-semibold text-white"
                                >EVT (GPD)</td
                            >
                            <td class="px-4 py-3 text-neutral-300"
                                >Tail risk → CVaR / Expected Shortfall</td
                            >
                            <td class="px-4 py-3 text-neutral-400"
                                >Honest about fat tails; sizes the frozen reserve.</td
                            >
                        </tr>
                        <tr>
                            <td class="px-4 py-3 font-semibold text-white">HMM</td
                            >
                            <td class="px-4 py-3 text-neutral-300"
                                >Latent regime classification</td
                            >
                            <td class="px-4 py-3 text-neutral-400"
                                >Detects regime shifts before vol confirms.</td
                            >
                        </tr>
                        <tr>
                            <td class="px-4 py-3 font-semibold text-white"
                                >GARCH(1,1)</td
                            >
                            <td class="px-4 py-3 text-neutral-300"
                                >Conditional vol forecast</td
                            >
                            <td class="px-4 py-3 text-neutral-400"
                                >Prices the premium the system collects.</td
                            >
                        </tr>
                    </tbody>
                </table>
            </div>
        {/if}
    </main>
</div>

<style>
    .no-scrollbar::-webkit-scrollbar {
        display: none;
    }
    .no-scrollbar {
        -ms-overflow-style: none;
        scrollbar-width: none;
    }
</style>
