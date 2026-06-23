# Actuarial Quant System

A decoupled, capital-survival-first research stack that treats every trade as an
**underwritten insurance liability**. Backend math is pure `numpy`/`scipy`; the
engine runs 24/7 as a headless daemon and serves an on-demand Next.js portal.

> **Safety posture:** read-only / informational. `PAPER_TRADING_ONLY` defaults to
> `true`, the risk gate is hardcoded and AI-free, and the execution layer has **no
> withdrawal code path and no bank-network access** by construction. Execution
> stays disconnected until a validated paper track record exists.

## Architecture

```
actuarial_quant_system/
├── src/
│   ├── config.py                 # env wiring (NOT risk limits)
│   ├── data_pipeline/            # async WS feed + Redis pub/sub bus
│   │   └── stream_bus.py
│   ├── models/                   # pure actuarial & regime math
│   │   ├── actuarial_engine.py   # Cramér-Lundberg ruin, EVT/GPD CVaR, loss reserve
│   │   └── regime_models.py      # GARCH(1,1) + Gaussian HMM (Baum-Welch/Viterbi)
│   ├── risk_gate/                # hardcoded isolation firewall (fail-closed)
│   │   └── pre_trade_check.py
│   ├── execution/                # read-only broker adapter, withdrawal-blocked
│   │   └── broker_connector.py
│   └── api_dashboard/            # FastAPI orchestration
│       └── main.py
├── deploy/
│   └── actuarial-trading-engine.service   # systemd 24/7 daemon unit
└── frontend/components/Dashboard.tsx       # Next.js / Tailwind / lucide portal
```

## Run the backend

```bash
cd actuarial_quant_system
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edit as needed
uvicorn src.api_dashboard.main:app --host 127.0.0.1 --port 8200 --reload
```

Then: `http://127.0.0.1:8200/docs`

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/daily-briefing` | Tab-1 executive report payload (persisted) |
| `GET /api/v1/fund-allocation` | Tab-2 layers, aggregated from open positions |
| `GET /api/v1/regime` | GARCH + HMM regime snapshot |
| `GET /api/v1/signals` | Variance Risk Premium + underwriting signal per asset |
| `GET /api/v1/risk/ruin` | Cramér-Lundberg ruin probability |
| `GET /api/v1/macro-propagation` | SVAR / VAR(1) shock propagation + credibility (Tab 3) |
| `GET /api/v1/trades` | Recent paper fills (audit trail) |
| `POST /api/v1/cycle/run` | Trigger one paper underwriting cycle manually |
| `POST /api/v1/onboarding/validate` | Validate API keys (paper-safe), seed allocation |
| `POST /api/v1/reallocate` | Internal reallocation / deposit advice |

### Autonomous paper underwriting

On boot the daemon starts a background loop that, every `CYCLE_INTERVAL_SECONDS`,
runs the full pipeline per asset: **regime (HMM) → VRP signal → strategy structure
→ hardcoded risk gate → simulated fill → loss-reserve lock (Redis) → persist
(Postgres) → audit**. Every fill is paper-only; there is no live-order path.
State is restored from Redis on restart, so survival math survives a reboot.

### Frontend (Next.js)

```bash
cd frontend
cp .env.local.example .env.local      # point NEXT_PUBLIC_QUANT_API at the engine
npm install
npm run dev                           # http://localhost:3000
```

## Run the daemon (Linux, 24/7)

```bash
sudo cp deploy/actuarial-trading-engine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now actuarial-trading-engine
journalctl -u actuarial-trading-engine -f
```

## Frontend

`Dashboard.tsx` drops into a Next.js (App Router) project. Set
`NEXT_PUBLIC_QUANT_API=http://127.0.0.1:8200` and render `<Dashboard />`.
Requires `lucide-react` and Tailwind.

## Three independent safety layers (why it can't move your money)

1. **API-key scoping** — keys are minted READ (≤ TRADE) only; WITHDRAW disabled
   at the venue, so signed withdrawal requests are cryptographically rejected.
2. **No withdrawal code path** — there is no `withdraw()/transfer()/payout()`
   method anywhere; you can't call what doesn't exist.
3. **No bank reachability** — no ACH/SWIFT/wire/card rails; only HTTPS/WSS to the
   trading venue.
