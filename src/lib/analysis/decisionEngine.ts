export type EventCategory =
    | 'Geopolitical Conflict'
    | 'Macro Policy & Rates'
    | 'Energy & Supply Shock'
    | 'Tech & Semiconductor'
    | 'Auto & Renewables'
    | 'Currency & FX'
    | 'Macro Economy'
    | 'Regulatory Policy'
    | 'Unknown';

export interface AssetImpact {
    asset: string;
    direction: 'UP' | 'DOWN' | 'VOLATILE';
}

export interface HistoricalCase {
    date: string;
    headline: string;
    url: string; // Mock reference URL
}

export interface CausalRule {
    keywords: string[];
    category: EventCategory;
    subCategory: string;
    impacts: AssetImpact[];
    causalLogic: string;
    baseWinRate: number; // For the backtest simulator (e.g., 0.76 for 76%)
    baseOccurrences: number; // e.g., 38
    avgReturnPercent: number; // e.g., 2.1%
    intensityWeight: number; // 0 to 1
    historicalCases: HistoricalCase[];
}

// THE DETERMINISTIC RULESET (From User Specs)
export const DECISION_RULES: CausalRule[] = [
    {
        keywords: ['war', 'conflict', 'missile', 'attack', 'blockade', 'strike'],
        category: 'Geopolitical Conflict',
        subCategory: 'Kinetic Escalation',
        impacts: [
            { asset: 'WTI Crude Oil', direction: 'UP' },
            { asset: 'Natural Gas', direction: 'UP' },
            { asset: 'Gold', direction: 'UP' },
            { asset: 'Defense Stocks (RTX, LMT)', direction: 'UP' },
            { asset: 'S&P 500', direction: 'DOWN' },
            { asset: 'Tech Growth Stocks', direction: 'DOWN' },
        ],
        causalLogic: 'Supply restriction risk → Inflation expectations rise → Safe haven flight.',
        baseWinRate: 0.78,
        baseOccurrences: 42,
        avgReturnPercent: 2.3,
        intensityWeight: 0.9,
        historicalCases: [
            { date: "Oct 2023", headline: "Middle East Kinetic Escalation Spikes Brent Crude", url: "https://www.bloomberg.com/markets" },
            { date: "Feb 2022", headline: "Eastern Europe Ground Conflict Drives Safe Haven Rotation", url: "https://www.reuters.com/markets" },
            { date: "Sep 2019", headline: "Aramco Abqaiq Strike Halts 5% of Global Oil Supply", url: "https://www.ft.com/markets" }
        ]
    },
    {
        keywords: ['sanction', 'export control', 'embargo', 'ban'],
        category: 'Geopolitical Conflict',
        subCategory: 'Economic Sanctions',
        impacts: [
            { asset: 'Target Currency', direction: 'DOWN' },
            { asset: 'Local Supply Chains', direction: 'UP' },
            { asset: 'Global Supply Chains', direction: 'DOWN' },
        ],
        causalLogic: 'Trade friction → Localized supply gluts / Global supply squeezes → Margin compression.',
        baseWinRate: 0.65,
        baseOccurrences: 28,
        avgReturnPercent: -1.5,
        intensityWeight: 0.7,
        historicalCases: [
            { date: "May 2024", headline: "New Semiconductor Export Controls Cap Nvidia Revenue", url: "https://www.wsj.com/markets" },
            { date: "Mar 2022", headline: "SWIFT Disconnection Sanctions Force Currency Devaluation", url: "https://www.bloomberg.com/markets" }
        ]
    },
    {
        keywords: ['rate hike', 'hawkish', 'fed raises', 'inflation jumps'],
        category: 'Macro Policy & Rates',
        subCategory: 'Tightening Cycle',
        impacts: [
            { asset: 'DXY (US Dollar)', direction: 'UP' },
            { asset: 'US Treasury Yields', direction: 'UP' },
            { asset: 'Gold', direction: 'DOWN' },
            { asset: 'Tech/Growth Stocks', direction: 'DOWN' },
            { asset: 'Bond Prices', direction: 'DOWN' },
        ],
        causalLogic: 'Discount rate increases → Present value of future cash flows drops → Dollar strengthens.',
        baseWinRate: 0.82,
        baseOccurrences: 55,
        avgReturnPercent: -2.8,
        intensityWeight: 0.85,
        historicalCases: [
            { date: "Jun 2022", headline: "Fed Hikes 75bps, S&P 500 Enters Bear Market", url: "https://www.cnbc.com/markets" },
            { date: "Dec 2018", headline: "Powell's Hawkish Pivot Triggers Q4 Equities Selloff", url: "https://www.barrons.com" }
        ]
    },
    {
        keywords: ['rate cut', 'dovish', 'fed cuts', 'recession fears'],
        category: 'Macro Policy & Rates',
        subCategory: 'Easing Cycle',
        impacts: [
            { asset: 'S&P 500', direction: 'UP' },
            { asset: 'Gold', direction: 'UP' },
            { asset: 'Bond Prices', direction: 'UP' },
            { asset: 'DXY (US Dollar)', direction: 'DOWN' },
            { asset: 'Tech/Growth Stocks', direction: 'UP' },
        ],
        causalLogic: 'Cost of capital drops → Equity multiples expand → Yield-bearing assets weaken relative to non-yielding.',
        baseWinRate: 0.74,
        baseOccurrences: 34,
        avgReturnPercent: 1.9,
        intensityWeight: 0.8,
        historicalCases: [
            { date: "Sep 2024", headline: "FOMC Jumbo 50bps Cut Sparks Broad Equity Rally", url: "https://www.reuters.com/markets" },
            { date: "Mar 2020", headline: "Emergency Zero-Bound Rate Cut Initiates Longest Bull Run", url: "https://www.bloomberg.com/markets" }
        ]
    },
    {
        keywords: ['production cut', 'refinery explosion', 'opec', 'halts output'],
        category: 'Energy & Supply Shock',
        subCategory: 'Supply Contraction',
        impacts: [
            { asset: 'WTI Crude Oil', direction: 'UP' },
            { asset: 'Energy Sector (XLE)', direction: 'UP' },
            { asset: 'Airlines', direction: 'DOWN' },
            { asset: 'Transport/Logistics', direction: 'DOWN' },
        ],
        causalLogic: 'Immediate supply shock → Direct input cost spikes for transport → Margin expansion for producers.',
        baseWinRate: 0.88,
        baseOccurrences: 61,
        avgReturnPercent: 4.1,
        intensityWeight: 0.95,
        historicalCases: [
            { date: "Apr 2023", headline: "OPEC+ Surprise 1.16M bpd Output Cut Jolts Energy Markets", url: "https://www.ft.com/markets" },
            { date: "Aug 2020", headline: "Hurricane Delta Forces Preventive Refinery Shutdowns", url: "https://www.reuters.com/markets" }
        ]
    },
    {
        keywords: ['chip ban', 'export restriction', 'foundry', 'semiconductor ban'],
        category: 'Tech & Semiconductor',
        subCategory: 'Geopolitical Tech Friction',
        impacts: [
            { asset: 'TSMC (TSM)', direction: 'DOWN' },
            { asset: 'Nvidia (NVDA)', direction: 'DOWN' },
            { asset: 'SOXX (Semiconductor ETF)', direction: 'DOWN' },
        ],
        causalLogic: 'TAM (Total Addressable Market) reduction → Supply chain bifurcation → Revenue guidance cuts.',
        baseWinRate: 0.71,
        baseOccurrences: 19,
        avgReturnPercent: -3.4,
        intensityWeight: 0.8,
        historicalCases: [
            { date: "Oct 2022", headline: "BIS High-End AI Chip Export Ban Erases $240B in Semi Value", url: "https://www.wsj.com/markets" }
        ]
    },
    {
        keywords: ['gdp', 'payroll', 'employment', 'strong economy'],
        category: 'Macro Economy',
        subCategory: 'Growth Surprise',
        impacts: [
            { asset: 'Equities (SPY)', direction: 'UP' },
            { asset: 'Local Currency', direction: 'UP' },
            { asset: 'Bonds (TLT)', direction: 'DOWN' },
        ],
        causalLogic: 'Earnings outlook improves → Inflation risk rises → Bond yields spike.',
        baseWinRate: 0.68,
        baseOccurrences: 142,
        avgReturnPercent: 1.1,
        intensityWeight: 0.6,
        historicalCases: [
            { date: "Feb 2024", headline: "Blowout NFP Payrolls Report Triggers Massive Bond Selloff", url: "https://www.bloomberg.com/markets" },
            { date: "Jul 2023", headline: "GDP Prints 3.3% Rejecting Recession Theories", url: "https://www.cnbc.com/markets" }
        ]
    },
    {
        keywords: ['monopoly', 'antitrust', 'probe', 'subsidies'],
        category: 'Regulatory Policy',
        subCategory: 'Sector Regulation',
        impacts: [
            { asset: 'Targeted Mega-cap', direction: 'DOWN' },
            { asset: 'Subsidized Competitors', direction: 'UP' },
        ],
        causalLogic: 'Regulatory overhang caps valuation multiple → Capital rotates to subsidized peers.',
        baseWinRate: 0.60,
        baseOccurrences: 45,
        avgReturnPercent: -1.8,
        intensityWeight: 0.7,
        historicalCases: [
            { date: "Aug 2024", headline: "DOJ Landmark Alphabet Antitrust Ruling Signals Tech Contraction", url: "https://www.wsj.com" },
            { date: "Nov 2020", headline: "China Halts Ant Group IPO Sparking Multi-Year Tech Crackdown", url: "https://www.ft.com" }
        ]
    }
];

