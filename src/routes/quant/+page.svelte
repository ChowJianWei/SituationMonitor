<script lang="ts">
    import { onMount } from "svelte";

    type Tab = "Briefing" | "Performance" | "Markets" | "Allocation" | "Intelligence";
    let activeTab = $state<Tab>("Briefing");

    let markets = $state<any[]>([]);
    let selectedSymbol = $state<string>("BTC");
    let candleData = $state<any>(null);
    let candlesLoading = $state(false);

    let briefing = $state<any>(null);
    let performance = $state<any>(null);
    let allocation = $state<any[]>([]);
    let macro = $state<any>(null);
    let online = $state(true);
    let busy = $state(false);
    let loading = $state(true);
    let showGlossary = $state(false);

    // Add money / withdraw (paper)
    let showMoney = $state(false);
    let moneyKind = $state<"deposit" | "withdraw">("deposit");
    let moneyAmount = $state("");
    let moneyMsg = $state("");
    let moneyBusy = $state(false);

    function openMoney(kind: "deposit" | "withdraw") {
        moneyKind = kind;
        moneyAmount = "";
        moneyMsg = "";
        showMoney = true;
    }

    async function submitMoney() {
        const amt = Number(moneyAmount);
        if (!amt || amt <= 0) {
            moneyMsg = "Enter a positive amount.";
            return;
        }
        moneyBusy = true;
        moneyMsg = "";
        try {
            const r = await fetch(`/api/quant/account/${moneyKind}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ amount_usd: amt }),
            });
            const d = await r.json();
            if (d.ok) {
                showMoney = false;
                await loadAll();
            } else {
                moneyMsg = d.error || "Something went wrong.";
            }
        } catch {
            moneyMsg = "Couldn't reach the engine.";
        } finally {
            moneyBusy = false;
        }
    }

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

    async function loadMarkets() {
        try {
            const m = await get("markets");
            markets = m.markets ?? [];
        } catch {
            markets = [];
        }
    }

    async function loadCandles(sym: string) {
        selectedSymbol = sym;
        candlesLoading = true;
        try {
            candleData = await get(`markets/${sym}/candles?limit=90`);
        } catch {
            candleData = null;
        } finally {
            candlesLoading = false;
        }
    }

    onMount(async () => {
        await loadAll();
        await loadMarkets();
        await loadCandles(selectedSymbol);
    });

    // Candlestick geometry derived from the selected market's candles.
    let chart = $derived.by(() => {
        const cs = candleData?.candles ?? [];
        if (cs.length < 2) return null;
        const w = 920,
            h = 340,
            padL = 8,
            padR = 56,
            padT = 10,
            padB = 22;
        const min = Math.min(...cs.map((c: any) => c.l));
        const max = Math.max(...cs.map((c: any) => c.h));
        const span = max - min || 1;
        const n = cs.length;
        const cw = (w - padL - padR) / n;
        const bodyW = Math.max(1.5, cw * 0.62);
        const xc = (i: number) => padL + i * cw + cw / 2;
        const yv = (v: number) => padT + (1 - (v - min) / span) * (h - padT - padB);
        const bars = cs.map((c: any, i: number) => ({
            x: xc(i),
            wickTop: yv(c.h),
            wickBot: yv(c.l),
            bodyTop: yv(Math.max(c.o, c.c)),
            bodyH: Math.max(1, Math.abs(yv(c.o) - yv(c.c))),
            up: c.c >= c.o,
        }));
        return { w, h, padL, padR, bodyW, min, max, last: cs[cs.length - 1].c, bars,
                 yLast: yv(cs[cs.length - 1].c) };
    });

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

    // ---- plain-English translators ----
    function regimePlain(r: string) {
        if (r === "TAIL_STRESS")
            return {
                label: "Stressed (crash risk)",
                tone: "text-red-400",
                meaning:
                    "Markets are turbulent. The system pulls back, stops selling risk, and raises cash to protect you.",
            };
        if (r === "TRENDING")
            return {
                label: "Trending",
                tone: "text-emerald-400",
                meaning:
                    "Markets are moving in one clear direction. The system leans toward simply holding the asset.",
            };
        return {
            label: "Choppy / sideways",
            tone: "text-amber-400",
            meaning:
                "Markets are bouncing in a range. This is the sweet spot for selling option 'insurance' and collecting premium.",
        };
    }

    function healthWord(shi: number) {
        if (shi >= 90) return { word: "Very safe", tone: "text-emerald-400" };
        if (shi >= 70) return { word: "Healthy", tone: "text-emerald-400" };
        if (shi >= 50) return { word: "Caution", tone: "text-amber-400" };
        return { word: "At risk", tone: "text-red-400" };
    }

    function ruinWord(p: number) {
        if (p < 0.001) return "almost no chance of wiping out the account";
        if (p < 0.01) return "a very low chance of wiping out the account";
        if (p < 0.05) return "a small chance of wiping out the account";
        return "a real chance of wiping out — be careful";
    }

    // One-sentence conclusion built from the live numbers.
    let bottomLine = $derived.by(() => {
        if (!briefing) return "";
        const h = healthWord(briefing.surplus_health_index).word.toLowerCase();
        const reg = regimePlain(briefing.regime);
        const pnl = performance?.estimated_pnl_usd ?? 0;
        const pnlStr =
            pnl >= 0 ? `up ${fmtUsd(pnl)}` : `down ${fmtUsd(-pnl)}`;
        const action =
            briefing.regime === "TAIL_STRESS"
                ? "holding back and keeping cash safe"
                : "selling overpriced option 'insurance' and hedging the risk";
        return `Your money is ${h} — ${ruinWord(briefing.ruin_probability)}. The market is ${reg.label.toLowerCase()}, so the system is ${action}. On paper it's ${pnlStr}. It runs on autopilot with fake money — nothing for you to do.`;
    });

    function regimeTone(r: string) {
        return regimePlain(r).tone;
    }

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

    const glossary = [
        ["Surplus Health Index", "An overall 0–100 safety score for your capital — like a credit score for your account's survival. Higher = safer."],
        ["Market regime", "What 'mood' the market is in: trending, choppy/sideways, or stressed. The system switches strategy based on it."],
        ["Ruin probability", "The estimated chance the account gets wiped out over a very long run. The system is built to keep this near zero."],
        ["Expected Shortfall (CVaR)", "If a rare bad day happens, the typical loss to expect. Smaller = safer."],
        ["Loss reserve", "Cash the system freezes as a safety buffer whenever it holds a position — like an insurer setting money aside for claims."],
        ["Premium", "The income the system earns by selling options — it acts like an insurance company collecting premiums."],
        ["Paper mode", "Everything is simulated with fake money. No real trades, no real money at risk."],
    ];
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
            <div class="flex items-center gap-2">
                <button
                    onclick={() => (showGlossary = !showGlossary)}
                    class="px-3 py-1.5 rounded-md text-xs font-medium border border-neutral-700 text-neutral-300 hover:bg-neutral-800"
                >
                    {showGlossary ? "Hide" : "What do these mean?"}
                </button>
                <button
                    onclick={runCycle}
                    disabled={busy || !online}
                    class="px-3 py-1.5 rounded-md text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40"
                    title="Make the system analyse the market and place simulated trades right now"
                >
                    {busy ? "Running…" : "Run analysis now"}
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-8">
        {#if !online}
            <div
                class="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200"
            >
                <p class="font-semibold">The quant engine isn't reachable right now.</p>
                <p class="mt-1 text-red-300/80">
                    It runs as a separate service. Make sure it's deployed and that
                    <code>ACTUARIAL_API_URL</code> points to it.
                </p>
            </div>
        {/if}

        <!-- Always-visible plain-English conclusion -->
        {#if briefing}
            <div class="mb-6 rounded-xl border border-blue-500/30 bg-blue-500/5 p-5">
                <div class="mb-2 text-[11px] font-bold uppercase tracking-widest text-blue-300">
                    ⓘ In plain English — the bottom line
                </div>
                <p class="text-base md:text-lg leading-relaxed text-neutral-100">
                    {bottomLine}
                </p>
            </div>
        {/if}

        {#if showGlossary}
            <div class="mb-6 rounded-xl border border-neutral-800 bg-neutral-950 p-5">
                <h4 class="mb-3 text-sm font-semibold text-white">Quick glossary</h4>
                <dl class="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3">
                    {#each glossary as [term, def]}
                        <div>
                            <dt class="text-sm font-semibold text-blue-300">{term}</dt>
                            <dd class="text-sm text-neutral-400">{def}</dd>
                        </div>
                    {/each}
                </dl>
            </div>
        {/if}

        <!-- Tabs -->
        <div
            class="mb-6 flex gap-1 border-b border-neutral-800 overflow-x-auto no-scrollbar"
        >
            {#each [["Briefing", "Overview"], ["Performance", "Track record"], ["Markets", "Charts"], ["Allocation", "Where the money is"], ["Intelligence", "The why"]] as [tab, sub]}
                <button
                    class="px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap {activeTab ===
                    tab
                        ? 'border-blue-500 text-white'
                        : 'border-transparent text-neutral-400 hover:text-neutral-200'}"
                    onclick={() => (activeTab = tab as Tab)}
                    >{tab} <span class="text-[10px] text-neutral-600">· {sub}</span></button
                >
            {/each}
        </div>

        {#if loading}
            <p class="text-neutral-500">Loading…</p>
        {:else if activeTab === "Briefing"}
            {#if briefing}
                {@const hw = healthWord(briefing.surplus_health_index)}
                {@const reg = regimePlain(briefing.regime)}
                <div class="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                    <div>
                        <div class="text-[10px] uppercase tracking-wider text-neutral-500">
                            Money you can deploy (free cash)
                        </div>
                        <div class="text-xl font-semibold text-white">
                            {fmtUsd(briefing.free_capital_usd)}
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <button
                            onclick={() => openMoney("deposit")}
                            class="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
                            >+ Add money</button
                        >
                        <button
                            onclick={() => openMoney("withdraw")}
                            class="rounded-md border border-neutral-700 px-3 py-1.5 text-xs font-medium text-neutral-200 hover:bg-neutral-800"
                            >Withdraw</button
                        >
                    </div>
                </div>
                <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    <div
                        class="rounded-xl border border-neutral-800 bg-neutral-950 p-5 flex flex-col items-center justify-center text-center"
                    >
                        <div class="text-5xl font-extrabold text-white">
                            {briefing.surplus_health_index?.toFixed(0)}
                        </div>
                        <div class="mt-1 text-sm font-semibold {hw.tone}">{hw.word}</div>
                        <div class="mt-1 text-[11px] text-neutral-500">
                            Overall safety score (out of 100)
                        </div>
                    </div>
                    <div class="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                            <div class="text-[10px] uppercase tracking-wider text-neutral-500">
                                Profit / loss (last 24h)
                            </div>
                            <div
                                class="text-2xl font-semibold {(briefing.net_earnings_24h_usd ??
                                    0) >= 0
                                    ? 'text-emerald-400'
                                    : 'text-red-400'}"
                            >
                                {fmtUsd(briefing.net_earnings_24h_usd)}
                            </div>
                            <div class="mt-1 text-[11px] text-neutral-500">
                                Paper money — resets as the system runs.
                            </div>
                        </div>
                        <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                            <div class="text-[10px] uppercase tracking-wider text-neutral-500">
                                Market right now
                            </div>
                            <div class="text-2xl font-semibold {reg.tone}">{reg.label}</div>
                            <div class="mt-1 text-[11px] text-neutral-500">{reg.meaning}</div>
                        </div>
                        <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                            <div class="text-[10px] uppercase tracking-wider text-neutral-500">
                                Chance of wiping out
                            </div>
                            <div class="text-2xl font-semibold text-white">
                                {fmtPct(briefing.ruin_probability)}
                            </div>
                            <div class="mt-1 text-[11px] text-neutral-500">
                                Lower is safer. The system keeps this near zero.
                            </div>
                        </div>
                        <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                            <div class="text-[10px] uppercase tracking-wider text-neutral-500">
                                Worst-case crash loss
                            </div>
                            <div class="text-2xl font-semibold text-amber-400">
                                {fmtPct(briefing.expected_shortfall_99)}
                            </div>
                            <div class="mt-1 text-[11px] text-neutral-500">
                                Typical loss if a rare bad day hits. Smaller is safer.
                            </div>
                        </div>
                    </div>
                </div>
                <details class="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-5">
                    <summary class="cursor-pointer text-xs font-semibold uppercase tracking-wider text-neutral-400">
                        Technical detail (for the curious)
                    </summary>
                    <ul class="mt-3 space-y-2">
                        {#each briefing.executive_narrative ?? [] as line}
                            <li class="flex gap-2 text-sm text-neutral-400">
                                <span class="text-emerald-500">•</span>{line}
                            </li>
                        {/each}
                    </ul>
                </details>
            {/if}
        {:else if activeTab === "Performance"}
            {#if performance}
                {@const pnl = performance.estimated_pnl_usd ?? 0}
                <div class="mb-4 rounded-xl border border-neutral-800 bg-neutral-950 p-4 text-sm text-neutral-300">
                    The system has placed <b class="text-white">{performance.total_paper_fills}</b>
                    simulated trades. Its safety gate blocked
                    <b class="text-red-400">{performance.rejected_by_gate}</b> that were too risky.
                    On paper you're
                    <b class={pnl >= 0 ? "text-emerald-400" : "text-red-400"}
                        >{pnl >= 0 ? "up" : "down"} {fmtUsd(Math.abs(pnl))}</b
                    >, from <b class="text-emerald-400">{fmtUsd(performance.estimated_premium_collected_usd)}</b>
                    of option premium minus <b class="text-red-400">{fmtUsd(performance.total_costs_usd)}</b> in trading costs.
                    <span class="text-amber-300/80">(Estimated, paper money — not real returns.)</span>
                </div>
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                        <div class="text-[10px] uppercase tracking-wider text-neutral-500">Account value (paper)</div>
                        <div class="text-2xl font-semibold text-white">{fmtUsd(performance.estimated_equity_usd)}</div>
                    </div>
                    <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                        <div class="text-[10px] uppercase tracking-wider text-neutral-500">Profit so far (paper)</div>
                        <div class="text-2xl font-semibold {pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}">{fmtUsd(pnl)}</div>
                    </div>
                    <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                        <div class="text-[10px] uppercase tracking-wider text-neutral-500">Trades placed</div>
                        <div class="text-2xl font-semibold text-white">{performance.total_paper_fills}</div>
                    </div>
                    <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                        <div class="text-[10px] uppercase tracking-wider text-neutral-500">Risky trades blocked</div>
                        <div class="text-2xl font-semibold {performance.rejected_by_gate > 0 ? 'text-red-400' : 'text-white'}">{performance.rejected_by_gate}</div>
                    </div>
                </div>

                <div class="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-5">
                    <h4 class="mb-1 text-sm font-semibold text-white">Account value over time (paper)</h4>
                    <p class="mb-3 text-[11px] text-neutral-500">Each step is one analysis cycle. Up = the system is collecting more than it's paying.</p>
                    {#if sparkPoints}
                        <svg viewBox="0 0 600 120" class="w-full">
                            <polyline fill="none" stroke={sparkUp ? "#10b981" : "#ef4444"} stroke-width="2" points={sparkPoints} />
                        </svg>
                    {:else}
                        <p class="text-sm text-neutral-500">No trades yet — press “Run analysis now”.</p>
                    {/if}
                    <div class="mt-2 flex flex-wrap justify-between gap-2 text-xs text-neutral-500">
                        <span>Premium earned: <span class="text-emerald-400">{fmtUsd(performance.estimated_premium_collected_usd)}</span></span>
                        <span>Costs paid: <span class="text-red-400">{fmtUsd(performance.total_costs_usd)}</span></span>
                        <span>Safety cash frozen: <span class="text-amber-400">{fmtUsd(performance.reserves_locked_usd)}</span></span>
                    </div>
                </div>

                <div class="mt-4 rounded-xl border border-neutral-800 bg-neutral-950 p-5">
                    <h4 class="mb-3 text-sm font-semibold text-white">Recent activity</h4>
                    {#if (performance.recent_activity ?? []).length === 0}
                        <p class="text-sm text-neutral-500">No trades yet.</p>
                    {:else}
                        <ul class="space-y-2">
                            {#each performance.recent_activity as t}
                                <li class="flex flex-wrap items-center gap-2 rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm">
                                    <span class="rounded px-2 py-0.5 text-xs font-semibold {t.risk_verdict === 'APPROVED' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}">
                                        {t.risk_verdict === "APPROVED" ? "Placed" : "Blocked"}
                                    </span>
                                    <span class="font-semibold text-white">{t.symbol}</span>
                                    <span class="text-neutral-400">{t.structure === "SHORT_PUT" ? "sold a put (insurance)" : t.structure === "IRON_CONDOR" ? "sold a spread" : t.structure === "CASH_LONG" ? "bought spot" : t.structure}</span>
                                    <span class="text-neutral-300">{fmtUsd(Number(t.notional_usd))}</span>
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </div>
            {/if}
        {:else if activeTab === "Markets"}
            <p class="mb-4 text-sm text-neutral-400">
                Live prices and the system's current read on each market. Click a market to
                see its candlestick chart with the system's stance labelled on it.
            </p>
            <!-- Market selector list -->
            <div class="mb-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
                {#each markets as m}
                    <button
                        onclick={() => loadCandles(m.symbol)}
                        class="rounded-xl border p-4 text-left transition {selectedSymbol === m.symbol
                            ? 'border-blue-500 bg-blue-500/5'
                            : 'border-neutral-800 bg-neutral-950 hover:border-neutral-700'}"
                    >
                        <div class="flex items-center justify-between">
                            <span class="text-lg font-bold text-white">{m.symbol}</span>
                            <span class="text-[9px] uppercase tracking-wider text-neutral-600"
                                >{m.source === "synthetic" ? "demo data" : m.source}</span
                            >
                        </div>
                        <div class="mt-1 text-xl font-semibold text-neutral-200">
                            {m.last?.toLocaleString("en-US", { style: "currency", currency: "USD" })}
                        </div>
                        <div class="mt-1 text-xs {regimeTone(m.regime)}">{m.stance}</div>
                    </button>
                {/each}
                {#if markets.length === 0}
                    <p class="text-sm text-neutral-500">Loading markets…</p>
                {/if}
            </div>

            <!-- Candlestick chart -->
            <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
                <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <h4 class="text-sm font-semibold text-white">
                        {selectedSymbol} · last {candleData?.candles?.length ?? 0} bars
                        {#if candleData?.source}<span class="text-[10px] text-neutral-600"> ({candleData.source === "synthetic" ? "demo data" : "real data"})</span>{/if}
                    </h4>
                    {#if candleData}
                        <span class="rounded px-2 py-0.5 text-xs font-semibold {regimeTone(candleData.regime)} bg-neutral-900 border border-neutral-800">
                            System view: {candleData.stance}
                        </span>
                    {/if}
                </div>
                {#if candlesLoading}
                    <p class="text-sm text-neutral-500">Loading chart…</p>
                {:else if chart}
                    <svg viewBox={`0 0 ${chart.w} ${chart.h}`} class="w-full">
                        <!-- price axis labels -->
                        <text x={chart.w - chart.padR + 6} y="14" class="fill-neutral-500" font-size="11">{chart.max.toLocaleString()}</text>
                        <text x={chart.w - chart.padR + 6} y={chart.h - 24} class="fill-neutral-500" font-size="11">{chart.min.toLocaleString()}</text>
                        <!-- last price line + label -->
                        <line x1={chart.padL} y1={chart.yLast} x2={chart.w - chart.padR} y2={chart.yLast} stroke="#3b82f6" stroke-width="1" stroke-dasharray="3 3" opacity="0.6" />
                        <text x={chart.w - chart.padR + 6} y={chart.yLast + 4} class="fill-blue-400" font-size="11" font-weight="600">{chart.last.toLocaleString()}</text>
                        <!-- candles -->
                        {#each chart.bars as b}
                            <line x1={b.x} y1={b.wickTop} x2={b.x} y2={b.wickBot} stroke={b.up ? "#10b981" : "#ef4444"} stroke-width="1" />
                            <rect x={b.x - chart.bodyW / 2} y={b.bodyTop} width={chart.bodyW} height={b.bodyH} fill={b.up ? "#10b981" : "#ef4444"} />
                        {/each}
                        <!-- signal marker on the latest candle -->
                        {#if chart.bars.length}
                            {@const lb = chart.bars[chart.bars.length - 1]}
                            <polygon points={`${lb.x - 5},${lb.wickTop - 8} ${lb.x + 5},${lb.wickTop - 8} ${lb.x},${lb.wickTop - 2}`} fill="#facc15" />
                        {/if}
                    </svg>
                    <p class="mt-2 text-[11px] text-neutral-500">
                        ▲ marks the latest bar, where the system's current read applies.
                        Green = up bar, red = down bar.
                    </p>
                {:else}
                    <p class="text-sm text-neutral-500">No chart data.</p>
                {/if}
            </div>
        {:else if activeTab === "Allocation"}
            <p class="mb-4 text-sm text-neutral-400">
                How the system is using the money it's working with, split by job. (Amounts are
                cumulative across trades, not your cash balance.)
            </p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                {#each allocation as a}
                    <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
                        <div class="mb-3 text-lg font-bold text-white">{a.asset}</div>
                        <div class="space-y-3 text-sm">
                            <div>
                                <div class="flex justify-between">
                                    <span class="text-neutral-300">Earning income</span>
                                    <span class="text-emerald-400">{fmtUsd(a.yield_generation_usd)}</span>
                                </div>
                                <div class="text-[11px] text-neutral-500">Options sold to collect premium.</div>
                            </div>
                            <div>
                                <div class="flex justify-between">
                                    <span class="text-neutral-300">Safety reserve</span>
                                    <span class="text-amber-400">{fmtUsd(a.loss_reserve_usd)}</span>
                                </div>
                                <div class="text-[11px] text-neutral-500">Cash frozen to cover a bad move.</div>
                            </div>
                            <div>
                                <div class="flex justify-between">
                                    <span class="text-neutral-300">Price hedge</span>
                                    <span class="text-sky-400">{fmtUsd(a.delta_hedge_usd)}</span>
                                </div>
                                <div class="text-[11px] text-neutral-500">Spot held to cancel out price direction.</div>
                            </div>
                        </div>
                    </div>
                {/each}
                {#if allocation.length === 0}
                    <p class="text-sm text-neutral-500">Nothing allocated yet — press “Run analysis now”.</p>
                {/if}
            </div>
        {:else if activeTab === "Intelligence"}
            <p class="mb-4 text-sm text-neutral-400">
                How big outside events ripple through markets into your portfolio, and the math
                models the system relies on.
            </p>
            {#if macro?.links?.length}
                <div class="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
                    <h4 class="mb-1 text-sm font-semibold text-white">Knock-on effects</h4>
                    <p class="mb-3 text-[11px] text-neutral-500">
                        Read each row left-to-right: a change in the first thing pushes on the next,
                        and so on into your portfolio. “Credibility” = how reliable that chain is.
                    </p>
                    <ul class="space-y-2 text-sm">
                        {#each macro.links as l}
                            <li class="flex flex-wrap items-center gap-2">
                                <span class="font-mono text-xs text-amber-300">{l.source.replace(/_/g, " ")}</span>
                                <span class="text-neutral-600">→</span>
                                <span class="font-mono text-xs text-sky-300">{l.channel.replace(/_/g, " ")}</span>
                                <span class="text-neutral-600">→</span>
                                <span class="font-mono text-xs text-emerald-300">{l.target.replace(/_/g, " ")}</span>
                                <span class="ml-auto text-xs {l.credibility > 0.7 ? 'text-emerald-400' : 'text-amber-400'}">
                                    {(l.credibility * 100).toFixed(0)}% reliable
                                </span>
                            </li>
                        {/each}
                    </ul>
                </div>
            {/if}
            <div class="mt-4 overflow-hidden rounded-xl border border-neutral-800">
                <table class="w-full text-left text-sm">
                    <thead class="bg-neutral-900 text-neutral-400">
                        <tr>
                            <th class="px-4 py-3 font-medium">Model</th>
                            <th class="px-4 py-3 font-medium">What it figures out</th>
                            <th class="px-4 py-3 font-medium">Why it's trusted</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-neutral-800 bg-neutral-950">
                        <tr>
                            <td class="px-4 py-3 font-semibold text-white">EVT</td>
                            <td class="px-4 py-3 text-neutral-300">How bad a rare crash could get</td>
                            <td class="px-4 py-3 text-neutral-400">Honest about rare disasters; sets the safety reserve.</td>
                        </tr>
                        <tr>
                            <td class="px-4 py-3 font-semibold text-white">HMM</td>
                            <td class="px-4 py-3 text-neutral-300">What mood the market is in</td>
                            <td class="px-4 py-3 text-neutral-400">Spots a shift in the market before prices confirm it.</td>
                        </tr>
                        <tr>
                            <td class="px-4 py-3 font-semibold text-white">GARCH</td>
                            <td class="px-4 py-3 text-neutral-300">How wild prices will swing next</td>
                            <td class="px-4 py-3 text-neutral-400">Sets a fair price for the 'insurance' the system sells.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        {/if}
    </main>

    {#if showMoney}
        <div class="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4">
            <div class="w-full max-w-sm rounded-2xl border border-neutral-700 bg-neutral-950 p-6">
                <h3 class="mb-1 text-lg font-semibold text-white">
                    {moneyKind === "deposit" ? "Add money (paper)" : "Withdraw (paper)"}
                </h3>
                <p class="mb-4 text-xs text-neutral-500">
                    {moneyKind === "deposit"
                        ? "Adds to your simulated balance. No real money is moved."
                        : "Takes from free cash only — frozen safety reserves are protected. Real-money withdrawals are done manually at your broker, by design."}
                </p>
                <label class="mb-1 block text-[10px] uppercase tracking-wider text-neutral-500"
                    >Amount (USD)</label
                >
                <input
                    bind:value={moneyAmount}
                    type="number"
                    min="0"
                    placeholder="e.g. 10000"
                    class="mb-3 w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-white"
                />
                {#if moneyMsg}<p class="mb-3 text-xs text-red-400">{moneyMsg}</p>{/if}
                <div class="flex gap-2">
                    <button
                        onclick={submitMoney}
                        disabled={moneyBusy}
                        class="flex-1 rounded-lg bg-emerald-600 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-40"
                    >
                        {moneyBusy
                            ? "Working…"
                            : moneyKind === "deposit"
                              ? "Add money"
                              : "Withdraw"}
                    </button>
                    <button
                        onclick={() => (showMoney = false)}
                        class="rounded-lg border border-neutral-700 px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-800"
                        >Cancel</button
                    >
                </div>
            </div>
        </div>
    {/if}
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
