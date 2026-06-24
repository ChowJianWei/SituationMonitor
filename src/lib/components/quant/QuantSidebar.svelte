<script lang="ts">
    interface Props {
        activeTab: string;
        onSelect: (tab: string) => void;
    }

    let { activeTab, onSelect }: Props = $props();

    const menuItems = [
        { id: "overview", label: "主页", labelEn: "Overview", icon: "home" },
        { id: "monitor", label: "实时监控", labelEn: "Real-time Monitor", icon: "activity" },
        { id: "index", label: "股指策略", labelEn: "Index Strategy", icon: "trending-up" },
        { id: "bond", label: "可转债策略", labelEn: "Bond Strategy", icon: "layers" },
        { id: "cta", label: "CTA 策略", labelEn: "CTA Strategy", icon: "layout-grid" },
        { id: "option", label: "期权策略", labelEn: "Option Strategy", icon: "sliders" },
        { id: "etf", label: "ETF 策略", labelEn: "ETF Strategy", icon: "database" },
        { id: "macro-monitor", label: "宏观监控", labelEn: "Macro Monitor", icon: "globe" },
        { id: "macro-strategy", label: "宏观量化策略", labelEn: "Macro Strategy", icon: "pulse" },
        { id: "data-monitor", label: "数据监控", labelEn: "Data Monitor", icon: "hard-drive" },
        { id: "custom", label: "自选策略", labelEn: "Custom Strategy", icon: "star" },
        { id: "forum", label: "论坛 & AI 助手", labelEn: "Forum", icon: "message" },
        { id: "ai-codegen", label: "AI 策略生成", labelEn: "AI Codegen", icon: "sparkles" },
        { id: "openstock", label: "OpenStock 市场", labelEn: "OpenStock Portal", icon: "compass", highlight: true }
    ];
</script>