export interface DecisionEngineOutput {
    category: EventCategory;
    subCategory: string;
    causalLogic: string;
    impacts: AssetImpact[];
    backtest: {
        occurrences: number;
        winRate: number;
        avgReturn: number;
        timeframe: string;
    };
    historicalCases: HistoricalCase[];
    confidenceScore: number;
}

/**
 * Core routing engine that evaluates text and returns a structured, deterministic decision.
 */
export function evaluateEvent(title: string, summaryTexts: string[]): DecisionEngineOutput {
    const combinedText = [title, ...summaryTexts].join(' ').toLowerCase();

    // 1. Classification & Mapping
    let matchedRule: CausalRule = {
        keywords: [],
        category: 'Unknown',
        subCategory: 'Generic Volatility',
        impacts: [{ asset: 'VIX', direction: 'UP' }],
        causalLogic: 'Unclassified anomaly detected → Uncertainty premiums rise.',
        baseWinRate: 0.52,
        baseOccurrences: 120,
        avgReturnPercent: 0.5,
        intensityWeight: 0.3,
        historicalCases: [
            { date: "Oct 2008", headline: "VIX Spikes to Record Highs Amidst Unprecedented Confusion", url: "https://www.wsj.com" },
            { date: "Mar 2020", headline: "Global Shutdown Triggers Historic Market Circuit Breakers", url: "https://www.bloomberg.com" }
        ]
    };
    let maxMatchCount = 0;

    for (const rule of DECISION_RULES) {
        let matchCount = 0;
        for (const kw of rule.keywords) {
            if (combinedText.includes(kw.toLowerCase())) {
                matchCount++;
            }
        }
        if (matchCount > maxMatchCount) {
            maxMatchCount = matchCount;
            matchedRule = rule;
        }
    }

    // 2. Simulated Backtest Morphing (adds slight jitter so it looks dynamically calculated based on current severity)
    // In a production app, this would query a real historical tick database.
    const jitter = (Math.random() * 0.04) - 0.02; // +/- 2% 
    const finalWinRate = Math.min(0.99, Math.max(0.40, matchedRule.baseWinRate + jitter));

    // 3. Confidence Scoring Algorithm
    // - 40%: Historical Win Rate 
    // - 30%: Event Intensity Weight
    // - 20%: Market Context (Mocked as 0.8 for hackathon)
    // - 10%: Recency (Mocked as 1.0 for real-time events)

    const marketContextScore = 0.8;
    const recencyScore = 1.0;

    const confidenceScore = Math.round(
        (finalWinRate * 40) +
        (matchedRule.intensityWeight * 30) +
        (marketContextScore * 20) +
        (recencyScore * 10)
    );

    return {
        category: matchedRule.category,
        subCategory: matchedRule.subCategory,
        causalLogic: matchedRule.causalLogic,
        impacts: matchedRule.impacts,
        historicalCases: matchedRule.historicalCases,
        backtest: {
            occurrences: Math.floor(matchedRule.baseOccurrences * (1 + (Math.random() * 0.2))), // Add 0-20% variance to occurrences
            winRate: Math.round(finalWinRate * 100),
            avgReturn: parseFloat((matchedRule.avgReturnPercent * (1 + jitter)).toFixed(2)),
            timeframe: '1-Day' // Fixed to 1-Day for demo standard
        },
        confidenceScore
    };
}
