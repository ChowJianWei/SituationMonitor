<script lang="ts">
    import { onMount } from "svelte";

    // Watchlist State
    let watchlist = $state<string[]>(["NVDA", "AAPL", "MSFT"]);
    let emailInput = $state("");
    let subStatus = $state<"idle" | "success">("idle");

    // Color convention toggle:
    // "intl" -> Green Up / Red Down (US Style)
    // "cn" -> Red Up / Green Down (China Style)
    let colorScheme = $state<"intl" | "cn">("intl");

    // Ticker lookup / detailed view state
    let selectedTicker = $state<string | null>(null);
    let chartTimeframe = $state<"1D" | "1W" | "1M">("1D");

    // Alert settings state
    let alerts = $state<{ symbol: string; threshold: number; type: "above" | "below" }[]>([
        { symbol: "NVDA", threshold: 130, type: "above" },
        { symbol: "AAPL", threshold: 170, type: "below" }
    ]);
    let newAlertSymbol = $state("");
    let newAlertThreshold = $state("");
    let newAlertType = $state<"above" | "below">("above");
    let aiNewsPush = $state(true);

    // Heatmap data
    const sectors = [
        {
            name: "Technology (科技)",
            stocks: [
                { symbol: "NVDA", name: "英伟达", price: 124.50, change: 1.49 },
                { symbol: "AAPL", name: "苹果", price: 181.25, change: -0.99 },
                { symbol: "MSFT", name: "微软", price: 415.80, change: 0.52 },
                { symbol: "GOOGL", name: "谷歌", price: 172.40, change: -1.25 },
                { symbol: "AVGO", name: "博通", price: 1395.20, change: 2.10 },
                { symbol: "AMD", name: "超威半导体", price: 161.40, change: 3.40 }
            ]
        },
        {
            name: "Financials (金融)",
            stocks: [
                { symbol: "JPM", name: "摩根大通", price: 198.10, change: 1.12 },
                { symbol: "BAC", name: "美国银行", price: 39.45, change: 0.45 },
                { symbol: "MS", name: "摩根士丹利", price: 92.20, change: -0.20 },
                { symbol: "GS", name: "高盛集团", price: 442.80, change: 1.85 },
                { symbol: "WFC", name: "富国银行", price: 57.10, change: -0.10 }
            ]
        },
        {
            name: "Consumer & Retail (消费零售)",
            stocks: [
                { symbol: "AMZN", name: "亚马逊", price: 189.35, change: 1.35 },
                { symbol: "WMT", name: "沃尔玛", price: 68.25, change: 0.25 },
                { symbol: "TGT", name: "塔吉特", price: 145.88, change: -0.88 },
                { symbol: "HD", name: "家得宝", price: 348.60, change: 0.60 },
                { symbol: "COST", name: "开市客", price: 825.15, change: 1.15 }
            ]
        },
        {
            name: "Energy & Industry (能源工业)",
            stocks: [
                { symbol: "XOM", name: "埃克森美孚", price: 114.15, change: -2.15 },
                { symbol: "CVX", name: "雪佛龙", price: 154.80, change: -1.80 },
                { symbol: "CAT", name: "卡特彼勒", price: 325.50, change: 0.50 },
                { symbol: "GE", name: "通用电气", price: 164.20, change: 1.20 }
            ]
        }
    ];

    // Detailed stock analytics datasets
    const stockDetailsMap: Record<string, any> = {
        NVDA: {
            pe: "68.4", pb: "32.5", yield: "0.03%", revenueYoY: "+268%", netIncome: "14.88B",
            desc: "NVIDIA Corporation designs graphics processing units (GPUs) for the gaming and professional markets, as well as system on a chip units for the mobile computing and automotive market.",
            candles: [118, 120, 119, 122, 121, 123, 122, 124.5]
        },
        AAPL: {
            pe: "28.2", pb: "38.1", yield: "0.54%", revenueYoY: "-4%", netIncome: "23.64B",
            desc: "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide, and sells various related services.",
            candles: [186, 185, 184, 182, 183, 181.5, 182.2, 181.25]
        },
        MSFT: {
            pe: "36.8", pb: "12.4", yield: "0.72%", revenueYoY: "+17%", netIncome: "21.93B",
            desc: "Microsoft Corporation develops and supports software, services, devices, and solutions worldwide. Its Productivity and Business Processes segment includes Office, Exchange, SharePoint, Microsoft Teams, and LinkedIn.",
            candles: [410, 412, 411, 414, 413, 415, 414, 415.8]
        },
        GOOGL: {
            pe: "25.6", pb: "7.2", yield: "0.46%", revenueYoY: "+15%", netIncome: "23.66B",
            desc: "Alphabet Inc. offers Google Services, Google Cloud, and Other Bets segments. It operates through performance advertising, brand advertising, Google Play, Android, hardware, and YouTube.",
            candles: [175, 174, 176, 173, 174.5, 172.8, 173.5, 172.4]
        }
    };

    // Helper for color styling based on chosen convention:
    // intl: green is positive, red is negative.
    // cn: red is positive, green is negative.
    function getStockColorClass(change: number, type: "bg" | "text" | "border" = "text") {
        const isPositive = change >= 0;
        if (colorScheme === "intl") {
            if (isPositive) {
                return type === "bg" ? "bg-emerald-500/10 text-emerald-400" : type === "border" ? "border-emerald-500/20" : "text-emerald-400";
            } else {
                return type === "bg" ? "bg-red-500/10 text-red-400" : type === "border" ? "border-red-500/20" : "text-red-400";
            }
        } else {
            if (isPositive) {
                return type === "bg" ? "bg-red-500/10 text-red-400" : type === "border" ? "border-red-500/20" : "text-red-400";
            } else {
                return type === "bg" ? "bg-emerald-500/10 text-emerald-400" : type === "border" ? "border-emerald-500/20" : "text-emerald-400";
            }
        }
    }

    function toggleWatchlist(sym: string) {
        if (watchlist.includes(sym)) {
            watchlist = watchlist.filter(s => s !== sym);
        } else {
            watchlist = [...watchlist, sym];
        }
    }

    function addAlert(e: Event) {
        e.preventDefault();
        const price = Number(newAlertThreshold);
        if (newAlertSymbol && price > 0) {
            alerts = [...alerts, { symbol: newAlertSymbol.toUpperCase(), threshold: price, type: newAlertType }];
            newAlertSymbol = "";
            newAlertThreshold = "";
        }
    }

    function removeAlert(index: number) {
        alerts = alerts.filter((_, i) => i !== index);
    }

    function handleSubscribe(e: Event) {
        e.preventDefault();
        if (emailInput.trim()) {
            subStatus = "success";
            setTimeout(() => {
                subStatus = "idle";
                emailInput = "";
            }, 3000);
        }
    }

    // Default detailed payload if clicked item isn't in mock mapping
    function getDetails(sym: string) {
        return stockDetailsMap[sym] || {
            pe: "22.4", pb: "3.5", yield: "1.20%", revenueYoY: "+8%", netIncome: "2.10B",
            desc: `${sym} is listed on S&P 500 under general industrial sectors. Showcasing real-time indicators.`,
            candles: [100, 102, 101, 104, 103, 105, 104, 106]
        };
    }