<aside class="w-64 bg-neutral-950 text-neutral-300 border-r border-neutral-800 flex flex-col h-full flex-shrink-0 transition-all duration-300 select-none">
    <!-- Top Logo Panel -->
    <div class="h-16 flex items-center gap-3 px-4 border-b border-neutral-900 bg-neutral-950/80 backdrop-blur-md">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 via-amber-600 to-yellow-400 flex items-center justify-center shadow-[0_0_15px_rgba(245,158,11,0.2)]">
            <!-- Flask/Alchemy Icon -->
            <svg class="w-4 h-4 text-neutral-950" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.26M14.25 3.104v5.26M3 19.5h18M12 9.577a6 6 0 11-6.813 9.423h13.626A6 6 0 0112 9.577z" />
            </svg>
        </div>
        <div class="flex flex-col">
            <span class="font-extrabold text-sm text-neutral-100 tracking-tight leading-none">QuantAlchemist</span>
            <span class="text-[10px] text-amber-500/80 font-bold uppercase tracking-widest mt-1">Laboratory</span>
        </div>
    </div>

    <!-- Navigation Menu Items -->
    <div class="flex-1 overflow-y-auto py-4 px-2 space-y-1 scrollbar-thin">
        {#each menuItems as item}
            <button
                onclick={() => onSelect(item.id)}
                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left text-sm font-medium transition-all duration-200 group relative
                {activeTab === item.id 
                    ? 'bg-amber-500/10 text-amber-400 font-semibold border-l-2 border-amber-500 pl-2.5' 
                    : item.highlight
                      ? 'text-sky-400 hover:bg-sky-500/5 hover:text-sky-300'
                      : 'text-neutral-400 hover:bg-neutral-900 hover:text-neutral-100'}"
            >
                <!-- SVG Icon Selector -->
                <span class="w-5 h-5 flex items-center justify-center transition-transform group-hover:scale-105">
                    {#if item.icon === "home"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                        </svg>
                    {:else if item.icon === "activity"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                        </svg>
                    {:else if item.icon === "trending-up"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
                        </svg>
                    {:else if item.icon === "layers"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6.429 9.75L2.25 12l4.179 2.25m11.142 0L21.75 12l-4.179-2.25m-11.142 0L12 7.5l5.571 2.25m-11.142 0v4.5L12 16.5l5.571-2.25v-4.5m-11.142 4.5L12 16.5l5.571-2.25" />
                        </svg>
                    {:else if item.icon === "layout-grid"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                        </svg>
                    {:else if item.icon === "sliders"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
                        </svg>
                    {:else if item.icon === "database"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V10.125m16.5 0v3.75m-16.5-3.75v3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V13.875" />
                        </svg>
                    {:else if item.icon === "globe"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12.75 3.03v.568c0 .334.148.65.405.864l.406.34c.15.124.325.2.512.224l.69.09c.237.03.45.179.559.4a1.125 1.125 0 01-.19 1.012l-.41.386a1.125 1.125 0 01-.838.356h-.128a1.125 1.125 0 00-.75.287l-.448.405a1.125 1.125 0 01-1.062.266l-.515-.172a1.125 1.125 0 00-1.41.684l-.111.332a1.125 1.125 0 01-.84.78l-.501.12a1.125 1.125 0 01-1.122-.38l-.178-.222a1.125 1.125 0 00-.939-.404h-.139A1.125 1.125 0 012.75 14v-.22c0-.334.148-.65.405-.864l.406-.34c.15-.124.325-.2.512-.224l.69-.09c.237-.03.45-.179.559-.4a1.125 1.125 0 01-.19-1.012l-.41-.386a1.125 1.125 0 01-.838-.356h-.128a1.125 1.125 0 00-.75-.287l-.448-.405a1.125 1.125 0 01-1.062-.266l-.515-.172a1.125 1.125 0 00-1.41.684l-.111.332a1.125 1.125 0 01-.84.78l-.501.12a1.125 1.125 0 01-1.122-.38l-.178-.222a1.125 1.125 0 00-.939-.404h-.139A1.125 1.125 0 012.75 14" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18z" />
                        </svg>
                    {:else if item.icon === "pulse"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 9l1.054 3.162a1 1 0 00.95.684h1.99a1 1 0 00.95-.684L15 9M3.75 12h5.25m6 0h5.25M12 2.25v3M12 18.75v3" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18z" />
                        </svg>
                    {:else if item.icon === "hard-drive"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m16.5 0a2.25 2.25 0 00-2.25-2.25H6a2.25 2.25 0 00-2.25 2.25m16.5 0v3.375c0 .621-.503 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V7.5M3.75 7.5v3.375c0 .621.504 1.125 1.125 1.125h2.25a1.125 1.125 0 001.125-1.125V7.5m0 0v5.625c0 .621.504 1.125 1.125 1.125h1.5a1.125 1.125 0 001.125-1.125V7.5m4.5 0v5.625c0 .621.504 1.125 1.125 1.125h1.5a1.125 1.125 0 001.125-1.125V7.5" />
                        </svg>
                    {:else if item.icon === "star"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499c.15-.358.67-.358.82 0l2.4 4.87 5.38.784c.396.058.554.543.268.826l-3.89 3.793 1.01 5.353c.074.397-.343.699-.696.5l-4.793-2.52-4.793 2.52c-.352.199-.769-.103-.697-.5l1.01-5.353-3.89-3.793c-.286-.283-.129-.768.269-.784l5.38-.784 2.4-4.87z" />
                        </svg>
                    {:else if item.icon === "message"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                        </svg>
                    {:else if item.icon === "sparkles"}
                        <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 21L7.188 15.904L2 15L7.188 14.096L9 9L9.813 14.096L15 15L9.813 15.904Z" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19.071 4.929a10 10 0 00-14.142 0M19.071 4.929a10 10 0 010 14.142" />
                        </svg>
                    {:else if item.icon === "compass"}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.746 3.746 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
                        </svg>
                    {/if}
                </span>

                <div class="flex flex-col">
                    <span class="leading-none">{item.label}</span>
                    <span class="text-[9px] text-neutral-500 font-mono mt-0.5 tracking-tight group-hover:text-neutral-400 group-hover:translate-x-0.5 transition-all">{item.labelEn}</span>
                </div>

                <!-- Glowing Dot for Highlighted/Special Items -->
                {#if item.highlight}
                    <span class="absolute right-3 top-1/2 -translate-y-1/2 flex h-2 w-2">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-sky-500"></span>
                    </span>
                {/if}
            </button>
        {/each}
    </div>

    <!-- Bottom User Section -->
    <div class="p-3 border-t border-neutral-900 bg-neutral-950 flex flex-col gap-2">
        <div class="flex items-center gap-3 px-1 py-1">
            <div class="w-9 h-9 rounded-full bg-gradient-to-tr from-amber-600 to-yellow-500 text-neutral-950 font-bold flex items-center justify-center shadow-md">
                H
            </div>
            <div class="flex flex-col overflow-hidden">
                <span class="text-sm font-semibold text-neutral-100 truncate">howard</span>
                <span class="text-[10px] text-neutral-500 truncate">Underwriter Account</span>
            </div>
        </div>

        <button class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-xs font-semibold text-red-400/80 hover:text-red-400 hover:bg-red-500/5 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
            </svg>
            <span>登出 (Logout)</span>
        </button>
    </div>
</aside>

<style>
    /* Thin scrollbar for sidebar */
    .scrollbar-thin::-webkit-scrollbar {
        width: 4px;
    }
    .scrollbar-thin::-webkit-scrollbar-track {
        background: transparent;
    }
    .scrollbar-thin::-webkit-scrollbar-thumb {
        background: #262626;
        border-radius: 4px;
    }
    .scrollbar-thin::-webkit-scrollbar-thumb:hover {
        background: #404040;
    }
</style>
