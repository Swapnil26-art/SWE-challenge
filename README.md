# UK Wind Power Forecast & Accuracy Dashboard

A web application for a UK energy utility's **day-ahead market procurement team**:

1. **View the day-ahead wind generation forecasts** — exactly the forecast information a trader had available at the January 2026 purchase decision point (latest WINDFOR publication before each delivery day's gate closure)
2. **Evaluate forecast accuracy quantitatively** against actual generation (FUELHH) with MAE, RMSE, MAPE, mean bias and daily error breakdowns

Built with **React + Vite + Chart.js** (frontend) and **Python Flask** (backend), containerised with **Docker**, deployable as a single Vercel project.

> **AI Assistance (declared per requirements):** This application was built with assistance from AI coding tools (Google Gemini / Antigravity, and OpenCode with GLM). All design decisions, data verification against the live Elexon API and testing were done manually.

---

## Live Demo

🔗 **Deployed App:** https://swe-challenge-wind.vercel.app  <!-- TODO: replace with the final URL after `vercel deploy --prod` -->

Health check: `/api/health`

---

## Project Structure

```
as/
├── api/
│   └── index.py            # Vercel serverless entry point → re-exports the Flask app
├── backend/
│   ├── app.py              # Flask API: actuals, day-ahead forecasts, accuracy endpoints
│   └── requirements.txt
├── frontend/react-app/
│   ├── src/
│   │   ├── App.jsx         # Dashboard: KPI cards, charts, error distribution, data table
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js      # Dev proxy → Flask on :5000
├── Dockerfile              # Multi-stage: build React, serve via Flask
├── vercel.json             # Vercel build + /api rewrites + function duration
├── requirements.txt        # Dependencies for the Vercel Python runtime
└── README.md
```

---

## Data Sources (Elexon BMRS Insights Solution API)

| Dataset | Endpoint | Description |
|---------|----------|-------------|
| **FUELHH** | `GET /datasets/FUELHH/stream?fuelType=WIND&settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31` | Actual half-hourly national wind generation for every January 2026 delivery day (1488 slots) |
| **WINDFOR** | `GET /datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-02-01T00:00:00Z` | Wind generation forecast publications (~every 3 h, each covering D-1 → D+2), each record carries `startTime`, `publishTime`, `generation` |

**Key API note:** the non-stream `/datasets/{DATASET}` endpoints silently ignore date-range query
parameters (verified live: a January query returns current-day records), so the app uses the
`/stream` variants with server-side date filters.

---

## Methodology

1. **Day-ahead decision view.** For each January 2026 delivery hour, the app selects the
   *latest* WINDFOR forecast **published before 09:00 UTC on D-1** (day-ahead gate closure),
   mirroring what the trader actually saw when committing purchases. Intraday updates
   published after the gate are excluded from accuracy evaluation.
2. **Resolution matching.** WINDFOR forecasts are hourly-resolved while FUELHH actuals are
   half-hourly; each hour's actual is the mean of its two half-hourly readings, so the
   comparison has no resolution bias (≈744 hourly samples).
3. **Accuracy metrics.** MAE, RMSE, MAPE, mean bias and worst-case % error, plus per-day
   buckets used by the charts and an error-distribution breakdown (<5 %, 5–10 %, 10–20 %,
   >20 % of slots).

January 2026 headline result (live Elexon data): **MAE ≈ 2 100 MW, RMSE ≈ 2 600 MW,
MAPE ≈ 22 %, mean bias ≈ +1 850 MW (systematic over-forecast)** — the team should hold
back part of any wind-derived procurement because forecasts read on average high.

If the upstream API is unreachable the backend serves clearly-labelled simulated
January 2026 data (`"source": "fallback"`), shown as a badge in the UI rather than silently.

---

## How to Run Locally

### Option 1 – Docker (recommended)

```bash
docker build -t wind-forecast .
docker run -p 5000:5000 wind-forecast
```

Open **http://localhost:5000** — the analysis loads automatically; use **ANALYSE** to refresh.

### Option 2 – Manual (dev mode)

**Backend:**
```bash
pip install -r backend/requirements.txt
python backend/app.py   # http://localhost:5000
```

**Frontend (separate terminal):**
```bash
cd frontend/react-app
npm install
npm run dev             # http://localhost:5173 (proxies /api to :5000)
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Liveness + configuration status |
| `GET /api/actuals` | Actual WIND generation, Jan 2026, half-hourly (FUELHH) |
| `GET /api/forecasts` | Day-ahead forecast per hour — latest publication before gate closure (WINDFOR) |
| `GET /api/accuracy` | Joined hourly dataset, per-day summary, MAE / RMSE / MAPE / bias + `forecastBasis` explanation |

---

## Deployment

### Vercel (single project, frontend + Python serverless backend)

1. Push the repo to GitHub and import it at [vercel.com/new](https://vercel.com/new), or run `vercel --prod` locally.
2. Vercel builds the React bundle (`npm run build --prefix frontend/react-app`) and deploys `/api/*` as Python serverless functions from `api/index.py` (dependencies come from the root `requirements.txt`; function duration capped at 30 s via `vercel.json`).

### Environment Variables (Vercel → Project Settings → Environment Variables)

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `ELEXON_API_KEY` (`BMRS_API_KEY` / `API_KEY` aliases) | Optional | Elexon key. The public BMRS API works without one; if provided it is forwarded as `x-api-key` / `Ocp-Apim-Subscription-Key` header and `api_key` query parameter. |
| `APP_API_KEY` (`BACKEND_API_KEY`) | Optional | Protects `/api/*` — requests must then send the value in `x-api-key` or `Authorization: Bearer <key>`. |
| `VITE_APP_API_KEY` | Optional | Frontend copy of `APP_API_KEY`, injected at build time and sent automatically. |
| `VITE_API_URL` | Optional | Override backend URL. Defaults to same origin on Vercel/Docker. |

Example `.env.example` is included; **never commit real secrets**.

### Heroku (Docker) — alternative

```bash
heroku login
heroku create <app-name>
heroku container:push web -a <app-name>
heroku container:release web -a <app-name>
heroku open -a <app-name>
```
