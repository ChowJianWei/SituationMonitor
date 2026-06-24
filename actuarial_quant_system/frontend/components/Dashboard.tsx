"use client";

/**
 * Dashboard.tsx
 * =============
 * Visual portal for the Actuarial Quant System. Three tabs:
 *   1. Daily Executive Briefing  (login modal view + onboarding/API-key wizard)
 *   2. Fund Allocation Matrix     (per-asset yield / reserve / hedge layers)
 *   3. Global Intelligence        (macro propagation + EVT vs HMM vs GARCH table)
 *
 * Talks to the FastAPI backend (default http://127.0.0.1:8200). Read-only:
 * nothing here can place a trade or move funds.
 */

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Coins,
  Gauge,
  Globe2,
  History,
  KeyRound,
  Layers,
  LineChart,
  Receipt,
  ShieldCheck,
  TrendingUp,
  Waves,
  Wallet,
  X,
} from "lucide-react";

const API_BASE =
  process.env.NEXT_PUBLIC_QUANT_API ?? "http://127.0.0.1:8200";

type TabKey = "briefing" | "allocation" | "performance" | "intelligence";

interface Briefing {
  as_of: string;
  surplus_health_index: number;
  net_earnings_24h_usd: number;
  regime: string;
  regime_probabilities: Record<string, number>;
  ruin_probability: number;
  expected_shortfall_99: number;
  value_at_risk_99: number;
  free_capital_usd: number;
  frozen_reserve_usd: number;
  kill_switch_engaged: boolean;
  executive_narrative: string[];
}

interface Allocation {
  asset: string;
  yield_generation_usd: number;
  loss_reserve_usd: number;
  delta_hedge_usd: number;
  reserve_ratio: number;
}

const fmtUsd = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const fmtPct = (n: number) => `${(n * 100).toFixed(2)}%`;

