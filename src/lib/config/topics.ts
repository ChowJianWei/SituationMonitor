export const TOPIC_MAPPING: Record<string, { sectors: string[], tickers: string[], baseWeight: number }> = {
    'semiconductor export controls': {
        sectors: ['Technology', 'Semiconductors'],
        tickers: ['NVDA', 'AMD', 'ASML', 'INTC', 'TSM', 'SOXX'],
        baseWeight: 1.5
    },
    'oil supply disruption': {
        sectors: ['Energy', 'Oil & Gas'],
        tickers: ['XOM', 'CVX', 'SHEL', 'XLE', 'USO'],
        baseWeight: 1.5
    },
    'rate cuts': {
        sectors: ['Real Estate', 'Financials'],
        tickers: ['XLRE', 'XLF', 'JPM', 'BAC', 'SPY'],
        baseWeight: 1.2
    },
    'tariffs': {
        sectors: ['Industrials', 'Consumer Discretionary'],
        tickers: ['XLI', 'XLY', 'AAPL', 'TSLA'],
        baseWeight: 1.3
    },
    'geopolitical escalation': {
        sectors: ['Defense', 'Gold'],
        tickers: ['LMT', 'RTX', 'NOC', 'GLD', 'VIX'],
        baseWeight: 2.0
    }
};

export const KEYWORD_SEVERITY: Record<string, number> = {
    'war': 100,
    'sanctions': 80,
    'outage': 60,
    'fraud': 70,
    'recall': 50,
    'resignation': 40,
    'unprecedented': 50,
    'emergency': 80,
    'disruption': 60
};
