<script lang="ts">
    import { onMount } from "svelte";
    import { fade } from "svelte/transition";

    interface Props {
        activeTab: string;
    }

    let { activeTab }: Props = $props();

    // Strategy Details Modals
    let activeModal = $state<string | null>(null);

    // Helpers to format currency and percentages in Chinese conventional style:
    // positive returns are colored RED, negative or neutral risk metrics are GREEN/GOLD
    const fmtUsd = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
    const fmtPct = (n: number) => `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;

    // ----------------------------------------------------
    // Curve generators for realistic visual backtests
    // ----------------------------------------------------
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

    // Static curve datasets
    const etfCurve = generateCurvePoints(100, 100, 1.8, 4.5);
    const macroLiquidityCurve = generateCurvePoints(100, 120, 1.2, 3.8);
    const ctaCurve = generateCurvePoints(100, 80, 2.2, 5.0);
    const optionCompositeCurve = generateCurvePoints(100, 90, 1.6, 2.5);
    const bondCurve = generateCurvePoints(100, 70, 0.9, 1.2);

    function svgPoints(curve: number[], width: number, height: number, padding: number) {
        if (curve.length < 2) return "";
        const min = Math.min(...curve);
        const max = Math.max(...curve);
        const span = max - min || 1;
        return curve
            .map((v, i) => {
                const x = padding + (i / (curve.length - 1)) * (width - 2 * padding);
                const y = height - padding - ((v - min) / span) * (height - 2 * padding);
                return `${x.toFixed(1)},${y.toFixed(1)}`;
            })
            .join(" ");
    }
</script>

<div class="space-y-6">
    <!-- ========================================== -->
    <!-- 1. STOCK INDEX STRATEGY (股指策略) -->
    <!-- ========================================== -->
    {#if activeTab === "index"}
        <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-6">
            <div class="flex justify-between items-start mb-6">
                <div>
                    <h2 class="text-xl font-extrabold text-white flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                        股指策略看板 <span class="text-xs text-neutral-500 font-normal">INDEX STRATEGY</span>
                    </h2>
                    <p class="text-xs text-neutral-400 mt-1">实时监控多因子与趋势动量持仓信号，智能算法执行</p>
                </div>
                <div class="flex gap-2">
                    <span class="px-2 py-1 text-[10px] font-bold bg-neutral-900 border border-neutral-800 rounded text-neutral-400">行情：实时</span>
                </div>
            </div>

            <!-- Signal Monitor Grid -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                {#each [
                    { name: "沪深300 (IF)", weight: "多因子", price: "3,842.10", change: 0.85, signal: "做多", time: "09:31:02", pnl: 12450 },
                    { name: "中证500 (IC)", weight: "趋势动量", price: "5,321.40", change: -0.42, signal: "做空", time: "10:15:44", pnl: -3200 },
                    { name: "上证50 (IH)", weight: "多因子", price: "2,410.80", change: 1.12, signal: "做多", time: "09:30:15", pnl: 8900 },
                    { name: "中证1000 (IM)", weight: "量化多头", price: "5,189.60", change: 0.15, signal: "观望", time: "11:02:11", pnl: 0 }
                ] as asset}
                    <div class="bg-neutral-900/60 border border-neutral-850 rounded-xl p-4 flex flex-col justify-between">
                        <div class="flex justify-between items-start">
                            <div>
                                <h4 class="font-bold text-white text-sm">{asset.name}</h4>
                                <span class="text-[10px] text-neutral-500">{asset.weight}</span>
                            </div>
                            <span class="px-2 py-0.5 text-[9px] font-bold rounded 
                                {asset.signal === '做多' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                                 asset.signal === '做空' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 
                                 'bg-neutral-800 text-neutral-400'}"
                            >
                                {asset.signal}
                            </span>
                        </div>
                        <div class="mt-4">
                            <div class="text-xl font-mono font-bold text-white">{asset.price}</div>
                            <div class="flex justify-between text-[11px] mt-1 font-mono">
                                <span class={asset.change >= 0 ? "text-red-400" : "text-green-400"}>
                                    {asset.change >= 0 ? "+" : ""}{asset.change}%
                                </span>
                                <span class="text-neutral-500">更新: {asset.time}</span>
                            </div>
                        </div>
                        <div class="border-t border-neutral-800/80 mt-3 pt-2 flex justify-between items-center text-xs">
                            <span class="text-neutral-400">浮动盈亏</span>
                            <span class="font-mono font-bold {asset.pnl >= 0 ? 'text-red-400' : 'text-green-400'}">
                                {asset.pnl >= 0 ? "+" : ""}{asset.pnl.toLocaleString()} USD
                            </span>
                        </div>
                    </div>
                {/each}
            </div>

            <!-- Signal Table Logs -->
            <div class="bg-neutral-900/40 rounded-xl border border-neutral-850 overflow-hidden">
                <div class="px-4 py-3 border-b border-neutral-850 flex justify-between items-center bg-neutral-900/80">
                    <span class="text-xs font-bold uppercase text-neutral-400">信号变动日志</span>
                    <span class="text-[10px] text-neutral-500">显示最近10条</span>
                </div>
                <table class="w-full text-left text-xs text-neutral-300">
                    <thead class="bg-neutral-950 text-neutral-500 font-medium">
                        <tr>
                            <th class="px-4 py-2.5">时间</th>
                            <th class="px-4 py-2.5">标的</th>
                            <th class="px-4 py-2.5">策略类型</th>
                            <th class="px-4 py-2.5">动作</th>
                            <th class="px-4 py-2.5">执行价</th>
                            <th class="px-4 py-2.5">当前浮盈</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-neutral-850 font-mono">
                        {#each [
                            { t: "2026-06-24 14:02:11", s: "IH 股指主力", p: "多因子核心", a: "开多", pr: "2,410.80", pnl: "+8,900 USD", c: "text-red-400" },
                            { t: "2026-06-24 13:45:22", s: "IF 股指主力", p: "多因子核心", a: "持有多", pr: "3,840.50", pnl: "+12,450 USD", c: "text-red-400" },
                            { t: "2026-06-24 12:10:04", s: "IC 股指主力", p: "动态反向动量", a: "开空", pr: "5,320.10", pnl: "-3,200 USD", c: "text-green-400" },
                            { t: "2026-06-24 10:30:00", s: "IM 股指主力", p: "均值回归", a: "平多观望", pr: "5,190.00", pnl: "0.00 USD", c: "text-neutral-500" }
                        ] as row}
                            <tr class="hover:bg-neutral-900/30">
                                <td class="px-4 py-2 text-neutral-400">{row.t}</td>
                                <td class="px-4 py-2 font-bold text-white">{row.s}</td>
                                <td class="px-4 py-2 text-neutral-400">{row.p}</td>
                                <td class="px-4 py-2 font-bold {row.a.includes('多') ? 'text-red-400' : row.a.includes('空') ? 'text-green-400' : 'text-neutral-400'}">{row.a}</td>
                                <td class="px-4 py-2 text-white">{row.pr}</td>
                                <td class="px-4 py-2 font-bold {row.c}">{row.pnl}</td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {/if}

    <!-- ========================================== -->
    <!-- 2. CONVERTIBLE BOND STRATEGY (可转债策略) -->
    <!-- ========================================== -->
    {#if activeTab === "bond"}
        <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-6">
            <h2 class="text-xl font-extrabold text-white flex items-center gap-2 mb-2">
                可转债策略看板 <span class="text-xs text-neutral-500 font-normal">CONVERTIBLE BOND</span>
            </h2>
            <p class="text-xs text-neutral-400 mb-6">低风险期权不对称套利策略，基于双低策略（低溢价率+低债底价格）及网格算法</p>

            <!-- Metrics -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-neutral-900/60 p-4 rounded-xl border border-neutral-850">
                    <div class="text-neutral-500 text-[10px] uppercase font-bold">累计收益</div>
                    <div class="text-2xl font-bold font-mono text-red-500 mt-1">+167.33%</div>
                </div>
                <div class="bg-neutral-900/60 p-4 rounded-xl border border-neutral-850">
                    <div class="text-neutral-500 text-[10px] uppercase font-bold">年化收益</div>
                    <div class="text-2xl font-bold font-mono text-red-500 mt-1">+11.50%</div>
                </div>
                <div class="bg-neutral-900/60 p-4 rounded-xl border border-neutral-850">
                    <div class="text-neutral-500 text-[10px] uppercase font-bold">夏普比率</div>
                    <div class="text-2xl font-bold font-mono text-white mt-1">0.95</div>
                </div>
                <div class="bg-neutral-900/60 p-4 rounded-xl border border-neutral-850">
                    <div class="text-neutral-500 text-[10px] uppercase font-bold">最大回撤</div>
                    <div class="text-2xl font-bold font-mono text-green-400 mt-1">10.80%</div>
                </div>
            </div>

            <!-- Chart -->
            <div class="bg-neutral-900/40 border border-neutral-850 rounded-xl p-5 mb-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-sm font-bold text-white">资金净值曲线 (双低对冲套利)</h3>
                    <span class="text-[10px] text-neutral-500 font-mono">2018 - 2026</span>
                </div>
                <div class="w-full h-48 bg-neutral-950 rounded border border-neutral-900 flex items-center justify-center relative overflow-hidden">
                    <svg viewBox="0 0 600 120" class="w-full h-full" preserveAspectRatio="none">
                        <polyline fill="none" stroke="#ef4444" stroke-width="2" points={svgPoints(bondCurve, 600, 120, 10)} />
                    </svg>
                </div>
            </div>
        </div>
    {/if}

    <!-- ========================================== -->
    <!-- 3. CTA STRATEGY (CTA策略) -->
    <!-- ========================================== -->
    {#if activeTab === "cta"}
        <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-6">
            <h2 class="text-xl font-extrabold text-white flex items-center gap-2 mb-2">
                CTA 策略看板 <span class="text-xs text-neutral-500 font-normal">CTA STRATEGY</span>
            </h2>
            <p class="text-xs text-neutral-400 mb-6">管理期货量化策略，通过趋势动量、波动突破、期限结构等多策略横截面配置</p>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                {#each [
                    { name: "趋势跟踪 (Trend Following)", return: 189.44, ann: 14.50, sharpe: 1.12, dd: 12.50, desc: "大周期时序动量，捕获黑色、有色、能化板块大级别行情。" },
                    { name: "日内破位 (Intraday Breakout)", return: 86.30, ann: 9.20, sharpe: 0.78, dd: 8.40, desc: "基于多周期平均真实波幅(ATR)突破开仓，快速获利止盈。" },
                    { name: "期限套利 (Term Arbitrage)", return: 245.12, ann: 18.70, sharpe: 1.34, dd: 14.20, desc: "做多近月升水合约同时做空远月贴水合约，套取跨期基差利润。" }
                ] as strategy}
                    <div class="bg-neutral-900/60 border border-neutral-850 rounded-xl p-5 flex flex-col justify-between">
                        <div>
                            <h3 class="font-bold text-white text-base">{strategy.name}</h3>
                            <p class="text-xs text-neutral-400 mt-2 line-clamp-3">{strategy.desc}</p>
                        </div>
                        <div class="mt-6 space-y-2 border-t border-neutral-850/80 pt-4">
                            <div class="flex justify-between text-xs font-mono">
                                <span class="text-neutral-500">累计收益</span>
                                <span class="text-red-500 font-bold">+{strategy.return}%</span>
                            </div>
                            <div class="flex justify-between text-xs font-mono">
                                <span class="text-neutral-500">年化收益</span>
                                <span class="text-red-500 font-bold">+{strategy.ann}%</span>
                            </div>
                            <div class="flex justify-between text-xs font-mono">
                                <span class="text-neutral-500">夏普比率</span>
                                <span class="text-white font-bold">{strategy.sharpe}</span>
                            </div>
                            <div class="flex justify-between text-xs font-mono">
                                <span class="text-neutral-500">最大回撤</span>
                                <span class="text-green-400 font-bold">{strategy.dd}%</span>
                            </div>
                        </div>
                    </div>
                {/each}
            </div>

            <div class="bg-neutral-900/40 border border-neutral-850 rounded-xl p-5 mt-6">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-sm font-bold text-white">综合 CTA 策略净值走势 (呈平稳上行态势)</h3>
                    <span class="text-[10px] text-neutral-500 font-mono">2020 - 2026</span>
                </div>
                <div class="w-full h-40 bg-neutral-950 rounded border border-neutral-900 flex items-center justify-center relative overflow-hidden">
                    <svg viewBox="0 0 600 120" class="w-full h-full" preserveAspectRatio="none">
                        <polyline fill="none" stroke="#ef4444" stroke-width="2" points={svgPoints(ctaCurve, 600, 120, 10)} />
                    </svg>
                </div>
            </div>
        </div>
    {/if}

    <!-- ========================================== -->
    <!-- 4. OPTION STRATEGY (期权策略 - Image 4) -->
    <!-- ========================================== -->
    {#if activeTab === "option"}
        <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-6">
            <h2 class="text-xl font-extrabold text-white flex items-center gap-2 mb-2">
                期权策略看板 <span class="text-xs text-neutral-500 font-normal">OPTION</span>
            </h2>
            <p class="text-xs text-neutral-400 mb-6">利用波动率微笑扭曲、偏度异常及期限结构，进行多套利模型动态分配</p>

            <!-- Cards Grid -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                {#each [
                    {
                        id: "composite-core",
                        title: "核心合成曲线",
                        subtitle: "COMPOSITE CORE",
                        tag: "11 持仓",
                        desc: "统一资金账户动态合成 SG、GV、MMR 与 SKRR；SKRR 有持仓时提高事件权重，平时以 SG/GV 为主，MMR 为期限结构卫星。",
                        details: ["SKRR激活时 80% 事件权重", "平时 SG/GV 各 45%", "MMR 常驻 10%"],
                        tags: ["期权", "合成", "动态权重", "1标的"],
                        r: 278.01, ann: 13.77, sharpe: 0.71, dd: 18.18, pos: 11
                    },
                    {
                        id: "option-allweather",
                        title: "全天候GV策略",
                        subtitle: "OPTION ALL WEATHER",
                        tag: "4 持仓",
                        desc: "以近月双卖套取时间价值为底仓，用远月虚值双买作为尾部保护；低波阶段主动叠加 Vega 保险，追求可长期持有、回撤更克制的曲线形态。",
                        details: ["全天候双买 + 远月保护", "近月双卖底仓", "远月虚值保护", "Vega overlay"],
                        tags: ["期权", "全天候", "Gamma/Vega", "2标的"],
                        r: 53.17, ann: 3.83, sharpe: 0.37, dd: 11.68, pos: 4
                    },
                    {
                        id: "short-long-gamma",
                        title: "SG策略",
                        subtitle: "SHORT / LONG GAMMA",
                        tag: "2 持仓",
                        desc: "用 VRP 250日分位数判断波动风险溢价：高分位卖近月双跨，低分位买近月双跨，并配合日频 Delta 对冲，在卖波收益和正 Gamma 波动保护间寻找平衡点。",
                        details: ["VRP 分位驱动 Gamma 切换", "高 VRP 卖近月", "低 VRP 买近月", "日频 Delta 对冲"],
                        tags: ["期权", "VRP", "Delta对冲", "2标的"],
                        r: 213.35, ann: 11.72, sharpe: 0.62, dd: 26.28, pos: 2
                    },
                    {
                        id: "skew-risk-reversal",
                        title: "SKRR策略",
                        subtitle: "SKEW RISK REVERSAL",
                        tag: "0 持仓",
                        desc: "识别严格 Put/Call skew 缺失、波动极值与神秘资金确认后的曲线失真事件。用法定一档风险反转或近月卖侧结构修复替代直接下注。",
                        details: ["Skew 异常事件修复", "Put/Call 缺失识别", "神秘资金确认", "风险反转表达"],
                        tags: ["期权", "Skew", "风险反转", "1标的"],
                        r: 152.58, ann: 9.39, sharpe: 0.41, dd: 28.30, pos: 0
                    }
                ] as opt}
                    <div class="bg-neutral-900/60 border border-neutral-850 rounded-xl p-5 flex flex-col justify-between">
                        <div>
                            <div class="flex justify-between items-start">
                                <div>
                                    <span class="text-[9px] font-mono text-neutral-500 font-bold block">{opt.subtitle}</span>
                                    <h3 class="font-bold text-white text-base mt-0.5">{opt.title}</h3>
                                </div>
                                <span class="px-2 py-0.5 text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 rounded">
                                    {opt.tag}
                                </span>
                            </div>
                            <p class="text-[11px] text-neutral-400 mt-3 leading-relaxed h-20 overflow-hidden line-clamp-4">{opt.desc}</p>
                            
                            <!-- Internal tags -->
                            <div class="flex flex-wrap gap-1.5 mt-3">
                                {#each opt.tags as tag}
                                    <span class="px-1.5 py-0.5 rounded bg-neutral-950 text-[10px] text-neutral-500">{tag}</span>
                                {/each}
                            </div>
                        </div>

                        <!-- Stats Block -->
                        <div class="mt-6 border-t border-neutral-850/80 pt-4">
                            <div class="grid grid-cols-3 gap-2 text-center mb-4">
                                <div>
                                    <span class="text-[9px] text-neutral-500 uppercase block">收益</span>
                                    <span class="text-sm font-bold font-mono text-red-500">+{opt.r}%</span>
                                </div>
                                <div>
                                    <span class="text-[9px] text-neutral-500 uppercase block">年化</span>
                                    <span class="text-sm font-bold font-mono text-red-500">+{opt.ann}%</span>
                                </div>
                                <div>
                                    <span class="text-[9px] text-neutral-500 uppercase block">夏普</span>
                                    <span class="text-sm font-bold font-mono text-white">{opt.sharpe}</span>
                                </div>
                            </div>
                            <div class="grid grid-cols-2 gap-2 text-xs mb-4">
                                <div class="flex justify-between font-mono bg-neutral-950 px-2 py-1 rounded">
                                    <span class="text-neutral-500">回撤</span>
                                    <span class="text-green-400 font-bold">-{opt.dd}%</span>
                                </div>
                                <div class="flex justify-between font-mono bg-neutral-950 px-2 py-1 rounded">
                                    <span class="text-neutral-500">持仓</span>
                                    <span class="text-white font-bold">{opt.pos}</span>
                                </div>
                            </div>

                            <!-- Red mini Sparkline Curve -->
                            <div class="h-10 bg-neutral-950/80 border border-neutral-900 rounded overflow-hidden flex items-center justify-center relative mb-4">
                                <svg viewBox="0 0 200 40" class="w-full h-full" preserveAspectRatio="none">
                                    <polyline fill="none" stroke="#ef4444" stroke-width="1.5" points={svgPoints(optionCompositeCurve, 200, 40, 2)} />
                                </svg>
                            </div>

                            <!-- Buttons -->
                            <div class="flex gap-2">
                                <button onclick={() => activeModal = opt.id} class="flex-1 bg-amber-500 text-neutral-950 font-bold py-1.5 px-3 rounded text-xs hover:bg-amber-400 transition text-center">
                                    详情
                                </button>
                                <button class="flex-1 bg-neutral-850 hover:bg-neutral-800 text-neutral-300 font-bold py-1.5 px-3 rounded text-xs transition text-center">
                                    加入自选
                                </button>
                            </div>
                        </div>
                    </div>
                {/each}
            </div>

            <!-- Row 5: MMR策略 (Image 4 bottom card) -->
            <div class="bg-neutral-900/60 border border-neutral-850 rounded-xl p-5 max-w-sm">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <span class="text-[9px] font-mono text-neutral-500 font-bold block">MAIN-MONTH MEAN REVERSION</span>
                        <h3 class="font-bold text-white text-base mt-0.5">MMR策略</h3>
                    </div>
                    <span class="px-2 py-0.5 text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 rounded">
                        4 持仓
                    </span>
                </div>
                <p class="text-xs text-neutral-400 leading-relaxed mb-4">
                    跟踪50ETF主力与次主力月份 ATM Put IV 期限价差的250日分位，在极高/极低分位点通过平铺同式月间利差做均值回复交易。
                </p>
                <div class="bg-neutral-950 p-3 rounded-lg border border-neutral-900 space-y-2">
                    <h4 class="text-xs font-bold text-white">Put 期限价差均值回复</h4>
                    <ul class="text-[11px] text-neutral-500 space-y-1">
                        <li>• 主次月 ATM Put</li>
                        <li>• 250日分位数定位</li>
                        <li>• 跨月月限价差捕捉</li>
                    </ul>
                </div>
                <div class="flex flex-wrap gap-1.5 mt-4">
                    <span class="px-1.5 py-0.5 rounded bg-neutral-950 text-[10px] text-neutral-500">期权</span>
                    <span class="px-1.5 py-0.5 rounded bg-neutral-950 text-[10px] text-neutral-500">期限结构</span>
                    <span class="px-1.5 py-0.5 rounded bg-neutral-950 text-[10px] text-neutral-500">月限差</span>
                    <span class="px-1.5 py-0.5 rounded bg-neutral-950 text-[10px] text-neutral-500">1标的</span>
                </div>
            </div>
        </div>
    {/if}

    <!-- ========================================== -->
    <!-- 5. ETF STRATEGY (ETF 策略 - Image 1) -->
    <!-- ========================================== -->
    {#if activeTab === "etf"}
        <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-6">
            <h2 class="text-xl font-extrabold text-white flex items-center gap-2 mb-2">
                ETF 策略看板 <span class="text-xs text-neutral-500 font-normal">ETF</span>
            </h2>
            <p class="text-xs text-neutral-400 mb-6">跟踪大盘核心ETF动量轮动，实施低换手率的趋势多头配置</p>

            <!-- Card Box (Recreates Image 1) -->
            <div class="max-w-sm bg-neutral-900/60 border border-neutral-850 rounded-xl p-5 flex flex-col justify-between">
                <div>
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[9px] font-mono text-neutral-500 font-bold block">ETF MOMENTUM</span>
                            <h3 class="font-bold text-white text-base mt-0.5">动量策略</h3>
                        </div>
                        <span class="px-2 py-0.5 text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20 rounded">
                            1 持仓
                        </span>
                    </div>
                    <p class="text-xs text-neutral-400 mt-3 leading-relaxed">
                        多资产 ETF 动态配置与动量轮动观察。
                    </p>

                    <!-- Tags -->
                    <div class="flex gap-1.5 mt-4">
                        <span class="px-1.5 py-0.5 rounded bg-neutral-950 text-[10px] text-neutral-500">ETF</span>
                        <span class="px-1.5 py-0.5 rounded bg-neutral-950 text-[10px] text-neutral-500">动量</span>
                        <span class="px-1.5 py-0.5 rounded bg-neutral-950 text-[10px] text-neutral-500">轮动</span>
                    </div>
                </div>

                <div class="mt-6 border-t border-neutral-850/80 pt-4">
                    <!-- Key Stats -->
                    <div class="grid grid-cols-3 gap-2 text-center mb-4">
                        <div>
                            <span class="text-[9px] text-neutral-500 uppercase block">收益</span>
                            <span class="text-base font-bold font-mono text-red-500">+406.05%</span>
                        </div>
                        <div>
                            <span class="text-[9px] text-neutral-500 uppercase block">年化</span>
                            <span class="text-base font-bold font-mono text-red-500">+21.27%</span>
                        </div>
                        <div>
                            <span class="text-[9px] text-neutral-500 uppercase block">夏普</span>
                            <span class="text-base font-bold font-mono text-white">0.89</span>
                        </div>
                    </div>
                    <div class="grid grid-cols-3 gap-2 text-center mb-4">
                        <div class="bg-neutral-950 rounded py-1 px-1 text-center">
                            <span class="text-[8px] text-neutral-500 uppercase block">回撤</span>
                            <span class="text-xs font-bold font-mono text-green-400">29.34%</span>
                        </div>
                        <div class="bg-neutral-950 rounded py-1 px-1 text-center">
                            <span class="text-[8px] text-neutral-500 uppercase block">持仓</span>
                            <span class="text-xs font-bold font-mono text-white">1</span>
                        </div>
                        <div class="bg-neutral-950 rounded py-1 px-1 text-center">
                            <span class="text-[8px] text-neutral-500 uppercase block">调仓</span>
                            <span class="text-xs font-bold font-mono text-white">50</span>
                        </div>
                    </div>

                    <!-- Net Value curve sparkline -->
                    <div class="mt-3">
                        <div class="flex justify-between items-center text-[10px] text-neutral-500 mb-1.5 font-mono">
                            <span>净值走势</span>
                            <span class="text-red-400 font-bold">+406.05%</span>
                        </div>
                        <div class="h-16 bg-neutral-950/80 border border-neutral-900 rounded overflow-hidden flex items-center justify-center relative mb-4">
                            <svg viewBox="0 0 200 60" class="w-full h-full" preserveAspectRatio="none">
                                <polyline fill="none" stroke="#ef4444" stroke-width="2" points={svgPoints(etfCurve, 200, 60, 2)} />
                            </svg>
                            <span class="absolute bottom-1 left-2 text-[8px] text-neutral-600 font-mono">2017-09-25</span>
                            <span class="absolute bottom-1 right-2 text-[8px] text-neutral-600 font-mono">2026-06-12</span>
                        </div>
                    </div>

                    <!-- Buttons -->
                    <div class="flex gap-2">
                        <button onclick={() => activeModal = "etf-details"} class="flex-1 bg-amber-500 text-neutral-950 font-bold py-2 px-3 rounded text-xs hover:bg-amber-400 transition text-center">
                            详情
                        </button>
                        <button class="flex-1 bg-neutral-850 hover:bg-neutral-800 text-neutral-300 font-bold py-2 px-3 rounded text-xs transition text-center">
                            加入自选
                        </button>
                    </div>
                </div>
            </div>
        </div>
    {/if}

    <!-- ========================================== -->
    <!-- 6. MACRO QUANT STRATEGY (宏观量化策略 - Image 2) -->
    <!-- ========================================== -->
    {#if activeTab === "macro-strategy"}
        <div class="bg-neutral-950 border border-neutral-800 rounded-xl p-6">
            <h2 class="text-xl font-extrabold text-white flex items-center gap-2 mb-2">
                宏观流动性策略 <span class="text-xs text-neutral-500 font-normal">MACRO STRATEGY</span>
            </h2>
            <p class="text-xs text-neutral-400 mb-6">IC、半月潮汐效应 + 剩余流动性象限择时</p>

            <!-- Recreating Image 2 grids -->
            <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
                <!-- 1. Left metadata block -->
                <div class="lg:col-span-3 bg-neutral-900/60 border border-neutral-850 rounded-xl p-5">
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 border-b border-neutral-850/80 pb-4 mb-4">
                        <div>
                            <span class="text-[9px] uppercase text-neutral-500 font-bold block">当前信号 (2026-06-12)</span>
                            <span class="px-2 py-0.5 text-xs font-bold bg-green-500/10 text-green-400 border border-green-500/20 rounded inline-block mt-1">做多</span>
                        </div>
                        <div>
                            <span class="text-[9px] uppercase text-neutral-500 font-bold block">执行原因</span>
                            <span class="text-xs text-neutral-300 mt-1 block font-semibold">上半年固定做多</span>
                        </div>
                        <div>
                            <span class="text-[9px] uppercase text-neutral-500 font-bold block">信号月份</span>
                            <span class="text-xs text-neutral-300 mt-1 block font-mono">202605</span>
                        </div>
                        <div>
                            <span class="text-[9px] uppercase text-neutral-500 font-bold block">目标仓位</span>
                            <span class="text-xs text-neutral-300 mt-1 block font-mono">1</span>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <span class="text-[9px] uppercase text-neutral-500 font-bold block">IC 开盘</span>
                            <span class="text-sm font-semibold font-mono text-white">8130.00</span>
                        </div>
                        <div>
                            <span class="text-[9px] uppercase text-neutral-500 font-bold block">IC 收盘</span>
                            <span class="text-sm font-semibold font-mono text-white">8117.20</span>
                        </div>
                        <div>
                            <span class="text-[9px] uppercase text-neutral-500 font-bold block">剩余流动性</span>
                            <span class="text-sm font-semibold font-mono text-white">0.00</span>
                        </div>
                        <div>
                            <span class="text-[9px] uppercase text-neutral-500 font-bold block">变化值</span>
                            <span class="text-sm font-semibold font-mono text-white">0.00</span>
                        </div>
                    </div>
                </div>

                <!-- 2. Right Backtest stats (回测表现) -->
                <div class="bg-neutral-900/60 border border-neutral-850 rounded-xl p-5 flex flex-col justify-between">
                    <div>
                        <h4 class="text-xs uppercase text-neutral-400 font-bold mb-3 border-b border-neutral-850/50 pb-2">回测表现</h4>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center text-xs">
                                <span class="text-neutral-500">累计收益</span>
                                <span class="font-mono text-red-500 font-bold">+151.04%</span>
                            </div>
                            <div class="flex justify-between items-center text-xs">
                                <span class="text-neutral-500">年化收益</span>
                                <span class="font-mono text-red-500 font-bold">+8.70%</span>
                            </div>
                            <div class="flex justify-between items-center text-xs">
                                <span class="text-neutral-500">最大回撤</span>
                                <span class="font-mono text-green-400 font-bold">13.85%</span>
                            </div>
                            <div class="flex justify-between items-center text-xs">
                                <span class="text-neutral-500">交易次数</span>
                                <span class="font-mono text-white font-bold">89</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Equity Curve & Strategy explanation -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                <!-- Curve -->
                <div class="lg:col-span-2 bg-neutral-900/60 border border-neutral-850 rounded-xl p-5">
                    <div class="flex justify-between items-center mb-4 border-b border-neutral-850/50 pb-2">
                        <span class="text-xs font-bold text-white uppercase">净值曲线</span>
                        <span class="text-[9px] text-neutral-500 font-mono">2015-04-16 至 2026-06-15</span>
                    </div>
                    <div class="w-full h-56 bg-neutral-950 rounded border border-neutral-900 flex items-center justify-center relative overflow-hidden">
                        <svg viewBox="0 0 600 120" class="w-full h-full" preserveAspectRatio="none">
                            <polyline fill="none" stroke="#eab308" stroke-width="2" points={svgPoints(macroLiquidityCurve, 600, 120, 10)} />
                        </svg>
                    </div>
                </div>

                <!-- Description (策略说明) -->
                <div class="bg-neutral-900/60 border border-neutral-850 rounded-xl p-5 flex flex-col justify-between">
                    <div>
                        <h4 class="text-xs uppercase text-neutral-400 font-bold mb-3 border-b border-neutral-850/50 pb-2">策略说明</h4>
                        <div class="space-y-4 text-[11px] leading-relaxed text-neutral-300">
                            <div>
                                <span class="text-amber-500 font-bold block">半月潮汐</span>
                                <p class="text-neutral-400 mt-1">银行月末存贷考核等因素致宏观资金下半月通常强于下半月。</p>
                            </div>
                            <div>
                                <span class="text-amber-500 font-bold block">剩余流动性</span>
                                <p class="text-neutral-400 mt-1">监控M2与社融增速差值，动态映射流动性扩张与收缩象限。</p>
                            </div>
                            <div>
                                <span class="text-amber-500 font-bold block">双择时</span>
                                <p class="text-neutral-400 mt-1">上半月固定做多 IC；下半月按上一月剩余流动性象限决定做多、做空或空仓。</p>
                            </div>
                        </div>
                    </div>
                    <div class="border-t border-neutral-850 pt-2 mt-4 text-[9px] text-red-400">
                        风险：宏观数据滞后、政策节奏变化和市场波动都可能使历史规律失效。
                    </div>
                </div>
            </div>

            <!-- Signal History Logs -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Recent signals (最近信号) -->
                <div class="lg:col-span-2 bg-neutral-900/40 border border-neutral-850 rounded-xl overflow-hidden">
                    <div class="px-4 py-2.5 border-b border-neutral-850 bg-neutral-900/80 text-xs font-bold text-neutral-400">
                        最近信号
                    </div>
                    <table class="w-full text-left text-xs text-neutral-300">
                        <thead class="bg-neutral-950 text-neutral-500 font-medium">
                            <tr>
                                <th class="px-4 py-2">日期</th>
                                <th class="px-4 py-2">方向</th>
                                <th class="px-4 py-2">信号月</th>
                                <th class="px-4 py-2">象限</th>
                                <th class="px-4 py-2">流动性</th>
                                <th class="px-4 py-2">IC收盘</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-neutral-850 font-mono text-[11px]">
                            {#each [
                                { d: "2026-06-12", dir: "做多", m: "202605", q: "缺失", l: "0.00", ic: "8117.20", c: "text-red-400" },
                                { d: "2026-05-15", dir: "做空", m: "202604", q: "衰退增加", l: "-0.15", ic: "8102.50", c: "text-green-400" },
                                { d: "2026-04-12", dir: "做多", m: "202603", q: "复苏增加", l: "0.22", ic: "7980.80", c: "text-red-400" }
                            ] as sig}
                                <tr class="hover:bg-neutral-900/30">
                                    <td class="px-4 py-2 text-neutral-400">{sig.d}</td>
                                    <td class="px-4 py-2 font-bold {sig.c}">{sig.dir}</td>
                                    <td class="px-4 py-2">{sig.m}</td>
                                    <td class="px-4 py-2 text-neutral-400">{sig.q}</td>
                                    <td class="px-4 py-2">{sig.l}</td>
                                    <td class="px-4 py-2 text-white">{sig.ic}</td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>

                <!-- Monthly Liquidity Table (月度流动性) -->
                <div class="bg-neutral-900/40 border border-neutral-850 rounded-xl overflow-hidden">
                    <div class="px-4 py-2.5 border-b border-neutral-850 bg-neutral-900/80 text-xs font-bold text-neutral-400 flex justify-between">
                        <span>月度流动性</span>
                        <span class="text-[9px] text-neutral-500 font-mono">Tushare 数据源</span>
                    </div>
                    <table class="w-full text-left text-xs text-neutral-300">
                        <thead class="bg-neutral-950 text-neutral-500 font-medium">
                            <tr>
                                <th class="px-4 py-2">月份</th>
                                <th class="px-4 py-2">象限</th>
                                <th class="px-4 py-2">M2</th>
                                <th class="px-4 py-2">社融</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-neutral-850 font-mono text-[11px]">
                            {#each [
                                { m: "202604", q: "复苏增加", m2: "8.60%", sf: "7.76%" },
                                { m: "202603", q: "复苏增加", m2: "8.72%", sf: "7.92%" },
                                { m: "202602", q: "滞胀收缩", m2: "8.30%", sf: "8.10%" }
                            ] as liq}
                                <tr class="hover:bg-neutral-900/30">
                                    <td class="px-4 py-2 text-neutral-400">{liq.m}</td>
                                    <td class="px-4 py-2 text-white">{liq.q}</td>
                                    <td class="px-4 py-2">{liq.m2}</td>
                                    <td class="px-4 py-2">{liq.sf}</td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    {/if}
</div>

<!-- ========================================== -->
<!-- STRATEGY DETAILS DETAILS MODALS (详情弹出框) -->
<!-- ========================================== -->
{#if activeModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm" transition:fade>
        <div class="w-full max-w-2xl bg-neutral-950 rounded-2xl border border-neutral-800 p-6 relative shadow-2xl">
            <button onclick={() => activeModal = null} class="absolute top-4 right-4 text-neutral-500 hover:text-white transition">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>

            {#if activeModal === "etf-details"}
                <h3 class="text-lg font-bold text-white mb-2">ETF 动量轮动策略详情</h3>
                <p class="text-xs text-neutral-400 mb-4">该策略监控全球核心指数、贵金属及商品ETF动量值，按月对资产打分，挑选动量最高的单一ETF重仓持有。如果所有标的动量为负，策略自动平仓回笼现金避险。</p>
                <div class="bg-neutral-900 p-4 rounded-xl border border-neutral-850 space-y-3">
                    <h4 class="text-sm font-semibold text-amber-400 border-b border-neutral-800 pb-2">当前配置权重 (Current Portfolio)</h4>
                    <div class="flex justify-between items-center text-xs py-1">
                        <span class="text-white font-mono font-bold">QQQ (纳斯达克100 ETF)</span>
                        <span class="text-red-400 font-bold">100.00% (满仓轮入)</span>
                    </div>
                    <div class="flex justify-between items-center text-xs py-1 border-t border-neutral-800/50">
                        <span class="text-neutral-500 font-mono">GLD (黄金 ETF)</span>
                        <span class="text-neutral-500">0.00% (备选, 动量第2)</span>
                    </div>
                    <div class="flex justify-between items-center text-xs py-1 border-t border-neutral-800/50">
                        <span class="text-neutral-500 font-mono">SPY (标普500 ETF)</span>
                        <span class="text-neutral-500">0.00% (备选, 动量第3)</span>
                    </div>
                </div>
            {:else if activeModal === "composite-core"}
                <h3 class="text-lg font-bold text-white mb-2">核心合成曲线 (Composite Core)</h3>
                <p class="text-xs text-neutral-400 mb-4">将旗下多个期权策略融合，平滑风险敞口。动态控制多标的 Delta / Vega 敞口，实现资产曲线稳健攀升。</p>
                <ul class="space-y-2 text-xs text-neutral-300">
                    <li class="bg-neutral-900 p-2.5 rounded border border-neutral-850 flex justify-between">
                        <span>全天候双卖底仓</span> <span class="text-amber-400 font-bold">45.00%</span>
                    </li>
                    <li class="bg-neutral-900 p-2.5 rounded border border-neutral-850 flex justify-between">
                        <span>VRP 驱动 Gamma 切换</span> <span class="text-amber-400 font-bold">45.00%</span>
                    </li>
                    <li class="bg-neutral-900 p-2.5 rounded border border-neutral-850 flex justify-between">
                        <span>期限均值回复 (MMR)</span> <span class="text-amber-400 font-bold">10.00%</span>
                    </li>
                </ul>
            {:else if activeModal === "option-allweather"}
                <h3 class="text-lg font-bold text-white mb-2">全天候GV策略 (Option All Weather)</h3>
                <p class="text-xs text-neutral-400 mb-4">通过做空近月虚值看涨/看跌期权（赚取时间衰减），做多远月更深虚值期权（应对尾部极端闪崩风险）。</p>
                <div class="bg-neutral-900 p-3 rounded-lg text-xs space-y-2 text-neutral-400">
                    <p><strong class="text-white">回测参数：</strong>250日波动率回溯，远月尾部保护覆盖率达 120%。</p>
                    <p><strong class="text-white">调仓频率：</strong>周频调仓，到期日前4天自动滚动平仓。</p>
                </div>
            {:else if activeModal === "short-long-gamma"}
                <h3 class="text-lg font-bold text-white mb-2">SG策略 (Short/Long Gamma)</h3>
                <p class="text-xs text-neutral-400 mb-4">基于方差风险溢价 (VRP) 估算。当 VRP 位于历史高分位（期权隐含波动率显著高于历史实际波动率）时卖出近月跨式，低分位时买入。日频进行 Delta 动态对冲，消除方向性敞口。</p>
            {:else if activeModal === "skew-risk-reversal"}
                <h3 class="text-lg font-bold text-white mb-2">SKRR策略 (Skew Risk Reversal)</h3>
                <p class="text-xs text-neutral-400 mb-4">捕捉看涨和看跌期权波幅不对称偏离的极端异常。利用风险反转期权结构，在极低回撤风险的前提下，捕获市场单边破位带来的暴利契机。</p>
            {/if}

            <div class="mt-6 flex justify-end">
                <button onclick={() => activeModal = null} class="bg-amber-500 hover:bg-amber-400 text-neutral-950 font-bold py-2 px-5 rounded text-xs transition">
                    关闭
                </button>
            </div>
        </div>
    </div>
{/if}