// ---------------------------------------------------------------------------
// Small presentational helpers
// ---------------------------------------------------------------------------
function HealthMeter({ value }: { value: number }) {
  const color = value >= 70 ? "#10b981" : value >= 40 ? "#f59e0b" : "#ef4444";
  const angle = (Math.min(Math.max(value, 0), 100) / 100) * 180;
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 110" className="w-56">
        <path d="M10 100 A90 90 0 0 1 190 100" fill="none" stroke="#1f2937" strokeWidth="14" />
        <path
          d="M10 100 A90 90 0 0 1 190 100"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeDasharray={`${(angle / 180) * 283} 283`}
          strokeLinecap="round"
        />
        <text x="100" y="92" textAnchor="middle" className="fill-white" fontSize="34" fontWeight="700">
          {value.toFixed(0)}
        </text>
      </svg>
      <span className="text-xs uppercase tracking-widest text-gray-400">Surplus Health Index</span>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  tone = "neutral",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone?: "neutral" | "good" | "bad";
}) {
  const toneClass =
    tone === "good" ? "text-emerald-400" : tone === "bad" ? "text-red-400" : "text-white";
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
      <div className="mb-2 flex items-center gap-2 text-gray-400">
        {icon}
        <span className="text-xs uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-2xl font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Onboarding / API-key wizard (shown when zero keys are linked)
// ---------------------------------------------------------------------------
function OnboardingModal({ onClose }: { onClose: () => void }) {
  const [apiKey, setApiKey] = useState("");
  const [secret, setSecret] = useState("");
  const [deposit, setDeposit] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  async function handleActivate() {
    setStatus("Validating…");
    try {
      const res = await fetch(`${API_BASE}/api/v1/onboarding/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: "binance",
          api_key: apiKey,
          api_secret: secret,
          allocation_usd: Number(deposit) || 0,
        }),
      });
      const data = await res.json();
      if (data?.validation?.valid) {
        setStatus("Connected (paper). Withdrawals disabled. Activating engine…");
        setTimeout(onClose, 800);
      } else {
        setStatus("Validation failed — check your keys.");
      }
    } catch {
      setStatus("Backend unreachable. Is the engine running on :8200?");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-lg rounded-2xl border border-gray-700 bg-gray-950 p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
            <KeyRound size={18} className="text-amber-400" /> Link Venue & Allocate
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
          Create API keys with <b>READ</b> (and at most <b>TRADE</b>) scope.
          Never enable <b>WITHDRAW</b> — this engine is structurally unable to move funds off-venue.
        </div>

        <label className="mb-1 block text-xs uppercase tracking-wider text-gray-400">API Key</label>
        <input
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="mb-3 w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
          placeholder="read/trade-scoped key"
        />
        <label className="mb-1 block text-xs uppercase tracking-wider text-gray-400">API Secret</label>
        <input
          value={secret}
          onChange={(e) => setSecret(e.target.value)}
          type="password"
          className="mb-3 w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
          placeholder="••••••••"
        />
        <label className="mb-1 block text-xs uppercase tracking-wider text-gray-400">
          Initial Allocation (USD)
        </label>
        <input
          value={deposit}
          onChange={(e) => setDeposit(e.target.value)}
          className="mb-4 w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
          placeholder="e.g. 50000"
        />

        <button
          onClick={handleActivate}
          className="w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-500"
        >
          Start Underwriting (Paper Mode)
        </button>
        {status && <p className="mt-3 text-center text-xs text-gray-400">{status}</p>}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TAB 1 — Daily Executive Briefing
// ---------------------------------------------------------------------------
function BriefingTab({ data }: { data: Briefing | null }) {
  if (!data) return <p className="text-gray-500">Loading briefing…</p>;
  const regimeTone =
    data.regime === "TAIL_STRESS" ? "bad" : data.regime === "TRENDING" ? "good" : "neutral";

  return (
    <div className="space-y-6">
      {data.kill_switch_engaged && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-red-300">
          <AlertTriangle size={18} /> KILL SWITCH ENGAGED — trading halted, human reset required.
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex items-center justify-center rounded-xl border border-gray-800 bg-gray-900/60 p-6 lg:col-span-1">
          <HealthMeter value={data.surplus_health_index} />
        </div>
        <div className="grid grid-cols-2 gap-4 lg:col-span-2">
          <StatCard
            icon={<Wallet size={16} />}
            label="Net 24h Earnings"
            value={fmtUsd(data.net_earnings_24h_usd)}
            tone={data.net_earnings_24h_usd >= 0 ? "good" : "bad"}
          />
          <StatCard
            icon={<Activity size={16} />}
            label="Active Regime"
            value={data.regime.replace(/_/g, " ")}
            tone={regimeTone}
          />
          <StatCard
            icon={<AlertTriangle size={16} />}
            label="Ruin Probability (10k-step)"
            value={fmtPct(data.ruin_probability)}
            tone={data.ruin_probability < 0.01 ? "good" : "bad"}
          />
          <StatCard
            icon={<Gauge size={16} />}
            label="Expected Shortfall (99%)"
            value={fmtPct(data.expected_shortfall_99)}
            tone="bad"
          />
        </div>
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5">
        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-300">
          <BarChart3 size={16} /> Executive Narrative — Underwriting Activity
        </h4>
        <ul className="space-y-2">
          {data.executive_narrative.map((line, i) => (
            <li key={i} className="flex gap-2 text-sm text-gray-300">
              <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-emerald-500" />
              {line}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TAB 2 — Fund Allocation Matrix
// ---------------------------------------------------------------------------
function AllocationTab({ data }: { data: Allocation[] }) {
  const [active, setActive] = useState(0);
  if (!data.length) return <p className="text-gray-500">Loading allocations…</p>;
  const a = data[active];
  const total = a.yield_generation_usd + a.loss_reserve_usd + a.delta_hedge_usd;

  const layers = [
    { name: "Yield Generation", desc: "Active derivative positions", v: a.yield_generation_usd, color: "bg-emerald-500", icon: <TrendingUp size={16} /> },
    { name: "Loss Reserve", desc: "Frozen cash backing margin", v: a.loss_reserve_usd, color: "bg-amber-500", icon: <ShieldCheck size={16} /> },
    { name: "Delta Hedge", desc: "Spot holdings, directionally neutral", v: a.delta_hedge_usd, color: "bg-sky-500", icon: <Layers size={16} /> },
  ];

  return (
    <div className="space-y-5">
      <div className="flex gap-2">
        {data.map((asset, i) => (
          <button
            key={asset.asset}
            onClick={() => setActive(i)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium ${
              i === active ? "bg-white text-gray-900" : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            <Coins size={15} /> {asset.asset}
          </button>
        ))}
      </div>

      {/* Stacked allocation bar */}
      <div className="overflow-hidden rounded-full border border-gray-800">
        <div className="flex h-6 w-full">
          {layers.map((l) => (
            <div
              key={l.name}
              className={l.color}
              style={{ width: `${(l.v / total) * 100}%` }}
              title={`${l.name}: ${fmtUsd(l.v)}`}
            />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {layers.map((l) => (
          <div key={l.name} className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
            <div className="mb-1 flex items-center gap-2 text-gray-300">
              {l.icon}
              <span className="text-sm font-semibold">{l.name}</span>
            </div>
            <p className="mb-2 text-xs text-gray-500">{l.desc}</p>
            <div className="text-xl font-semibold text-white">{fmtUsd(l.v)}</div>
            <div className="text-xs text-gray-500">{((l.v / total) * 100).toFixed(1)}% of {a.asset}</div>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-gray-800 bg-gray-900/40 px-4 py-3 text-xs text-gray-400">
        Loss-reserve ratio for {a.asset}: <b className="text-amber-400">{fmtPct(a.reserve_ratio)}</b> of
        notional is frozen as an actuarial buffer (max of exchange margin and EVT Expected Shortfall + prudence load).
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TAB 3 — Performance & Activity (trade / investment tracking)
// ---------------------------------------------------------------------------
interface Performance {
  estimated: boolean;
  note: string;
  seed_equity_usd: number;
  estimated_equity_usd: number;
  estimated_pnl_usd: number;
  estimated_return_pct: number;
  total_paper_fills: number;
  rejected_by_gate: number;
  total_notional_underwritten_usd: number;
  total_costs_usd: number;
  estimated_premium_collected_usd: number;
  reserves_locked_usd: number;
  equity_curve: number[];
  per_asset: { asset: string; fills: number; notional_usd: number; premium_usd: number; costs_usd: number }[];
  recent_activity: any[];
}

function Sparkline({ data }: { data: number[] }) {
  if (data.length < 2) return <div className="h-[120px]" />;
  const w = 600, h = 120, pad = 8;
  const min = Math.min(...data), max = Math.max(...data);
  const span = max - min || 1;
  const pts = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (w - 2 * pad);
    const y = h - pad - ((v - min) / span) * (h - 2 * pad);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const up = data[data.length - 1] >= data[0];
  const color = up ? "#10b981" : "#ef4444";
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
      <polyline fill="none" stroke={color} strokeWidth="2" points={pts.join(" ")} />
    </svg>
  );
}

function PerformanceTab() {
  const [perf, setPerf] = useState<Performance | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () =>
    fetch(`${API_BASE}/api/v1/performance`).then((r) => r.json()).then(setPerf).catch(() => setPerf(null));
  useEffect(() => { load(); }, []);

  async function runCycle() {
    setBusy(true);
    await fetch(`${API_BASE}/api/v1/cycle/run`, { method: "POST" }).catch(() => {});
    await load();
    setBusy(false);
  }

  if (!perf) return <p className="text-gray-500">Loading performance… (is the engine running on :8200?)</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-xs text-amber-300/80">{perf.note}</p>
        <button
          onClick={runCycle}
          disabled={busy}
          className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {busy ? "Running…" : "Run underwriting cycle"}
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard icon={<LineChart size={16} />} label="Estimated Equity" value={fmtUsd(perf.estimated_equity_usd)} />
        <StatCard
          icon={<TrendingUp size={16} />}
          label="Estimated P&L"
          value={`${perf.estimated_pnl_usd >= 0 ? "+" : ""}${fmtUsd(perf.estimated_pnl_usd)}`}
          tone={perf.estimated_pnl_usd >= 0 ? "good" : "bad"}
        />
        <StatCard icon={<Receipt size={16} />} label="Paper Fills" value={`${perf.total_paper_fills}`} />
        <StatCard
          icon={<ShieldCheck size={16} />}
          label="Rejected by Gate"
          value={`${perf.rejected_by_gate}`}
          tone={perf.rejected_by_gate > 0 ? "bad" : "neutral"}
        />
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5">
        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-300">
          <LineChart size={16} /> Estimated Paper Equity Curve
        </h4>
        <Sparkline data={perf.equity_curve} />
        <div className="mt-2 flex flex-wrap justify-between gap-2 text-xs text-gray-500">
          <span>Premium collected: <span className="text-emerald-400">{fmtUsd(perf.estimated_premium_collected_usd)}</span></span>
          <span>Costs: <span className="text-red-400">{fmtUsd(perf.total_costs_usd)}</span></span>
          <span>Reserves locked: <span className="text-amber-400">{fmtUsd(perf.reserves_locked_usd)}</span></span>
        </div>
      </div>

      {perf.per_asset.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-gray-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="px-4 py-3 font-medium">Asset</th>
                <th className="px-4 py-3 font-medium">Fills</th>
                <th className="px-4 py-3 font-medium">Notional</th>
                <th className="px-4 py-3 font-medium">Est. Premium</th>
                <th className="px-4 py-3 font-medium">Costs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800 bg-gray-900/40">
              {perf.per_asset.map((a) => (
                <tr key={a.asset}>
                  <td className="px-4 py-3 font-semibold text-white">{a.asset}</td>
                  <td className="px-4 py-3 text-gray-300">{a.fills}</td>
                  <td className="px-4 py-3 text-gray-300">{fmtUsd(a.notional_usd)}</td>
                  <td className="px-4 py-3 text-emerald-400">{fmtUsd(a.premium_usd)}</td>
                  <td className="px-4 py-3 text-red-400">{fmtUsd(a.costs_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5">
        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-300">
          <History size={16} /> Activity Feed
        </h4>
        {perf.recent_activity.length === 0 ? (
          <p className="text-sm text-gray-500">No fills yet — click “Run underwriting cycle”.</p>
        ) : (
          <ul className="space-y-2">
            {perf.recent_activity.map((t, i) => (
              <li key={i} className="flex flex-wrap items-center gap-2 rounded-lg border border-gray-800 bg-gray-950 px-3 py-2 text-sm">
                <span className={`rounded px-2 py-0.5 text-xs font-semibold ${t.risk_verdict === "APPROVED" ? "bg-emerald-500/15 text-emerald-400" : "bg-red-500/15 text-red-400"}`}>
                  {t.risk_verdict}
                </span>
                <span className="font-semibold text-white">{t.symbol}</span>
                <span className="text-gray-400">{t.structure}</span>
                <span className={t.side === "SELL" ? "text-amber-400" : "text-sky-400"}>{t.side}</span>
                <span className="text-gray-300">{fmtUsd(Number(t.notional_usd))}</span>
                <span className="ml-auto truncate text-xs text-gray-500">{t.rationale}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TAB 4 — Global Intelligence & Macro Propagation
// ---------------------------------------------------------------------------
function IntelligenceTab() {
  const [links, setLinks] = useState<
    { source: string; channel: string; target: string; impact_pct: number; credibility: number }[]
  >([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/macro-propagation`)
      .then((r) => r.json())
      .then((d) => setLinks(d.links ?? []))
      .catch(() => setLinks([]));
  }, []);

  const channels = [
    { node: "Central Bank Rate Δ", color: "text-amber-400", icon: <Globe2 size={18} /> },
    { node: "Funding & Carry Costs", color: "text-sky-400", icon: <Waves size={18} /> },
    { node: "Implied Volatility Surface", color: "text-purple-400", icon: <Activity size={18} /> },
    { node: "Portfolio Loss Reserves", color: "text-emerald-400", icon: <ShieldCheck size={18} /> },
  ];

  const models = [
    { name: "EVT (GPD)", purpose: "Crash tail risk → CVaR / Expected Shortfall", confidence: "99% quantile", reliability: "High in tails, sparse data", trust: "Only model honest about fat tails; sizes the frozen reserve." },
    { name: "HMM", purpose: "Latent regime classification", confidence: "Posterior > 0.7", reliability: "Strong regime persistence", trust: "Detects regime shifts before vol confirms; gates risk appetite." },
    { name: "GARCH(1,1)", purpose: "Conditional vol & clustering forecast", confidence: "1-step σ band", reliability: "High intraday, mean-reverting", trust: "Calibrates position sizing to forecast volatility." },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5">
        <h4 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-300">
          <Globe2 size={16} /> Macro Shock Propagation
        </h4>
        <div className="flex flex-col items-stretch gap-2 md:flex-row md:items-center">
          {channels.map((c, i) => (
            <div key={c.node} className="flex flex-1 items-center gap-2">
              <div className="flex w-full flex-col items-center rounded-lg border border-gray-800 bg-gray-950 p-3 text-center">
                <span className={c.color}>{c.icon}</span>
                <span className="mt-1 text-xs text-gray-300">{c.node}</span>
              </div>
              {i < channels.length - 1 && <span className="hidden text-gray-600 md:block">→</span>}
            </div>
          ))}
        </div>
      </div>

      {links.length > 0 && (
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5">
          <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-gray-300">
            <Activity size={16} /> Fitted Propagation — VAR(1) Impulse Response
          </h4>
          <ul className="space-y-2 text-sm">
            {links.map((l, i) => (
              <li key={i} className="flex flex-wrap items-center gap-2 text-gray-300">
                <span className="font-mono text-xs text-amber-300">{l.source}</span>
                <span className="text-gray-600">→</span>
                <span className="font-mono text-xs text-sky-300">{l.channel}</span>
                <span className="text-gray-600">→</span>
                <span className="font-mono text-xs text-emerald-300">{l.target}</span>
                <span className="ml-auto text-xs text-gray-400">
                  peak {l.impact_pct.toFixed(1)} ·{" "}
                  <span className={l.credibility > 0.7 ? "text-emerald-400" : "text-amber-400"}>
                    credibility {(l.credibility * 100).toFixed(0)}%
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="overflow-hidden rounded-xl border border-gray-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-900 text-gray-400">
            <tr>
              <th className="px-4 py-3 font-medium">Model</th>
              <th className="px-4 py-3 font-medium">Purpose</th>
              <th className="px-4 py-3 font-medium">Confidence</th>
              <th className="px-4 py-3 font-medium">Reliability</th>
              <th className="px-4 py-3 font-medium">Why Trusted</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 bg-gray-900/40">
            {models.map((m) => (
              <tr key={m.name}>
                <td className="px-4 py-3 font-semibold text-white">{m.name}</td>
                <td className="px-4 py-3 text-gray-300">{m.purpose}</td>
                <td className="px-4 py-3 text-gray-300">{m.confidence}</td>
                <td className="px-4 py-3 text-gray-300">{m.reliability}</td>
                <td className="px-4 py-3 text-gray-400">{m.trust}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Root component
// ---------------------------------------------------------------------------
export default function Dashboard() {
  const [tab, setTab] = useState<TabKey>("briefing");
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [hasKeys, setHasKeys] = useState(true); // flip to false to force wizard

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/daily-briefing`)
      .then((r) => r.json())
      .then(setBriefing)
      .catch(() => setBriefing(null));
    fetch(`${API_BASE}/api/v1/fund-allocation`)
      .then((r) => r.json())
      .then((d) => setAllocations(d.allocations ?? []))
      .catch(() => setAllocations([]));
    if (!hasKeys) setShowOnboarding(true);
  }, [hasKeys]);

  const tabs = useMemo(
    () => [
      { key: "briefing" as const, label: "Daily Briefing", icon: <Gauge size={16} /> },
      { key: "allocation" as const, label: "Fund Allocation", icon: <Layers size={16} /> },
      { key: "performance" as const, label: "Performance", icon: <LineChart size={16} /> },
      { key: "intelligence" as const, label: "Global Intelligence", icon: <Globe2 size={16} /> },
    ],
    []
  );

  return (
    <div className="min-h-screen bg-gray-950 p-6 text-gray-100">
      {showOnboarding && <OnboardingModal onClose={() => { setShowOnboarding(false); setHasKeys(true); }} />}

      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldCheck className="text-emerald-400" size={28} />
          <div>
            <h1 className="text-xl font-bold">Actuarial Quant System</h1>
            <p className="text-xs text-gray-500">Capital-survival underwriting · paper / informational mode</p>
          </div>
        </div>
        <button
          onClick={() => setShowOnboarding(true)}
          className="flex items-center gap-2 rounded-lg border border-gray-700 px-3 py-2 text-sm text-gray-300 hover:bg-gray-800"
        >
          <KeyRound size={15} /> Link API Keys
        </button>
      </header>

      <nav className="mb-6 flex gap-2 border-b border-gray-800">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition ${
              tab === t.key
                ? "border-emerald-400 text-white"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === "briefing" && <BriefingTab data={briefing} />}
        {tab === "allocation" && <AllocationTab data={allocations} />}
        {tab === "performance" && <PerformanceTab />}
        {tab === "intelligence" && <IntelligenceTab />}
      </main>
    </div>
  );
}
