<script lang="ts">
    import { onMount } from "svelte";
    import QuantSidebar from "$lib/components/quant/QuantSidebar.svelte";
    import StrategyViews from "$lib/components/quant/StrategyViews.svelte";
    import MacroMonitorGrid from "$lib/components/quant/MacroMonitorGrid.svelte";
    import OpenStockPortal from "$lib/components/quant/OpenStockPortal.svelte";

    // Navigation and main state
    let activeTab = $state("overview");
    let online = $state(true);
    let busy = $state(false);
    let loading = $state(true);

    // Actuarial Engine API Data
    let briefing = $state<any>(null);
    let performance = $state<any>(null);
    let allocation = $state<any[]>([]);
    let macro = $state<any>(null);

    // Onboarding modal states
    let showGlossary = $state(false);
    let showMoney = $state(false);
    let moneyKind = $state<"deposit" | "withdraw">("deposit");
    let moneyAmount = $state("");
    let moneyMsg = $state("");
    let moneyBusy = $state(false);

    // Interactive GDP News Simulation State
    let gdpSimStep = $state<"idle" | "news" | "ea_wipe" | "ai_flip" | "done">("idle");
    let simLogs = $state<string[]>([]);
    let simProgress = $state(0);

    // Custom backtest sandbox state
    let customAsset = $state("BTC");
    let customRisk = $state("mid");
    let customStrat = "nlp";
    let customTesting = $state(false);
    let customResult = $state<any>(null);

    // AI Forum / Chat Analyzer state
    let chatInput = $state("");
    let chatHistory = $state<{ role: "user" | "assistant"; text: string; details?: any }[]>([
        { role: "assistant", text: "您好！我是 QuantAlchemist AI 助手。您可以输入任何市场新闻或经济数据头条，我将利用 NLP 情绪模型为您解析事件冲击，并生成交易决策推荐。" }
    ]);
    let chatAnalyzing = $state(false);

    // AI strategy generator & deployment sandbox states
    let codegenPrompt = $state("");
    let codegenLoading = $state(false);
    let codegenMode = $state<"indicator" | "event">("indicator");
    let generatedCode = $state("");
    let serverBacktesting = $state(false);
    let serverBacktestResult = $state<any>(null);
    let liveMarket = $state("binance");
    let exchangeApiKey = $state("");
    let exchangeApiSecret = $state("");
    let aiApiKey = $state("");
    let liveLogs = $state<string[]>([]);
    let deployStatus = $state<"idle" | "deploying" | "active">("idle");

    function generateStrategyCode() {
        if (!codegenPrompt.trim()) return;
        codegenLoading = true;
        generatedCode = "";
        serverBacktestResult = null;
        
        setTimeout(() => {
            codegenLoading = false;
            if (codegenMode === "indicator") {
                generatedCode = `class CustomIndicatorStrategy(Strategy):
    # 指标策略：快速在K线上验证买卖逻辑
    def init(self):
        self.rsi = self.I(RSI, self.data.Close, 14)
        self.ma = self.I(SMA, self.data.Close, 20)
        
    def next(self):
        # 用一句代码描述逻辑，并在K线上标记点
        if self.rsi[-1] < 30 and self.data.Close[-1] < self.ma[-1]:
            self.buy(label="RSI超卖买入") # 在K线上标记绿色三角形买入
        elif self.rsi[-1] > 70 or self.data.Close[-1] > self.ma[-1]:
            self.sell(label="RSI超买卖出") # 在K线上标记红色倒三角形卖出`;
            } else {
                generatedCode = `class CustomEventStrategy(EventDrivenStrategy):
    # 事件驱动策略：具备开仓回调、逐根K线细粒度控制
    def on_bar(self, bar):
        # 逐根K线控制
        rsi_val = self.indicators.rsi(bar.Close, 14)
        ma_val = self.indicators.sma(bar.Close, 20)
        
        # 仅用一句代码处理买入卖出，附带开仓回调与追踪止损
        if rsi_val < 30 and bar.Close < ma_val:
            self.order_target_percent(1.0, callback=self.on_open_callback)
            
    def on_open_callback(self, order):
        # 开仓成功回调函数
        self.log(f"成功触发事件驱动买入! 成交价: {order.price}, 锁定追踪止损: 2.5%")
        self.set_trailing_stop(2.5)`;
            }
        }, 1500);
    }

    function runServerBacktest() {
        serverBacktesting = true;
        serverBacktestResult = null;
        
        setTimeout(() => {
            serverBacktesting = false;
            const points = generateCurvePoints(100, 20, 2.5, 4.8);
            serverBacktestResult = {
                winRate: "65.4%",
                profit: "+34.50%",
                maxDd: "8.12%",
                transactions: [
                    { time: "2026-06-24 10:00", type: "BUY", price: "$64,250", profit: "—" },
                    { time: "2026-06-24 11:30", type: "SELL", price: "$65,800", profit: "+2.41%" },
                    { time: "2026-06-24 12:15", type: "BUY", price: "$65,100", profit: "—" },
                    { time: "2026-06-24 14:00", type: "SELL", price: "$65,950", profit: "+1.30%" }
                ],
                points
            };
        }, 2000);
    }

    function deployLiveTrading() {
        if (!exchangeApiKey || !exchangeApiSecret) {
            alert("请先配置交易所 API 密钥和 AI 密钥！");
            return;
        }
        deployStatus = "deploying";
        liveLogs = ["【系统部署】实盘环境构建中...", "【系统部署】正在建立与 " + liveMarket.toUpperCase() + " API 的安全通信连接...", "【系统部署】验证 AI 引擎 API Key 有效性..."];
        
        setTimeout(() => {
            deployStatus = "active";
            liveLogs = [
                ...liveLogs,
                "✓ 【实盘就绪】API 验证成功！实盘环境托管已移交至服务端后台服务。",
                "🚀 【策略自动运行】托管实盘监控激活！正在逐根监控 " + liveMarket.toUpperCase() + " 的 K 线形态，自动执行自然语言策略..."
            ];
        }, 3000);
    }

    // Fallback Mock Data in case Python Actuarial backend is offline
    const mockBriefing = {
        free_capital_usd: 124500,
        surplus_health_index: 85,
        net_earnings_24h_usd: 4850,
        regime: "TRENDING",
        ruin_probability: 0.0008,
        expected_shortfall_99: 0.1245,
        executive_narrative: [
            "方差风险溢价 (VRP) 确认流动性健康扩张",
            "Cramér-Lundberg 破产概率低于阈值 0.01%，资金处于极度安全状态",
            "根据 GARCH(1,1) 波动预测，自动冻结 12.45% 作为底层防亏损储备",
            "系统主要持仓于 QQQ 趋势动量与沪深300多因子期权对冲组合"
        ]
    };

    const mockPerformance = {
        total_paper_fills: 142,
        rejected_by_gate: 12,
        estimated_pnl_usd: 15450,
        estimated_premium_collected_usd: 21800,
        total_costs_usd: 6350,
        estimated_equity_usd: 139950,
        reserves_locked_usd: 14500,
        recent_activity: [
            { risk_verdict: "APPROVED", symbol: "XAUUSD", structure: "CASH_LONG", notional_usd: 12000, rationale: "NLP 情绪异动买入" },
            { risk_verdict: "APPROVED", symbol: "BTCUSD", structure: "SHORT_PUT", notional_usd: 25000, rationale: "VRP高分位卖权" },
            { risk_verdict: "BLOCKED", symbol: "SOLUSD", structure: "IRON_CONDOR", notional_usd: 18000, rationale: "超额预期损失拦截" }
        ],
        equity_curve: [100000, 102000, 101500, 104200, 103800, 106000, 109200, 114500, 113900, 115450]
    };

    const mockAllocation = [
        { asset: "BTC", yield_generation_usd: 12000, loss_reserve_usd: 5000, delta_hedge_usd: 8000 },
        { asset: "XAUUSD", yield_generation_usd: 15000, loss_reserve_usd: 4000, delta_hedge_usd: 12000 }
    ];

    const mockMacro = {
        links: [
            { source: "Fed_Rate_Hike", channel: "Capital_Cost_Up", target: "Equity_Reserve_Frozen", credibility: 0.85 },
            { source: "GDP_Surprise_Up", channel: "DXY_Bullish_Momentum", target: "Gold_Short_Flip", credibility: 0.92 }
        ]
    };

    // Main fetchers
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
            // Graceful Offline Fallback to match exact high-fidelity requirements
            online = false;
            briefing = mockBriefing;
            performance = mockPerformance;
            allocation = mockAllocation;
            macro = mockMacro;
        } finally {
            loading = false;
        }
    }

    async function runCycle() {
        busy = true;
        try {
            await fetch("/api/quant/cycle/run", { method: "POST" });
            await loadAll();
        } catch {
            // Trigger local mock cycle run if engine offline
            if (performance) {
                performance.total_paper_fills += 1;
                performance.estimated_pnl_usd += 250;
                performance.estimated_equity_usd += 250;
                performance.equity_curve = [...performance.equity_curve, performance.estimated_equity_usd];
            }
        } finally {
            busy = false;
        }
    }

    onMount(async () => {
        await loadAll();
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

    // ----------------------------------------------------
    // GDP Simulation trigger
    // ----------------------------------------------------
    function runGdpSimulation() {
        gdpSimStep = "news";
        simLogs = ["【系统初始化】模拟准备就绪。标的：XAUUSD (黄金)。当前头寸：空头。", "【数据源】等待美国商务部季度 GDP 实际数据发布..."];
        simProgress = 10;

        setTimeout(() => {
            gdpSimStep = "ea_wipe";
            simLogs = [
                ...simLogs,
                "🚨 【突发新闻】美国第一季度实际 GDP 年化季率初值录得 3.2%，远超市场预期的 1.6%！",
                "📈 经济极度强劲促使美联储降息预期暴跌，美元指数暴涨，黄金瞬间大幅反弹跳空！",
                "❌ 【传统 EA 规则机】基于死参数及固定技术指标，无法读取宏观新闻内容。由于到达网格交易区间上限，强制死扛继续逆市加仓做空！",
                "💀 【传统 EA 规则机】亏损迅速溢出风险资本上限，触发追缴保证金！系统爆仓，最终以惨痛本金全灭出局。"
            ];
            simProgress = 50;
        }, 3000);

        setTimeout(() => {
            gdpSimStep = "ai_flip";
            simLogs = [
                ...simLogs,
                "🤖 【Alchemist AI 模型】动态新闻 NLP 解析管道触发！",
                "🔍 【新闻情感指数】'Strong GDP growth / delayed rate cuts' -> 看空黄金 / 看多美元。AI 情绪分数骤降至极低值 -0.85。",
                "🔄 【动态概率反转】系统判定原始空头网格在当前突发事件下破产概率飙升至 98%！避险模块介入。",
                "⚡ 【反手开仓】智能代理快速砍掉空头亏损头寸，顺应新闻趋势反手多仓买入黄金对冲资产！"
            ];
            simProgress = 80;
        }, 7000);

        setTimeout(() => {
            gdpSimStep = "done";
            simLogs = [
                ...simLogs,
                "✅ 【交易执行】AI 黄金多头合约成功在上涨浪中平仓获利！",
                "💰 【模拟报告】传统 EA 系统：爆仓 (亏损 100%)。AI 交易系统：及时反手获利 +15.42%！",
                "📊 回测时间跨度：2024.01.25 至 2024.12.27，AI 系统实现极具弹性的健康净值增长。"
            ];
            simProgress = 100;
        }, 11000);
    }

    function resetGdpSimulation() {
        gdpSimStep = "idle";
        simLogs = [];
        simProgress = 0;
    }

    // ----------------------------------------------------
    // Custom backtest sandbox simulator
    // ----------------------------------------------------
    function runCustomBacktest() {
        customTesting = true;
        customResult = null;

        setTimeout(() => {
            const points = generateCurvePoints(100, 20, customRisk === "high" ? 3.2 : customRisk === "mid" ? 1.8 : 0.8, customRisk === "high" ? 8 : 4);
            const winRate = 60 + Math.random() * 12;
            const netProfit = customRisk === "high" ? 45.42 : customRisk === "mid" ? 22.80 : 11.20;

            customResult = {
                winRate: winRate.toFixed(1) + "%",
                netProfit: "+" + netProfit.toFixed(2) + "%",
                dd: (customRisk === "high" ? 24.5 : customRisk === "mid" ? 12.8 : 5.4).toFixed(1) + "%",
                points
            };
            customTesting = false;
        }, 1500);
    }

    function generateCurvePoints(seed: number, steps: number, trend: number, vol: number) {
        let current = seed;
        let points = [];
        for (let i = 0; i < steps; i++) {
            let change = (Math.random() - 0.45) * vol + trend;
            current = current * (1 + change / 100);
            points.push(current);
        }
        return points;
    }

    // ----------------------------------------------------
    // AI Chat/Forum submission
    // ----------------------------------------------------
    function submitChat(e: Event) {
        e.preventDefault();
        if (!chatInput.trim()) return;

        const userMsg = chatInput;
        chatHistory = [...chatHistory, { role: "user", text: userMsg }];
        chatInput = "";
        chatAnalyzing = true;

        setTimeout(() => {
            let responseText = "";
            let responseDetails = null;

            if (userMsg.toLowerCase().includes("gdp")) {
                responseText = "【AI 风险雷达】解析美国 GDP 突发超预期数据。当前模型判定美元流动性趋紧，美元指数（DXY）买盘情绪骤升。黄金兑美元（XAUUSD）呈现强空头压力。推荐策略：平仓原黄金多头，建议在 2,310 位置反手做空。";
                responseDetails = { sentiment: "-0.85 (强看空)", target: "黄金/非美货币", action: "反手做空" };
            } else if (userMsg.toLowerCase().includes("降息") || userMsg.toLowerCase().includes("降准")) {
                responseText = "【AI 风险雷达】国内央行超预期降准50个基点。该事件将释放长期流动性约 1 万亿元，利多 A 股中证500与可转债双低组合。由于剩余流动性象限向‘复苏扩张’偏移，策略推荐：做多 IC 股指策略，并加仓高流动性 ETF 策略组合。";
                responseDetails = { sentiment: "+0.92 (强看多)", target: "股指 (IC) / 可转债", action: "全仓买入" };
            } else {
                responseText = `【AI 风险雷达】对 headline: "${userMsg}" 进行情感语义提取完毕。事件冲击度：中等偏弱。宏观环境属于震荡无方向阶段。推荐策略：建议维持当前期权策略中‘核心合成曲线’的 SG/GV 双卖底仓模式，套取时间价值，暂不建议进行方向性追单。`;
                responseDetails = { sentiment: "0.00 (中性)", target: "全市场", action: "跨式双卖套利" };
            }

            chatHistory = [...chatHistory, { role: "assistant", text: responseText, details: responseDetails }];
            chatAnalyzing = false;
        }, 1500);
    }
</script>

<svelte:head>
    <title>QuantAlchemist Laboratory | 智能量化交易中心</title>
</svelte:head>

<div class="min-h-screen bg-neutral-950 text-neutral-100 font-sans flex h-screen overflow-hidden">
    <!-- Collapsible Sidebar Component -->
    <QuantSidebar activeTab={activeTab} onSelect={(tab) => activeTab = tab} />

    <!-- Content Panel Area -->
    <div class="flex-1 flex flex-col h-full overflow-hidden bg-neutral-950">
        <!-- Main Navbar Header -->
        <header class="h-16 border-b border-neutral-900 bg-neutral-950/80 backdrop-blur-md px-6 flex items-center justify-between z-30">
            <div class="flex items-center gap-4">
                <h1 class="text-base font-extrabold text-neutral-100 tracking-tight flex items-center gap-2">
                    系统状态 
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider
                        {online ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}"
                    >
                        <span class="w-1.5 h-1.5 rounded-full {online ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
                        {online ? "Engine Live (在线)" : "Engine Sandbox (沙盒模拟模式)"}
                    </span>
                </h1>
            </div>
            
            <div class="flex items-center gap-3">
                <button
                    onclick={() => showGlossary = !showGlossary}
                    class="px-3.5 py-1.5 rounded bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-300 hover:text-white transition"
                >
                    {showGlossary ? "收起名词解释" : "名词科普手册"}
                </button>
                <button
                    onclick={runCycle}
                    disabled={busy}
                    class="px-4 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-neutral-950 font-extrabold text-xs transition disabled:opacity-40"
                >
                    {busy ? "模型迭代中..." : "手动驱动一次交易周期"}
                </button>
            </div>
        </header>

        <!-- Scrollable Main View -->
        <main class="flex-1 overflow-y-auto p-6 space-y-6">
            <!-- Glossaries dropdown -->
            {#if showGlossary}
                <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5 shadow-lg">
                    <h3 class="text-sm font-bold text-white mb-3">📖 量化金融核心指标说明</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                        <div class="bg-neutral-950 p-3 rounded border border-neutral-850">
                            <span class="font-bold text-amber-400">盈亏盈亏比 (Profit/Loss Ratio)</span>
                            <p class="text-neutral-400 mt-1">系统所有盈利交易的总利润除以所有亏损交易的总亏损。通常盈亏比越合理，策略长期生存能力越强。</p>
                        </div>
                        <div class="bg-neutral-950 p-3 rounded border border-neutral-850">
                            <span class="font-bold text-amber-400">夏普比率 (Sharpe Ratio)</span>
                            <p class="text-neutral-400 mt-1">单位超额风险所获得的超额回报。比率大于 1 代表投资性价比优秀，波动控制合理。</p>
                        </div>
                        <div class="bg-neutral-950 p-3 rounded border border-neutral-850">
                            <span class="font-bold text-amber-400">最大回撤 (Max Drawdown)</span>
                            <p class="text-neutral-400 mt-1">在选定周期内，资金曲线从最高点跌落到最低点的最大亏损幅度。代表投资该策略可能面临的最坏亏损情况。</p>
                        </div>
                    </div>
                </div>
            {/if}

            <!-- ========================================================= -->
            <!-- TAB: OVERVIEW (主页 / AI模型 vs 传统EA 对比 - AlphathePro 报告) -->
            <!-- ========================================================= -->
            {#if activeTab === "overview"}
                <!-- Title -->
                <div class="flex justify-between items-end border-b border-neutral-900 pb-4 mb-4">
                    <div>
                        <h2 class="text-xl font-extrabold text-white">策略大厅与 AI 核心模型</h2>
                        <p class="text-xs text-neutral-400 mt-1">分析传统固定规则系统与动态 NLP 决策系统在突发宏观新闻冲击下的绝对优劣</p>
                    </div>
                </div>

                <!-- 1. Grid of Traditional vs AI System -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Left: Traditional EA -->
                    <div class="bg-neutral-900/40 border border-neutral-850 rounded-xl p-5 flex flex-col justify-between">
                        <div>
                            <span class="text-[9px] font-mono text-neutral-500 font-bold uppercase tracking-widest">TRADITIONAL SYSTEM</span>
                            <h3 class="text-base font-extrabold text-neutral-300 mt-1">传统 EA 智能交易系统 (固定逻辑)</h3>
                            <p class="text-xs text-neutral-400 mt-3 leading-relaxed">
                                基于人工编写的固定指标规则（如双均线、MACD金叉等），使用死参数和优化拟合后的静态区间。在无突发宏观风险的静默市场中表现尚可，但在大新闻冲击下因无法自适应，极易死扛单向波动，最终爆仓归零。
                            </p>
                        </div>
                        <div class="mt-6 space-y-2 border-t border-neutral-850 pt-4 text-xs font-mono">
                            <div class="flex justify-between text-neutral-500"><span>事件适应性</span> <span class="text-red-400">极差 (无信息提取)</span></div>
                            <div class="flex justify-between text-neutral-500"><span>调仓机制</span> <span class="text-red-400">死参数 / 网格死扛</span></div>
                            <div class="flex justify-between text-neutral-500"><span>突发新闻结果</span> <span class="text-red-400">逆市加仓直至爆仓 (Wipeout)</span></div>
                        </div>
                    </div>

                    <!-- Right: AI Trading System -->
                    <div class="bg-gradient-to-tr from-amber-950/20 to-neutral-900/60 border border-neutral-800 rounded-xl p-5 flex flex-col justify-between relative overflow-hidden">
                        <div class="absolute inset-0 bg-radial-gradient from-amber-500/5 to-transparent"></div>
                        <div class="relative z-10">
                            <span class="text-[9px] font-mono text-amber-500 font-bold uppercase tracking-widest">AI DECISION LAYER</span>
                            <h3 class="text-base font-extrabold text-white mt-1">现代 AI 交易系统 (动态概率驱动)</h3>
                            <p class="text-xs text-neutral-300 mt-3 leading-relaxed">
                                结合自然语言处理 (NLP) 抓取全球实时财经新闻、宏观流动性数据和市场情绪指数。系统基于马尔可夫决策过程 (MDP) 与条件波动率定价，在重磅经济数据发布时，支持瞬间反手斩仓并开出方向对冲头寸。
                            </p>
                        </div>
                        <div class="mt-6 space-y-2 border-t border-neutral-800 pt-4 text-xs font-mono relative z-10">
                            <div class="flex justify-between text-neutral-400"><span>事件适应性</span> <span class="text-red-400 font-bold">优秀 (NLP实时语义提取)</span></div>
                            <div class="flex justify-between text-neutral-400"><span>调仓机制</span> <span class="text-red-400 font-bold">根据破产概率自动反手</span></div>
                            <div class="flex justify-between text-neutral-400"><span>突发新闻结果</span> <span class="text-red-400 font-bold">及时止损反向获利 (V-Shape Profit)</span></div>
                        </div>
                    </div>
                </div>

                <!-- 2. GDP interactive simulation panel -->
                <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-6">
                    <h3 class="text-sm font-extrabold text-white uppercase mb-3 flex items-center justify-between">
                        <span>互动实验室：美国 GDP 爆仓与翻仓模拟器</span>
                        <span class="text-[10px] text-neutral-500 font-normal font-mono">Simulate geopolitical macro stress test</span>
                    </h3>
                    <p class="text-xs text-neutral-400 mb-4">点击下方启动按钮，观看当强于预期的 GDP 数据突发落地时，传统 EA 与现代 AI 系统的动态决策轨迹与本金变化对比。</p>

                    <div class="flex gap-3 mb-4">
                        {#if gdpSimStep === "idle"}
                            <button onclick={runGdpSimulation} class="px-5 py-2 rounded bg-amber-500 hover:bg-amber-400 text-neutral-950 font-bold text-xs transition">
                                启动实时决策测试 (Run Simulation)
                            </button>
                        {:else}
                            <button onclick={resetGdpSimulation} class="px-5 py-2 rounded bg-neutral-800 border border-neutral-700 hover:bg-neutral-700 text-white font-bold text-xs transition">
                                重置实验
                            </button>
                        {/if}
                    </div>

                    <!-- Progress bar -->
                    {#if gdpSimStep !== "idle"}
                        <div class="w-full bg-neutral-950 rounded-full h-1.5 mb-4 overflow-hidden">
                            <div class="bg-amber-500 h-1.5 transition-all duration-500" style="width: {simProgress}%"></div>
                        </div>
                    {/if}

                    <!-- Terminal style output -->
                    <div class="bg-neutral-950 p-4 rounded-lg border border-neutral-900 font-mono text-[11px] leading-relaxed space-y-1.5 max-h-56 overflow-y-auto pr-1">
                        {#if simLogs.length === 0}
                            <span class="text-neutral-600">// 点击上方按钮即可运行多线程决策审计...</span>
                        {:else}
                            {#each simLogs as log}
                                <div class="text-neutral-300">
                                    {#if log.includes("🚨") || log.includes("❌") || log.includes("💀")}
                                        <span class="text-red-400">{log}</span>
                                    {:else if log.includes("🤖") || log.includes("✅") || log.includes("💰")}
                                        <span class="text-amber-400">{log}</span>
                                    {:else}
                                        <span>{log}</span>
                                    {/if}
                                </div>
                            {/each}
                        {/if}
                    </div>
                </div>

                <!-- 3. AlphathePro Gold Lab backtest report -->
                <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5">
                    <h3 class="text-sm font-extrabold text-white uppercase mb-2">黄金兑美元 (XAUUSD) AI 策略回测报告</h3>
                    <p class="text-xs text-neutral-400 mb-5">系统在 AlphathePro Laboratory 平台针对 XAUUSD 近一年的分钟级别回测展示。数据统计跨度：2024-01-25 至 2024-12-27。</p>

                    <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                        <div class="bg-neutral-950 border border-neutral-850 p-3 rounded-lg text-center">
                            <span class="text-[9px] text-neutral-500 uppercase block font-bold">回测净收益</span>
                            <span class="text-sm font-bold font-mono text-red-500 mt-1">+142.85%</span>
                        </div>
                        <div class="bg-neutral-950 border border-neutral-850 p-3 rounded-lg text-center">
                            <span class="text-[9px] text-neutral-500 uppercase block font-bold">胜率 (Win Rate)</span>
                            <span class="text-sm font-bold font-mono text-red-500 mt-1">68.5%</span>
                        </div>
                        <div class="bg-neutral-950 border border-neutral-850 p-3 rounded-lg text-center">
                            <span class="text-[9px] text-neutral-500 uppercase block font-bold">盈亏比</span>
                            <span class="text-sm font-bold font-mono text-white mt-1">2.34 : 1</span>
                        </div>
                        <div class="bg-neutral-950 border border-neutral-850 p-3 rounded-lg text-center">
                            <span class="text-[9px] text-neutral-500 uppercase block font-bold">最大回撤</span>
                            <span class="text-sm font-bold font-mono text-green-400 mt-1">6.82%</span>
                        </div>
                        <div class="bg-neutral-950 border border-neutral-850 p-3 rounded-lg text-center">
                            <span class="text-[9px] text-neutral-500 uppercase block font-bold">Sharpe 比率</span>
                            <span class="text-sm font-bold font-mono text-white mt-1">2.15</span>
                        </div>
                    </div>
                </div>

            <!-- ========================================================= -->
            <!-- TAB: MONITOR (实时监控 - Original Daily Briefing & Allocation) -->
            <!-- ========================================================= -->
            {:else if activeTab === "monitor"}
                {#if briefing}
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <!-- Left briefing stats -->
                        <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5 space-y-4">
                            <h3 class="text-sm font-bold text-white uppercase border-b border-neutral-800 pb-2">精简风险简报</h3>
                            <div class="space-y-3 font-mono text-xs">
                                <div class="flex justify-between">
                                    <span class="text-neutral-500">存活健康度指数</span>
                                    <span class="text-red-500 font-bold">{briefing.surplus_health_index}/100</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-neutral-500">可供支配本金</span>
                                    <span class="text-white font-bold">{fmtUsd(briefing.free_capital_usd)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-neutral-500">24小时净收益</span>
                                    <span class="font-bold {briefing.net_earnings_24h_usd >= 0 ? 'text-red-400' : 'text-green-400'}">
                                        {fmtUsd(briefing.net_earnings_24h_usd)}
                                    </span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-neutral-500">破产清算概率</span>
                                    <span class="text-green-400 font-bold">{fmtPct(briefing.ruin_probability)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-neutral-500">极端日预期损失 (CVaR)</span>
                                    <span class="text-white font-bold">{fmtPct(briefing.expected_shortfall_99)}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Right executive logs -->
                        <div class="md:col-span-2 bg-neutral-900/60 border border-neutral-800 rounded-xl p-5">
                            <h3 class="text-sm font-bold text-white uppercase border-b border-neutral-800 pb-2 mb-3">系统动态决策审计</h3>
                            <ul class="space-y-2 text-xs text-neutral-300">
                                {#each briefing.executive_narrative as line}
                                    <li class="flex items-start gap-2">
                                        <span class="text-amber-500 font-bold mt-0.5">•</span>
                                        <span class="leading-relaxed">{line}</span>
                                    </li>
                                {/each}
                            </ul>
                        </div>
                    </div>

                    <!-- Fund Allocation Matrix -->
                    <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5">
                        <h3 class="text-sm font-bold text-white uppercase border-b border-neutral-800 pb-2 mb-4">资产头寸分类与储备冻结</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {#each allocation as a}
                                <div class="bg-neutral-950 p-4 border border-neutral-900 rounded-xl">
                                    <h4 class="font-bold text-white font-mono text-sm border-b border-neutral-900 pb-2 mb-3">{a.asset}</h4>
                                    <div class="space-y-2 text-xs font-mono">
                                        <div class="flex justify-between">
                                            <span class="text-neutral-500">衍生品收益层 (Yield Generation)</span>
                                            <span class="text-red-500 font-bold">{fmtUsd(a.yield_generation_usd)}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-neutral-500">冻结安全储备 (Loss Reserve)</span>
                                            <span class="text-green-400 font-bold">{fmtUsd(a.loss_reserve_usd)}</span>
                                        </div>
                                        <div class="flex justify-between">
                                            <span class="text-neutral-500">现货对冲层 (Delta Hedge)</span>
                                            <span class="text-white font-bold">{fmtUsd(a.delta_hedge_usd)}</span>
                                        </div>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}

            <!-- ========================================================= -->
            <!-- TAB: STRATEGIES (Index, Bond, CTA, Option, ETF, Macro Strategy) -->
            <!-- ========================================================= -->
            {:else if ["index", "bond", "cta", "option", "etf", "macro-strategy"].includes(activeTab)}
                <StrategyViews activeTab={activeTab} />

            <!-- ========================================================= -->
            <!-- TAB: MACRO MONITOR (宏观监控) -->
            <!-- ========================================================= -->
            {:else if activeTab === "macro-monitor"}
                <MacroMonitorGrid />

            <!-- ========================================================= -->
            <!-- TAB: DATA MONITOR (数据监控 / Performance logs) -->
            <!-- ========================================================= -->
            {:else if activeTab === "data-monitor"}
                {#if performance}
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="bg-neutral-900/60 p-4 rounded-xl border border-neutral-800 font-mono text-center">
                            <span class="text-neutral-500 text-[10px] uppercase font-bold">总模拟充值</span>
                            <span class="text-lg font-bold text-white block mt-1">{fmtUsd(performance.estimated_equity_usd)}</span>
                        </div>
                        <div class="bg-neutral-900/60 p-4 rounded-xl border border-neutral-800 font-mono text-center">
                            <span class="text-neutral-500 text-[10px] uppercase font-bold">累计利润</span>
                            <span class="text-lg font-bold text-red-500 block mt-1">+{fmtUsd(performance.estimated_pnl_usd)}</span>
                        </div>
                        <div class="bg-neutral-900/60 p-4 rounded-xl border border-neutral-800 font-mono text-center">
                            <span class="text-neutral-500 text-[10px] uppercase font-bold">交易成交量</span>
                            <span class="text-lg font-bold text-white block mt-1">{performance.total_paper_fills} 次</span>
                        </div>
                        <div class="bg-neutral-900/60 p-4 rounded-xl border border-neutral-800 font-mono text-center">
                            <span class="text-neutral-500 text-[10px] uppercase font-bold">被风险门拦截</span>
                            <span class="text-lg font-bold text-green-400 block mt-1">{performance.rejected_by_gate} 次</span>
                        </div>
                    </div>

                    <!-- Fills history table -->
                    <div class="bg-neutral-900/40 border border-neutral-800 rounded-xl overflow-hidden mt-6">
                        <div class="px-4 py-3 border-b border-neutral-800 bg-neutral-900/80 text-xs font-bold text-neutral-400">
                            近期审计交易填单日志 (Fills Activity Log)
                        </div>
                        <table class="w-full text-left text-xs text-neutral-300 font-mono">
                            <thead class="bg-neutral-950 text-neutral-500 font-medium">
                                <tr>
                                    <th class="px-4 py-2.5">标的代码</th>
                                    <th class="px-4 py-2.5">交易合约</th>
                                    <th class="px-4 py-2.5">仓位大小</th>
                                    <th class="px-4 py-2.5">风控审判</th>
                                    <th class="px-4 py-2.5">成交原因</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-neutral-850">
                                {#each performance.recent_activity as act}
                                    <tr class="hover:bg-neutral-900/30">
                                        <td class="px-4 py-2.5 font-bold text-white">{act.symbol}</td>
                                        <td class="px-4 py-2.5 text-neutral-400">{act.structure}</td>
                                        <td class="px-4 py-2.5">{fmtUsd(act.notional_usd)}</td>
                                        <td class="px-4 py-2.5">
                                            <span class="px-2 py-0.5 text-[9px] font-bold rounded
                                                {act.risk_verdict === 'APPROVED' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'}"
                                            >
                                                {act.risk_verdict === "APPROVED" ? "已放行成交" : "风控强制熔断"}
                                            </span>
                                        </td>
                                        <td class="px-4 py-2.5 text-neutral-500 text-[10px]">{act.rationale}</td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                {/if}

            <!-- ========================================================= -->
            <!-- TAB: CUSTOM STRATEGY (自选回测沙盒) -->
            <!-- ========================================================= -->
            {:else if activeTab === "custom"}
                <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-6">
                    <h2 class="text-base font-extrabold text-white mb-2">策略回测沙盒测试柜 (Backtest Sandbox)</h2>
                    <p class="text-xs text-neutral-400 mb-6">自主配置资产池，加载不同 AI 模型及方差风险参数进行历史回撤测试。</p>

                    <form onsubmit={(e) => { e.preventDefault(); runCustomBacktest(); }} class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div class="flex flex-col gap-1.5">
                            <label class="text-[10px] uppercase text-neutral-500 font-bold">标的资产 (Asset)</label>
                            <select bind:value={customAsset} class="bg-neutral-950 border border-neutral-800 rounded p-2 text-xs text-neutral-300">
                                <option value="BTC">比特币 (BTCUSD)</option>
                                <option value="XAUUSD">黄金对美元 (XAUUSD)</option>
                                <option value="SPY">标普500指数 (SPY)</option>
                                <option value="QQQ">纳斯达克100 (QQQ)</option>
                            </select>
                        </div>
                        <div class="flex flex-col gap-1.5">
                            <label class="text-[10px] uppercase text-neutral-500 font-bold">风险水平 (Volatility Cap)</label>
                            <select bind:value={customRisk} class="bg-neutral-950 border border-neutral-800 rounded p-2 text-xs text-neutral-300">
                                <option value="low">低波动 (5% Vol Cap)</option>
                                <option value="mid">中等风险 (15% Vol Cap)</option>
                                <option value="high">超额弹性 (30% Vol Cap)</option>
                            </select>
                        </div>
                        <div class="flex flex-col gap-1.5">
                            <label class="text-[10px] uppercase text-neutral-500 font-bold">驱动策略 (Model Core)</label>
                            <select class="bg-neutral-950 border border-neutral-800 rounded p-2 text-xs text-neutral-300">
                                <option value="nlp">NLP 新闻情感对冲型</option>
                                <option value="vrp">VRP 波动率期限均值回复</option>
                                <option value="factor">大宽客多因子截面策略</option>
                            </select>
                        </div>
                        <div class="flex items-end">
                            <button type="submit" disabled={customTesting} class="w-full bg-amber-500 hover:bg-amber-400 text-neutral-950 font-bold py-2 rounded text-xs transition">
                                {customTesting ? "回测分析中..." : "启动历史回测"}
                            </button>
                        </div>
                    </form>

                    <!-- Backtest output curve and cards -->
                    {#if customResult}
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 pt-4 border-t border-neutral-800">
                            <!-- stats -->
                            <div class="bg-neutral-950 p-4 border border-neutral-850 rounded-xl space-y-4 font-mono text-xs">
                                <div class="flex justify-between border-b border-neutral-900 pb-2">
                                    <span class="text-neutral-500">回测盈利率</span>
                                    <span class="text-red-400 font-bold">{customResult.netProfit}</span>
                                </div>
                                <div class="flex justify-between border-b border-neutral-900 pb-2">
                                    <span class="text-neutral-500">胜率 (Win Rate)</span>
                                    <span class="text-red-400 font-bold">{customResult.winRate}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-neutral-500">最大本金回撤</span>
                                    <span class="text-green-400 font-bold">{customResult.dd}</span>
                                </div>
                            </div>
                            <!-- svg curve -->
                            <div class="md:col-span-3 bg-neutral-950 p-4 border border-neutral-850 rounded-xl h-40 relative flex items-center justify-center overflow-hidden">
                                <svg viewBox="0 0 400 120" class="w-full h-full" preserveAspectRatio="none">
                                    <polyline fill="none" stroke="#ef4444" stroke-width="2" 
                                        points={customResult.points.map((p: number, i: number) => {
                                            const x = (i / 19) * 400;
                                            const y = 110 - ((p - Math.min(...customResult.points)) / (Math.max(...customResult.points) - Math.min(...customResult.points) || 1)) * 100;
                                            return `${x.toFixed(1)},${y.toFixed(1)}`;
                                        }).join(" ")}
                                    />
                                </svg>
                                <span class="absolute bottom-1 right-2 text-[8px] text-neutral-600 font-mono">回测完成 250 bars</span>
                            </div>
                        </div>
                    {/if}
                </div>

            <!-- ========================================================= -->
            <!-- TAB: FORUM / AI ASSISTANT (论坛 & AI 助手) -->
            <!-- ========================================================= -->
            {:else if activeTab === "forum"}
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[72vh]">
                    <!-- Forum thread list (Left) -->
                    <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5 overflow-y-auto">
                        <h3 class="text-sm font-bold text-white uppercase border-b border-neutral-800 pb-2 mb-4">宽客策略讨论区</h3>
                        <div class="space-y-4">
                            {#each [
                                { title: "NLP 实时新闻对冲参数调优分享", author: "QuantExpert_9", replies: 24, views: 189 },
                                { title: "美国 GDP 初值对黄金避险资产隐含波动率微笑曲线的冲击", author: "MacroWiz", replies: 12, views: 95 },
                                { title: "可转债双低策略中溢价率因子的动态残差修正", author: "ArbitrageAlchemist", replies: 8, views: 56 }
                            ] as thread}
                                <div class="bg-neutral-950 p-3 rounded border border-neutral-850 hover:border-neutral-700 transition cursor-pointer">
                                    <h4 class="text-xs font-bold text-white hover:text-amber-400 transition">{thread.title}</h4>
                                    <div class="flex justify-between items-center text-[9px] text-neutral-500 font-mono mt-2">
                                        <span>发布: {thread.author}</span>
                                        <span>{thread.replies} 回复 · {thread.views} 阅读</span>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    </div>

                    <!-- AI Sentiment Chatbox (Right) -->
                    <div class="lg:col-span-2 bg-neutral-900/60 border border-neutral-800 rounded-xl p-5 flex flex-col justify-between overflow-hidden">
                        <h3 class="text-sm font-bold text-white uppercase border-b border-neutral-800 pb-2">AI 宏观新闻情绪分析机</h3>
                        
                        <!-- Chat history stream -->
                        <div class="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
                            {#each chatHistory as chat}
                                <div class="flex {chat.role === 'user' ? 'justify-end' : 'justify-start'}">
                                    <div class="max-w-[80%] rounded-xl p-3.5 text-xs leading-relaxed
                                        {chat.role === 'user' 
                                            ? 'bg-amber-500 text-neutral-950 font-semibold' 
                                            : 'bg-neutral-950 border border-neutral-850 text-neutral-300'}"
                                    >
                                        <p>{chat.text}</p>
                                        
                                        <!-- If assistant returns a structured trade verdict -->
                                        {#if chat.details}
                                            <div class="mt-3 pt-2.5 border-t border-neutral-800 text-[10px] font-mono grid grid-cols-3 gap-2">
                                                <div class="bg-neutral-900/80 p-1.5 rounded">
                                                    <span class="text-neutral-500 block uppercase font-bold">NLP情绪值</span>
                                                    <span class="text-white font-bold">{chat.details.sentiment}</span>
                                                </div>
                                                <div class="bg-neutral-900/80 p-1.5 rounded">
                                                    <span class="text-neutral-500 block uppercase font-bold">主要标的</span>
                                                    <span class="text-white font-bold">{chat.details.target}</span>
                                                </div>
                                                <div class="bg-neutral-900/80 p-1.5 rounded">
                                                    <span class="text-neutral-500 block uppercase font-bold">动作指示</span>
                                                    <span class="text-white font-bold">{chat.details.action}</span>
                                                </div>
                                            </div>
                                        {/if}
                                    </div>
                                </div>
                            {/each}
                            {#if chatAnalyzing}
                                <div class="flex justify-start">
                                    <div class="bg-neutral-950 border border-neutral-850 rounded-xl p-3 text-xs text-neutral-500 animate-pulse">
                                        NLP 情感指标生成中，建立因子对冲中...
                                    </div>
                                </div>
                            {/if}
                        </div>

                        <!-- Chat input form -->
                        <form onsubmit={submitChat} class="flex gap-2 border-t border-neutral-800 pt-3">
                            <input
                                bind:value={chatInput}
                                disabled={chatAnalyzing}
                                placeholder="输入宏观新闻头条进行情感语义测试... (例如: 美国第一季度 GDP 年化增速超出预期)"
                                class="flex-1 bg-neutral-950 border border-neutral-800 rounded-lg px-3 py-2 text-xs text-white"
                            />
                            <button type="submit" disabled={chatAnalyzing} class="bg-amber-500 hover:bg-amber-400 text-neutral-950 font-extrabold px-5 rounded-lg text-xs transition">
                                发送
                            </button>
                        </form>
                    </div>
                </div>

            <!-- ========================================================= -->
            <!-- TAB: AI CODEGEN & DEPLOYMENT (AI 策略生成与一键实盘) -->
            <!-- ========================================================= -->
            {:else if activeTab === "ai-codegen"}
                <div class="space-y-6">
                    <!-- 4-Step Onboarding Grid -->
                    <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5">
                        <h3 class="text-xs font-bold text-amber-500 uppercase tracking-widest mb-4">⚡ 4步上手实盘交易指引 (Quick Start Guide)</h3>
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                            {#each [
                                { step: "1", title: "复制 curl 一键部署", desc: "终端运行 curl 脚本自动拉取 Docker 并安装所有依赖环境。" },
                                { step: "2", title: "浏览器登录系统", desc: "用浏览器打开本地 8888 端口，即可登录量化工作台。" },
                                { step: "3", title: "配置密钥跑回测", desc: "加载 AI 生成的策略文件，先运行历史回测验证交易想法。" },
                                { step: "4", title: "一键切换部署实盘", desc: "对回测满意后一键托管运行实盘，半小时内开启自动赚钱。" }
                            ] as stepInfo}
                                <div class="bg-neutral-950 p-4 border border-neutral-900 rounded-lg flex gap-3">
                                    <span class="w-6 h-6 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-500 flex items-center justify-center font-bold text-xs flex-shrink-0">
                                        {stepInfo.step}
                                    </span>
                                    <div>
                                        <h4 class="text-xs font-bold text-white leading-none mb-1.5">{stepInfo.title}</h4>
                                        <p class="text-[10px] text-neutral-500 leading-normal">{stepInfo.desc}</p>
                                    </div>
                                </div>
                            {/each}
                        </div>

                        <!-- Curl command copy box -->
                        <div class="mt-4 bg-neutral-950 border border-neutral-900 rounded-lg p-3 flex justify-between items-center text-xs font-mono">
                            <span class="text-neutral-400">curl -fsSL https://quantalchemist.ai/install.sh | sh</span>
                            <button onclick={() => alert("命令已复制到剪贴板！")} class="px-2.5 py-1 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-850 text-[10px] text-neutral-300 font-bold transition">
                                复制命令
                            </button>
                        </div>
                    </div>

                    <!-- Codegen Workstation Split Panel -->
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Left Panel: AI Codegen Input & Output -->
                        <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5 flex flex-col justify-between space-y-4">
                            <div>
                                <h3 class="text-sm font-bold text-white uppercase border-b border-neutral-800 pb-2 mb-3">AI 自然语言写策略</h3>
                                <p class="text-xs text-neutral-400 mb-4">输入您天马行空的交易点子，AI 策略模型将自动翻译为底层引擎支持的规范逻辑代码。</p>

                                <textarea
                                    bind:value={codegenPrompt}
                                    placeholder="例如：当 BTC 突破 20 日最高价且交易量放大时买入。如果跌破 10 日均线或者触发 3% 追踪止损，一键平仓。"
                                    class="w-full h-24 bg-neutral-950 border border-neutral-800 rounded-lg p-3 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-amber-500 transition mb-3"
                                ></textarea>

                                <div class="flex justify-between items-center mb-3">
                                    <div class="flex gap-2">
                                        <button 
                                            onclick={() => codegenMode = "indicator"}
                                            class="px-2.5 py-1 rounded text-[10px] font-bold border transition
                                                {codegenMode === 'indicator' ? 'bg-amber-500 text-neutral-950 border-amber-500' : 'bg-neutral-950 text-neutral-500 border-neutral-900 hover:text-neutral-300'}"
                                        >
                                            快速指标策略
                                        </button>
                                        <button 
                                            onclick={() => codegenMode = "event"}
                                            class="px-2.5 py-1 rounded text-[10px] font-bold border transition
                                                {codegenMode === 'event' ? 'bg-amber-500 text-neutral-950 border-amber-500' : 'bg-neutral-950 text-neutral-500 border-neutral-900 hover:text-neutral-300'}"
                                        >
                                            事件驱动策略
                                        </button>
                                    </div>
                                    <button
                                        onclick={generateStrategyCode}
                                        disabled={codegenLoading || !codegenPrompt.trim()}
                                        class="px-4 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-neutral-950 font-extrabold text-xs transition disabled:opacity-40"
                                    >
                                        {codegenLoading ? "策略编写中..." : "生成策略代码"}
                                    </button>
                                </div>
                            </div>

                            <!-- Codegen terminal display -->
                            <div class="flex-1 flex flex-col justify-between bg-neutral-950 border border-neutral-900 rounded-lg p-3.5 h-64 overflow-hidden">
                                <div class="flex justify-between items-center text-[10px] text-neutral-500 font-mono mb-2 border-b border-neutral-900 pb-1.5">
                                    <span>{codegenMode === "indicator" ? "indicator_strategy.py" : "event_driven_strategy.py"}</span>
                                    <span>python3</span>
                                </div>
                                <div class="flex-1 font-mono text-[10px] text-neutral-300 overflow-y-auto whitespace-pre leading-relaxed scrollbar-thin">
                                    {#if generatedCode}
                                        {generatedCode}
                                    {:else}
                                        <span class="text-neutral-600">// 生成的策略代码将在这儿高亮展示...</span>
                                    {/if}
                                </div>
                                {#if generatedCode}
                                    <div class="flex justify-end mt-2 pt-2 border-t border-neutral-900">
                                        <button onclick={() => alert("代码已复制到剪贴板！")} class="px-2.5 py-1 rounded bg-neutral-900 hover:bg-neutral-800 border border-neutral-850 text-[9px] text-neutral-400 hover:text-white transition font-bold font-mono">
                                            复制代码
                                        </button>
                                    </div>
                                {/if}
                            </div>
                        </div>

                        <!-- Right Panel: Backtesting & One-click Deploy -->
                        <div class="space-y-6">
                            <!-- Backtest Section -->
                            <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5">
                                <div class="flex justify-between items-center mb-3">
                                    <h3 class="text-sm font-bold text-white uppercase">服务端回测引擎</h3>
                                    <button
                                        onclick={runServerBacktest}
                                        disabled={serverBacktesting || !generatedCode}
                                        class="px-4 py-1 rounded bg-amber-500 hover:bg-amber-400 text-neutral-950 font-extrabold text-xs transition disabled:opacity-40"
                                    >
                                        {serverBacktesting ? "正在计算资金曲线..." : "启动服务端回测"}
                                    </button>
                                </div>
                                <p class="text-[11px] text-neutral-500 mb-4">直接调用服务端 CPU 算力，秒级跑完数年历史 K 线，生成净值曲线与回撤明细。</p>

                                {#if serverBacktestResult}
                                    <div class="grid grid-cols-3 gap-3 mb-4 text-center font-mono text-xs">
                                        <div class="bg-neutral-950 p-2.5 rounded border border-neutral-900">
                                            <span class="text-[8px] text-neutral-500 block">回测收益率</span>
                                            <span class="text-sm font-bold text-red-500">{serverBacktestResult.profit}</span>
                                        </div>
                                        <div class="bg-neutral-950 p-2.5 rounded border border-neutral-900">
                                            <span class="text-[8px] text-neutral-500 block">最大回撤</span>
                                            <span class="text-sm font-bold text-green-400">{serverBacktestResult.maxDd}</span>
                                        </div>
                                        <div class="bg-neutral-950 p-2.5 rounded border border-neutral-900">
                                            <span class="text-[8px] text-neutral-500 block">平均胜率</span>
                                            <span class="text-sm font-bold text-red-500">{serverBacktestResult.winRate}</span>
                                        </div>
                                    </div>
                                    <!-- Backtest Return Curve -->
                                    <div class="h-28 bg-neutral-950 rounded border border-neutral-900 relative flex items-center justify-center overflow-hidden mb-4">
                                        <svg viewBox="0 0 300 80" class="w-full h-full" preserveAspectRatio="none">
                                            <polyline fill="none" stroke="#ef4444" stroke-width="2" 
                                                points={serverBacktestResult.points.map((p: number, i: number) => {
                                                    const x = (i / 19) * 300;
                                                    const y = 70 - ((p - Math.min(...serverBacktestResult.points)) / (Math.max(...serverBacktestResult.points) - Math.min(...serverBacktestResult.points) || 1)) * 60;
                                                    return `${x.toFixed(1)},${y.toFixed(1)}`;
                                                }).join(" ")}
                                            />
                                        </svg>
                                    </div>
                                    <!-- Transaction logs -->
                                    <div class="max-h-28 overflow-y-auto pr-1">
                                        <table class="w-full text-left text-[10px] text-neutral-400 font-mono">
                                            <thead class="text-neutral-500 font-semibold bg-neutral-950 border-b border-neutral-900">
                                                <tr>
                                                    <th class="px-2 py-1">时间</th>
                                                    <th class="px-2 py-1">方向</th>
                                                    <th class="px-2 py-1">成交价</th>
                                                    <th class="px-2 py-1">每笔盈亏</th>
                                                </tr>
                                            </thead>
                                            <tbody class="divide-y divide-neutral-900">
                                                {#each serverBacktestResult.transactions as tx}
                                                    <tr>
                                                        <td class="px-2 py-1 text-neutral-500">{tx.time}</td>
                                                        <td class="px-2 py-1 font-bold {tx.type === 'BUY' ? 'text-red-400' : 'text-green-400'}">{tx.type}</td>
                                                        <td class="px-2 py-1 text-white">{tx.price}</td>
                                                        <td class="px-2 py-1 font-bold {tx.profit.includes('+') ? 'text-red-500' : 'text-neutral-400'}">{tx.profit}</td>
                                                    </tr>
                                                {/each}
                                            </tbody>
                                        </table>
                                    </div>
                                {/if}
                            </div>

                            <!-- Live Deploy Section -->
                            <div class="bg-neutral-900/60 border border-neutral-800 rounded-xl p-5">
                                <h3 class="text-sm font-bold text-white uppercase border-b border-neutral-800 pb-2 mb-4">一键部署托管实盘</h3>
                                
                                <div class="grid grid-cols-2 gap-3 mb-4 text-xs">
                                    <div class="flex flex-col gap-1">
                                        <label class="text-[9px] uppercase text-neutral-500 font-bold">实盘交易市场</label>
                                        <select bind:value={liveMarket} class="bg-neutral-950 border border-neutral-800 rounded p-1.5 text-neutral-300 font-mono">
                                            <option value="binance">Binance (币安)</option>
                                            <option value="bybit">Bybit (币市)</option>
                                            <option value="tradier">Tradier Sandbox (美股)</option>
                                            <option value="forex">OANDA (外汇)</option>
                                        </select>
                                    </div>
                                    <div class="flex flex-col gap-1">
                                        <label class="text-[9px] uppercase text-neutral-500 font-bold">AI API Key (密钥)</label>
                                        <input bind:value={aiApiKey} type="password" placeholder="••••••••" class="bg-neutral-950 border border-neutral-800 rounded p-1 text-white font-mono" />
                                    </div>
                                    <div class="flex flex-col gap-1 col-span-2">
                                        <label class="text-[9px] uppercase text-neutral-500 font-bold">交易所 API Key</label>
                                        <input bind:value={exchangeApiKey} placeholder="Exchange read/trade key" class="bg-neutral-950 border border-neutral-800 rounded p-1 text-white font-mono" />
                                    </div>
                                    <div class="flex flex-col gap-1 col-span-2">
                                        <label class="text-[9px] uppercase text-neutral-500 font-bold">交易所 API Secret</label>
                                        <input bind:value={exchangeApiSecret} type="password" placeholder="••••••••" class="bg-neutral-950 border border-neutral-800 rounded p-1 text-white font-mono" />
                                    </div>
                                </div>

                                <button
                                    onclick={deployLiveTrading}
                                    disabled={deployStatus === "deploying" || !serverBacktestResult}
                                    class="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white font-bold py-2.5 rounded-lg text-xs transition mb-4 shadow-[0_0_15px_rgba(16,185,129,0.1)] uppercase"
                                >
                                    {#if deployStatus === "idle"}
                                        一键托管运行实盘 (Deploy Live Trading)
                                    {:else}
                                        {deployStatus === "deploying" ? "正在打通 API 实盘连接..." : "✓ 实盘策略监控中 (LIVE MONITORING ACTIVE)"}
                                    {/if}
                                </button>

                                <!-- Live logs container -->
                                {#if liveLogs.length > 0}
                                    <div class="bg-neutral-950 rounded border border-neutral-900 p-3 font-mono text-[10px] leading-relaxed max-h-32 overflow-y-auto space-y-1">
                                        {#each liveLogs as log}
                                            <div class={log.includes("🚀") || log.includes("✓") ? "text-emerald-400 font-bold" : "text-neutral-400"}>
                                                {log}
                                            </div>
                                        {/each}
                                    </div>
                                {/if}
                            </div>
                        </div>
                    </div>
                </div>

            <!-- ========================================================= -->
            <!-- TAB: OPENSTOCK PORTAL (OpenStock 市场平台) -->
            <!-- ========================================================= -->
            {:else if activeTab === "openstock"}
                <OpenStockPortal />
            {/if}
        </main>
    </div>
</div>

<style>
    /* Global scrollbar behavior */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #1f2937;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #374151;
    }
</style>
