export interface Prediction {
    id: string;
    question: string;
    yes: number;
    volume: string;
}

export interface WhaleTransaction {
    coin: string;
    amount: number;
    usd: number;
    hash: string;
}

// Mock Polymarket predictions
export async function fetchPolymarket(): Promise<Prediction[]> {
    return [
        { id: 'pm-1', question: 'Will there be a US-China military incident in 2026?', yes: 18, volume: '2.4M' },
        { id: 'pm-2', question: 'Will Bitcoin reach $150K by end of 2026?', yes: 35, volume: '8.1M' },
        { id: 'pm-3', question: 'Will Fed cut rates in Q1 2026?', yes: 42, volume: '5.2M' },
        { id: 'pm-4', question: 'Will AI cause major job losses in 2026?', yes: 28, volume: '1.8M' },
        { id: 'pm-5', question: 'Will Ukraine conflict end in 2026?', yes: 22, volume: '3.5M' },
        { id: 'pm-6', question: 'Will oil prices exceed $100/barrel?', yes: 31, volume: '2.1M' },
        { id: 'pm-7', question: 'Will there be a major cyberattack on US infrastructure?', yes: 45, volume: '1.5M' }
    ];
}

// Mock whale transactions
export async function fetchWhaleTransactions(): Promise<WhaleTransaction[]> {
    return [
        { coin: 'BTC', amount: 1500, usd: 150000000, hash: '0x1a2b...3c4d' },
        { coin: 'ETH', amount: 25000, usd: 85000000, hash: '0x5e6f...7g8h' },
        { coin: 'BTC', amount: 850, usd: 55000000, hash: '0x9i0j...1k2l' },
        { coin: 'SOL', amount: 500000, usd: 75000000, hash: '0x3m4n...5o6p' },
        { coin: 'ETH', amount: 15000, usd: 51000000, hash: '0x7q8r...9s0t' }
    ];
}
