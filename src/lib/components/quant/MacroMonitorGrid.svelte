<script lang="ts">
    import { onMount } from "svelte";

    interface MacroItem {
        label: string;
        value: string;
        indicator?: string;
        subtext?: string;
        badge?: string;
        change?: string;
        isUp?: boolean;
    }

    interface Section {
        title: string;
        titleCn: string;
        count: number;
        items: MacroItem[];
    }

    // Macro monitors data grid
    const macroData: {
        feeds: number;
        groups: number;
        updated: string;
        sections: Section[];
    } = {
        feeds: 33,
        groups: 9,
        updated: "2026-06-15 10:02:25",
        sections: [
            {
                title: "REGIME",
                titleCn: "周期框架",
                count: 3,
                items: [
                    { label: "康波周期 (K-Wave)", value: "康波秋 (衰退过渡)", indicator: "red", subtext: "" },
                    { label: "长期债务周期 (Dalio)", value: "货币信用危机", indicator: "red", subtext: "" },
                    { label: "第四次转折 (Howe)", value: "秩序重组/地缘风险", indicator: "red", subtext: "" }
                ]
            },
            {
                title: "CROSS ASSET",
                titleCn: "全球商品",
                count: 5,
                items: [
                    { label: "比特币 (BTC)", value: "$65,457.75", badge: "+1.86%", isUp: true },
                    { label: "黄金 (Gold)", value: "$4,338.80", badge: "+2.36%", isUp: true },
                    { label: "白银 (Silver)", value: "$70.33", badge: "+3.47%", isUp: true },
                    { label: "铜 (Copper)", value: "$6.54", badge: "+1.48%", isUp: true },
                    { label: "原油 (WTI)", value: "$80.86", badge: "-4.74%", isUp: false }
                ]
            },
            {
                title: "RATES",
                titleCn: "债市利率",
                count: 3,
                items: [
                    { label: "美债 10Y", value: "4.43%", indicator: "yellow" },
                    { label: "美债 2Y", value: "4.03%", indicator: "yellow" },
                    { label: "日债 10Y", value: "2.58%", indicator: "yellow" }
                ]
            },
            {
                title: "RISK / FX",
                titleCn: "风险与汇率",
                count: 3,
                items: [
                    { label: "美元指数 (DXY)", value: "99.58", change: "-0.17%", isUp: false, subtext: "宽幅波动" },
                    { label: "USD/CNH (离岸)", value: "6.76", change: "-0.10%", isUp: false, subtext: "汇率稳健" },
                    { label: "VIX恐慌指数", value: "17.68", change: "-9.85%", isUp: false, subtext: "市场平稳" }
                ]
            },
            {
                title: "RATIOS",
                titleCn: "宏观比价",
                count: 4,
                items: [
                    { label: "金银比 (G/S)", value: "61.69", indicator: "yellow", subtext: "复苏/通胀" },
                    { label: "金油比 (Au/Oil)", value: "53.66", indicator: "red", subtext: "极度衰退/战争" },
                    { label: "铜金比 (Cu/Au)", value: "0.1506", indicator: "yellow", subtext: "增长放缓" },
                    { label: "金铜比 (Au/Cu)", value: "663.88", indicator: "yellow", subtext: "避险升温" }
                ]
            },
            {
                title: "A-SHARE",
                titleCn: "A股杠杆",
                count: 4,
                items: [
                    { label: "两融余额", value: "2.85万亿", indicator: "red", subtext: "极度狂热" },
                    { label: "两融/流通市值", value: "2.78%", indicator: "green", subtext: "结构健康" },
                    { label: "总市值", value: "129.23万亿", indicator: "neutral" },
                    { label: "流通市值", value: "102.64万亿", indicator: "neutral" }
                ]
            },
            {
                title: "GROWTH",
                titleCn: "经济增长",
                count: 3,
                items: [
                    { label: "制造业 PMI (CN)", value: "50.80", indicator: "green", subtext: "扩张区间" },
                    { label: "制造 PMI (US)", value: "48.20", indicator: "yellow", subtext: "收缩区间" },
                    { label: "GDP 年化季环比 (US)", value: "1.60%", indicator: "yellow", subtext: "增速放缓" }
                ]
            },
            {
                title: "VALUATION",
                titleCn: "权益估值",
                count: 3,
                items: [
                    { label: "沪深300 PE (TTM)", value: "11.20", indicator: "green", subtext: "低于历史均值" },
                    { label: "标普500 PE (TTM)", value: "24.50", indicator: "red", subtext: "偏向高估" },
                    { label: "股权风险溢价 (ERP)", value: "3.42%", indicator: "yellow", subtext: "性价比一般" }
                ]
            },
            {
                title: "INFLATION",
                titleCn: "通货膨胀",
                count: 3,
                items: [
                    { label: "CPI同比 (US)", value: "3.20%", indicator: "yellow", subtext: "顽固高位" },
                    { label: "核心PCE物价指数 (US)", value: "2.80%", indicator: "yellow", subtext: "缓慢下行" },
                    { label: "PPI同比 (CN)", value: "-1.20%", indicator: "green", subtext: "通缩收窄" }
                ]
            }
        ]
    };
</script>