</script>

<div class="space-y-6 select-none">
    <!-- Platform Intro Header -->
    <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
            <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded font-mono">开源项目</span>
                <span class="text-xs text-neutral-500 font-semibold">• GitHub 6.5k ★</span>
            </div>
            <h1 class="text-xl font-extrabold text-white mt-1">OpenStock 市场平台</h1>
            <p class="text-xs text-neutral-400 mt-1">高效、免费的交易终端替代方案。多维度板块热力图与专业 K 线技术指标聚合看板</p>
        </div>
        <div class="flex gap-2">
            <button 
                onclick={() => colorScheme = colorScheme === "intl" ? "cn" : "intl"}
                class="px-3 py-1.5 rounded bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-300 hover:text-white transition"
            >
                配色约定: {colorScheme === "intl" ? "国际 (绿涨红跌)" : "中国 (红涨绿跌)"}
            </button>
        </div>
    </div>

    <!-- Main Grid Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 1. Heatmap (Left Column) -->
        <div class="lg:col-span-2 bg-neutral-950 border border-neutral-800 rounded-xl p-5">
            <h2 class="text-sm font-extrabold text-white uppercase mb-4 tracking-wider">市场板块热力图 (Sector Heatmap)</h2>
            <div class="space-y-6">
                {#each sectors as sector}
                    <div>
                        <h3 class="text-xs font-bold text-neutral-400 mb-2 border-l-2 border-amber-500 pl-2">{sector.name}</h3>
                        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
                            {#each sector.stocks as stock}
                                <button
                                    onclick={() => selectedTicker = stock.symbol}
                                    class="p-3 bg-neutral-900/60 border rounded-xl text-left transition duration-200 hover:border-neutral-700 hover:bg-neutral-900 flex flex-col justify-between h-20
                                    {getStockColorClass(stock.change, 'border')}"
                                >
                                    <div class="flex justify-between items-start w-full">
                                        <span class="font-bold font-mono text-white text-sm">{stock.symbol}</span>
                                        <span class="text-[10px] text-neutral-500">{stock.name}</span>
                                    </div>
                                    <div class="flex justify-between items-end w-full mt-2">
                                        <span class="text-xs font-mono text-neutral-400">${stock.price.toFixed(2)}</span>
                                        <span class="text-xs font-mono font-bold {getStockColorClass(stock.change)}">
                                            {stock.change > 0 ? "+" : ""}{stock.change}%
                                        </span>
                                    </div>
                                </button>
                            {/each}
                        </div>
                    </div>
                {/each}
            </div>
        </div>

        <!-- 2. Overview & Alert & Digest (Right Column) -->
        <div class="space-y-6">
            <!-- Market Overview Chart -->
            <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-5">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-sm font-bold text-white uppercase">龙头指数 (SPY Overview)</h3>
                    <div class="flex bg-neutral-900 border border-neutral-850 p-0.5 rounded text-[10px] font-bold">
                        {#each ["1D", "1W", "1M"] as tf}
                            <button
                                onclick={() => chartTimeframe = tf as any}
                                class="px-2 py-0.5 rounded {chartTimeframe === tf ? 'bg-amber-500 text-neutral-950' : 'text-neutral-500 hover:text-neutral-300'}"
                            >
                                {tf === "1D" ? "日线" : tf === "1W" ? "周线" : "月线"}
                            </button>
                        {/each}
                    </div>
                </div>
                <div class="w-full h-32 bg-neutral-900 rounded border border-neutral-850 flex flex-col justify-between p-2">
                    <div class="flex justify-between text-[10px] font-mono text-neutral-500">
                        <span>SPY (S&P 500 ETF)</span>
                        <span class="text-emerald-400 font-bold">$510.50 (+0.42%)</span>
                    </div>
                    <!-- K-line mock draw -->
                    <div class="flex-1 flex items-end justify-between px-2 gap-1.5 mt-2">
                        {#each [
                            { o: 40, c: 60, h: 70, l: 30, up: true },
                            { o: 60, c: 50, h: 65, l: 45, up: false },
                            { o: 50, c: 75, h: 80, l: 48, up: true },
                            { o: 75, c: 68, h: 78, l: 65, up: false },
                            { o: 68, c: 85, h: 90, l: 60, up: true },
                            { o: 85, c: 80, h: 88, l: 75, up: false },
                            { o: 80, c: 95, h: 100, l: 78, up: true }
                        ] as bar}
                            <div class="flex-1 flex flex-col items-center justify-end h-full relative">
                                <!-- Wick -->
                                <div class="w-px h-full bg-neutral-800 absolute z-0" style="bottom: {bar.l}%; top: {100 - bar.h}%"></div>
                                <!-- Body -->
                                <div class="w-full z-10 rounded-sm" 
                                     style="height: {Math.abs(bar.c - bar.o)}%; bottom: {Math.min(bar.o, bar.c)}%; 
                                            background-color: {bar.up ? '#10b981' : '#ef4444'}"></div>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>

            <!-- Personalized alerts manager -->
            <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-5">
                <h3 class="text-sm font-bold text-white uppercase mb-3 flex items-center justify-between">
                    <span>价格预警监控</span>
                    <span class="text-[9px] font-normal text-neutral-500 font-mono">Personalized Alerts</span>
                </h3>
                <form onsubmit={addAlert} class="grid grid-cols-3 gap-2 mb-4">
                    <input
                        bind:value={newAlertSymbol}
                        placeholder="代码 (NVDA)"
                        class="bg-neutral-900 border border-neutral-800 rounded px-2 py-1 text-xs text-white uppercase"
                    />
                    <input
                        bind:value={newAlertThreshold}
                        type="number"
                        placeholder="价格 ($)"
                        class="bg-neutral-900 border border-neutral-800 rounded px-2 py-1 text-xs text-white"
                    />
                    <select
                        bind:value={newAlertType}
                        class="bg-neutral-900 border border-neutral-800 rounded px-1 py-1 text-xs text-neutral-300"
                    >
                        <option value="above">大于</option>
                        <option value="below">小于</option>
                    </select>
                    <button type="submit" class="col-span-3 bg-amber-500 text-neutral-950 font-bold py-1.5 rounded text-xs hover:bg-amber-400 transition">
                        添加预警
                    </button>
                </form>

                <!-- Alerts List -->
                <div class="space-y-2 max-h-40 overflow-y-auto pr-1">
                    {#each alerts as alert, index}
                        <div class="flex items-center justify-between p-2 bg-neutral-900/60 border border-neutral-850 rounded-lg text-xs font-mono">
                            <span class="font-bold text-white">{alert.symbol}</span>
                            <span class="text-neutral-400">
                                {alert.type === "above" ? "突破涨至" : "跌穿跌至"} ${alert.threshold}
                            </span>
                            <button onclick={() => removeAlert(index)} class="text-red-400 hover:text-red-300 transition">删除</button>
                        </div>
                    {/each}
                </div>

                <!-- AI pushing -->
                <div class="mt-4 pt-3 border-t border-neutral-850 flex items-center justify-between">
                    <div class="flex flex-col">
                        <span class="text-xs font-bold text-white">异动 AI 自动推送</span>
                        <span class="text-[9px] text-neutral-500">检测到异常波动时邮件通知</span>
                    </div>
                    <input type="checkbox" bind:checked={aiNewsPush} class="w-4 h-4 text-amber-500 accent-amber-500 rounded border-neutral-800 bg-neutral-900" />
                </div>
            </div>

            <!-- Daily Newsletter digest -->
            <div class="bg-gradient-to-tr from-sky-950/20 to-neutral-950 border border-neutral-800 rounded-xl p-5 relative overflow-hidden">
                <div class="absolute inset-0 bg-radial-gradient from-sky-500/5 to-transparent"></div>
                <div class="relative z-10">
                    <h3 class="text-sm font-bold text-white uppercase mb-2">每日市场早报订阅</h3>
                    <p class="text-[11px] text-neutral-400 mb-4 leading-relaxed">
                        每天股市收盘后，由大模型AI自动提炼全市场涨跌异动、自选股新闻摘要及突发流动性报告，发送到您的邮箱。
                    </p>
                    {#if subStatus === "success"}
                        <p class="text-xs font-bold text-sky-400 text-center py-2 bg-sky-500/10 border border-sky-500/20 rounded">
                            ✓ 订阅成功！早报将于明日起发送。
                        </p>
                    {:else}
                        <form onsubmit={handleSubscribe} class="flex gap-2">
                            <input
                                bind:value={emailInput}
                                type="email"
                                required
                                placeholder="输入您的邮箱"
                                class="flex-1 bg-neutral-900 border border-neutral-800 rounded px-2.5 py-1.5 text-xs text-white"
                            />
                            <button type="submit" class="bg-sky-500 hover:bg-sky-400 text-neutral-950 font-bold px-3 py-1.5 rounded text-xs transition">
                                订阅
                            </button>
                        </form>
                    {/if}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- ========================================== -->
<!-- INDIVIDUAL STOCK DETAIL OVERVIEW (个股分析) -->
<!-- ========================================== -->
{#if selectedTicker}
    {@const info = getDetails(selectedTicker)}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm">
        <div class="w-full max-w-4xl bg-neutral-950 rounded-2xl border border-neutral-800 p-6 relative shadow-2xl overflow-y-auto max-h-[90vh]">
            <button onclick={() => selectedTicker = null} class="absolute top-4 right-4 text-neutral-500 hover:text-white transition">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>

            <!-- Ticker Header -->
            <div class="flex justify-between items-start mb-6 border-b border-neutral-850 pb-4">
                <div>
                    <div class="flex items-center gap-3">
                        <h3 class="text-xl font-extrabold text-white font-mono">{selectedTicker}</h3>
                        <span class="px-2 py-0.5 text-[10px] font-bold rounded bg-neutral-900 border border-neutral-800 text-neutral-400">NASDAQ 上市</span>
                        <button 
                            onclick={() => toggleWatchlist(selectedTicker!)}
                            class="px-2.5 py-0.5 text-[10px] font-bold rounded transition border
                                {watchlist.includes(selectedTicker) 
                                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' 
                                    : 'bg-neutral-900 text-neutral-500 border-neutral-800 hover:text-neutral-300'}"
                        >
                            {watchlist.includes(selectedTicker) ? "★ 已收藏" : "☆ 收藏自选"}
                        </button>
                    </div>
                    <p class="text-xs text-neutral-400 mt-2 max-w-xl">{info.desc}</p>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- 1. Technical chart and indicators (Left side) -->
                <div class="lg:col-span-2 space-y-4">
                    <div class="bg-neutral-900 border border-neutral-850 p-4 rounded-xl">
                        <div class="flex justify-between text-xs mb-3 text-neutral-400">
                            <span class="font-bold text-white">TradingView 专业图表</span>
                            <span class="font-mono">MACD & RSI 加载完成</span>
                        </div>
                        
                        <!-- Drawing candles -->
                        <div class="w-full h-56 bg-neutral-950 rounded border border-neutral-900 p-2 relative flex flex-col justify-between">
                            <svg viewBox="0 0 400 120" class="w-full h-full" preserveAspectRatio="none">
                                <!-- Draw curve grid -->
                                <line x1="0" y1="30" x2="400" y2="30" stroke="#1f2937" stroke-width="0.5" stroke-dasharray="2 2" />
                                <line x1="0" y1="60" x2="400" y2="60" stroke="#1f2937" stroke-width="0.5" stroke-dasharray="2 2" />
                                <line x1="0" y1="90" x2="400" y2="90" stroke="#1f2937" stroke-width="0.5" stroke-dasharray="2 2" />
                                <!-- MA 20 Indicator Line -->
                                <polyline fill="none" stroke="#eab308" stroke-width="1" stroke-dasharray="1 1"
                                    points={info.candles.map((c: number, i: number) => {
                                        const x = 20 + (i / 7) * 360;
                                        const y = 80 - (c - Math.min(...info.candles)) * 2.5;
                                        return `${x},${y}`;
                                    }).join(" ")}
                                />
                                <!-- Candle bars -->
                                {#each info.candles as c, i}
                                    {@const x = 20 + (i / 7) * 360}
                                    {@const y = 80 - (c - Math.min(...info.candles)) * 2.5}
                                    {@const height = Math.max(3, (c % 10) * 2)}
                                    <line x1={x} y1={y - height} x2={x} y2={y + height} stroke={i % 2 === 0 ? '#10b981' : '#ef4444'} stroke-width="1.5" />
                                    <rect x={x - 4} y={y - height / 2} width="8" height={height} fill={i % 2 === 0 ? '#10b981' : '#ef4444'} />
                                {/each}
                            </svg>
                        </div>
                    </div>

                    <!-- Tech indicators (MACD / RSI) mockups -->
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-neutral-900 border border-neutral-850 p-3 rounded-xl">
                            <span class="text-[10px] text-neutral-500 uppercase font-bold block">MACD 震荡指标</span>
                            <div class="h-10 flex items-end gap-1 mt-2">
                                {#each Array(15) as _, i}
                                    <div class="flex-1 bg-red-500/40 rounded-sm" style="height: {Math.abs(Math.sin(i)) * 100}%"></div>
                                {/each}
                            </div>
                        </div>
                        <div class="bg-neutral-900 border border-neutral-850 p-3 rounded-xl">
                            <span class="text-[10px] text-neutral-500 uppercase font-bold block">RSI (14) 强弱度</span>
                            <div class="h-10 flex items-center justify-between mt-2 font-mono">
                                <span class="text-xs text-neutral-300">指标数值: </span>
                                <span class="text-sm font-bold text-amber-400">58.45</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 2. Financial data reports (Right side) -->
                <div class="bg-neutral-900 border border-neutral-850 p-5 rounded-xl flex flex-col justify-between">
                    <div>
                        <h4 class="text-xs text-neutral-400 font-bold uppercase border-b border-neutral-800 pb-2 mb-4">财务数据面板 (Financial Reports)</h4>
                        <div class="space-y-4 font-mono text-xs">
                            <div class="flex justify-between border-b border-neutral-850/50 pb-2">
                                <span class="text-neutral-500">静态市盈率 (P/E)</span>
                                <span class="text-white font-bold">{info.pe}</span>
                            </div>
                            <div class="flex justify-between border-b border-neutral-850/50 pb-2">
                                <span class="text-neutral-500">市净率 (P/B)</span>
                                <span class="text-white font-bold">{info.pb}</span>
                            </div>
                            <div class="flex justify-between border-b border-neutral-850/50 pb-2">
                                <span class="text-neutral-500">股息红利率</span>
                                <span class="text-white font-bold">{info.yield}</span>
                            </div>
                            <div class="flex justify-between border-b border-neutral-850/50 pb-2">
                                <span class="text-neutral-500">营业收入同比</span>
                                <span class="text-red-400 font-bold">{info.revenueYoY}</span>
                            </div>
                            <div class="flex justify-between border-b border-neutral-850/50 pb-2">
                                <span class="text-neutral-500">单季净利润</span>
                                <span class="text-white font-bold">{info.netIncome}</span>
                            </div>
                        </div>
                    </div>

                    <div class="mt-6">
                        <button onclick={() => selectedTicker = null} class="w-full bg-amber-500 hover:bg-amber-400 text-neutral-950 font-bold py-2 rounded text-xs transition">
                            返回列表
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
{/if}
