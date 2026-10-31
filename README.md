# UK Wind Power Forecast & Accuracy Dashboard

A web application for UK energy utility day-ahead market procurement teams to:

1. **View the latest wind generation forecasts** for January 2026 (WINDFOR dataset)
2. **Evaluate forecast accuracy** against actuals (FUELHH dataset) with MAE, RMSE, MAPE metrics

Built with **React + Chart.js** (frontend) and **Python Flask** (backend), containerised with **Docker**.

> **AI Assistance:** This application was built with assistance from Google Gemini (Antigravity AI coding assistant).

---

## Live Demo

🔗 **Deployed App:** _(add your Vercel/Heroku URL here after deployment)_

---

## Project Structure

```
as/
├── backend/
│   ├── app.py               # Flask API server (actuals, forecasts, accuracy endpoints)
│   └── requirements.txt     # Python dependencies (Flask, requests)
├── frontend/
│   └── react-app/
│       ├── src/
│       │   ├── App.jsx      # Main React component with charts and tables
│       │   ├── App.css      # Responsive styles
│       │   └── main.jsx     # React entry point
│       ├── package.json     # Node dependencies (React, Chart.js, react-chartjs-2)
│       └── vite.config.js   # Vite build config
├── Dockerfile               # Multi-stage Docker build
├── vercel.json              # Vercel deployment configuration
└── README.md
```

---

## Data Sources

| Dataset | Endpoint | Description |
|---------|----------|-------------|
| **FUELHH** | `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH` | Actual half-hourly generation by fuel type (WIND) |
| **WINDFOR** | `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR` | Day-ahead wind generation forecasts |

The app filters data for **January 2026** only. If the Elexon API is unreachable, it falls back to realistic simulated data (1488 half-hour slots, Jan 2026).

---

## How to Run Locally

### Option 1 – Docker (recommended)

```bash
# Build the image
docker build -t wind-forecast .

# Run it
docker run -p 5000:5000 wind-forecast
```

Open **http://localhost:5000** and click **Generate Analysis**.

### Option 2 – Manual (dev mode)

**Backend:**
```bash
pip install -r backend/requirements.txt
python backend/app.py
# Flask listens on http://localhost:5000
```

**Frontend (separate terminal):**
```bash
cd frontend/react-app
npm install
npm run dev
# Vite dev server on http://localhost:5173
```

When running in dev mode, update the `API` constant in `App.jsx` to `http://localhost:5000` if CORS issues arise.

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/actuals` | Actual WIND generation (Jan 2026, half-hourly) |
| `GET /api/forecasts` | Wind generation forecasts (Jan 2026) |
| `GET /api/accuracy` | Accuracy analysis: MAE, RMSE, MAPE, daily summary, per-slot data |

---

## Key Features

- 📊 **Line chart** – daily avg actual vs forecast (Jan 2026)
- 📉 **Bar chart** – daily average absolute error with RAG colouring
- 🗂 **Full data table** – 1488 half-hour rows with colour-coded error bands
- 📐 **Metrics** – MAE, RMSE, MAPE, Mean Bias, Max % Error
- 🔄 **Resilient** – graceful fallback to simulated data if Elexon API unavailable
- 📱 **Responsive** – works on desktop and mobile

---

## Deployment on Heroku (Docker)

```bash
heroku login
heroku create <your-app-name>
heroku container:push web -a <your-app-name>
heroku container:release web -a <your-app-name>
heroku open -a <your-app-name>
```

## Deployment on Vercel

Push to GitHub and import the repository in [vercel.com/new](https://vercel.com/new).  
Vercel detects the `Dockerfile` and builds automatically.