<div class="bg-neutral-950 border border-neutral-800 rounded-xl p-6 select-none">
    <!-- Header -->
    <div class="border-b border-neutral-850/80 pb-4 mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-neutral-950">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                <!-- Globe SVG -->
                <svg class="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12.75 3.03v.568c0 .334.148.65.405.864l.406.34c.15.124.325.2.512.224l.69.09c.237.03.45.179.559.4a1.125 1.125 0 01-.19 1.012l-.41.386a1.125 1.125 0 01-.838.356h-.128a1.125 1.125 0 00-.75.287l-.448.405a1.125 1.125 0 01-1.062.266l-.515-.172a1.125 1.125 0 00-1.41.684l-.111.332a1.125 1.125 0 01-.84.78l-.501.12a1.125 1.125 0 01-1.122-.38l-.178-.222a1.125 1.125 0 00-.939-.404h-.139A1.125 1.125 0 012.75 14v-.22c0-.334.148-.65.405-.864l.406-.34c.15-.124.325-.2.512-.224l.69-.09c.237-.03.45-.179.559-.4a1.125 1.125 0 01-.19-1.012l-.41-.386a1.125 1.125 0 01-.838-.356h-.128a1.125 1.125 0 00-.75-.287l-.448-.405a1.125 1.125 0 01-1.062-.266l-.515-.172a1.125 1.125 0 00-1.41.684l-.111.332a1.125 1.125 0 01-.84.78l-.501.12a1.125 1.125 0 01-1.122-.38l-.178-.222a1.125 1.125 0 00-.939-.404h-.139A1.125 1.125 0 012.75 14" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18z" />
                </svg>
            </div>
            <div>
                <span class="text-[9px] text-neutral-500 font-mono font-bold tracking-widest block uppercase">GLOBAL MACRO TERMINAL</span>
                <h2 class="text-lg font-extrabold text-neutral-100 mt-0.5">宏观风险雷达 (Macro Risk Radar)</h2>
            </div>
        </div>
        
        <!-- Info blocks -->
        <div class="flex items-center gap-4 text-xs font-mono">
            <div class="bg-neutral-900 border border-neutral-850 px-3 py-1.5 rounded-lg flex flex-col items-center">
                <span class="text-[9px] text-neutral-500 font-bold uppercase">Feeds</span>
                <span class="text-white font-bold mt-0.5">{macroData.feeds}</span>
            </div>
            <div class="bg-neutral-900 border border-neutral-850 px-3 py-1.5 rounded-lg flex flex-col items-center">
                <span class="text-[9px] text-neutral-500 font-bold uppercase">Groups</span>
                <span class="text-white font-bold mt-0.5">{macroData.groups}</span>
            </div>
            <div class="bg-neutral-900 border border-neutral-850 px-3 py-1.5 rounded-lg flex flex-col items-start">
                <span class="text-[9px] text-neutral-500 font-bold uppercase">Updated</span>
                <span class="text-neutral-300 font-bold mt-0.5">{macroData.updated}</span>
            </div>
        </div>
    </div>

    <!-- Grid Columns -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each macroData.sections as section}
            <div class="bg-neutral-900/40 border border-neutral-850 rounded-xl overflow-hidden shadow-lg flex flex-col justify-between">
                <div>
                    <!-- Section Title -->
                    <div class="px-4 py-3 border-b border-neutral-850 bg-neutral-900/80 flex justify-between items-center">
                        <div class="flex flex-col">
                            <span class="text-[9px] text-neutral-500 font-mono font-bold tracking-wider uppercase leading-none">{section.title}</span>
                            <h3 class="text-sm font-extrabold text-neutral-200 mt-1 leading-none">{section.titleCn}</h3>
                        </div>
                        <span class="w-5 h-5 rounded bg-neutral-950 border border-neutral-800 text-[10px] text-neutral-500 flex items-center justify-center font-bold font-mono">
                            {section.count}
                        </span>
                    </div>

                    <!-- Items List -->
                    <div class="divide-y divide-neutral-850/60 p-1">
                        {#each section.items as item}
                            <div class="flex items-center justify-between px-3 py-3 hover:bg-neutral-900/40 rounded-lg transition duration-200 group">
                                <div class="flex items-center gap-2 max-w-[65%]">
                                    <!-- Indicator Dot (If applicable) -->
                                    {#if item.indicator}
                                        <span class="flex h-1.5 w-1.5 relative flex-shrink-0">
                                            {#if item.indicator === "red"}
                                                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                                <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-red-500"></span>
                                            {:else if item.indicator === "yellow"}
                                                <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-amber-500"></span>
                                            {:else if item.indicator === "green"}
                                                <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                                            {:else}
                                                <span class="relative inline-flex rounded-full h-1.5 w-1.5 bg-neutral-600"></span>
                                            {/if}
                                        </span>
                                    {/if}
                                    
                                    <div class="flex flex-col">
                                        <span class="text-xs font-medium text-neutral-300 group-hover:text-neutral-100 transition-colors leading-tight">{item.label}</span>
                                        {#if item.subtext}
                                            <span class="text-[9px] text-neutral-500 mt-0.5 leading-none">{item.subtext}</span>
                                        {/if}
                                    </div>
                                </div>

                                <div class="flex items-center gap-2">
                                    <span class="text-xs font-bold font-mono text-white text-right leading-tight">{item.value}</span>
                                    
                                    <!-- Badge for Commodity/Asset prices -->
                                    {#if item.badge}
                                        <span class="px-1.5 py-0.5 rounded text-[10px] font-bold font-mono text-center min-w-14
                                            {item.isUp ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'}"
                                        >
                                            {item.badge}
                                        </span>
                                    {/if}

                                    <!-- Percentage for currency values -->
                                    {#if item.change}
                                        <span class="text-[10px] font-bold font-mono text-right min-w-12
                                            {item.isUp ? 'text-red-400' : 'text-green-400'}"
                                        >
                                            {item.change}
                                        </span>
                                    {/if}
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>
        {/each}
    </div>
</div>
