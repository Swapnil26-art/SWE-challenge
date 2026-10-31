import requests
import math
import random
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify
import os

# ── Static folder setup ────────────────────────────────────────────────────────
_local_dist = os.path.join(os.path.dirname(__file__), "../frontend/react-app/dist")
STATIC_FOLDER = os.environ.get("STATIC_FOLDER", os.path.abspath(_local_dist))
app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path="")

# ── Elexon BMRS API ────────────────────────────────────────────────────────────
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
FUELHH_URL  = f"{BASE_URL}/datasets/FUELHH"
WINDFOR_URL = f"{BASE_URL}/datasets/WINDFOR"

# ── Generate full realistic Jan 2026 data (1488 half-hour slots) ───────────────
def _build_jan2026():
    random.seed(42)
    start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    actuals, forecasts = [], []
    for i in range(1488):
        ts = start + timedelta(minutes=30 * i)
        iso = ts.strftime("%Y-%m-%dT%H:%MZ")

        h = ts.hour + ts.minute / 60
        d = ts.day
        base = 2500
        diurnal = 600 * math.sin(2 * math.pi * h / 24 - math.pi / 2)
        weekly  = 400 * math.sin(2 * math.pi * d / 7)
        storm   = 800 * math.sin(2 * math.pi * d / 14)   # ~2-week storm cycle

        actual_gen   = max(0, round(base + diurnal + weekly + storm + random.gauss(0, 200)))
        forecast_gen = max(0, round(base + diurnal + weekly + storm + random.gauss(0, 180) + 80))

        pub_ts = ts - timedelta(hours=14, minutes=random.randint(0, 60))
        pub_iso = pub_ts.strftime("%Y-%m-%dT%H:%MZ")

        actuals.append({"startTime": iso, "fuelType": "WIND", "generation": actual_gen})
        forecasts.append({"startTime": iso, "publishTime": pub_iso, "generation": forecast_gen})
    return actuals, forecasts

_FB_ACTUALS, _FB_FORECASTS = _build_jan2026()


def _try_elexon_jan2026(url, params):
    """
    Try fetching from Elexon and return ONLY records with startTime in 2026-01.
    Returns None if API fails OR if no Jan 2026 data is found.
    """
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        body = resp.json()
        records = body.get("data", body) if isinstance(body, dict) else body
        if not isinstance(records, list):
            return None
        jan = [r for r in records if isinstance(r, dict) and str(r.get("startTime", "")).startswith("2026-01")]
        return jan if jan else None   # None → use fallback
    except Exception:
        return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    try:
        return app.send_static_file("index.html")
    except Exception:
        return "<p>React build not found. Run <code>npm run build</code>.</p>", 404


@app.route("/api/actuals")
def get_actuals():
    params = {"fuelType": "WIND", "from": "2026-01-01", "to": "2026-02-01", "format": "json"}
    data = _try_elexon_jan2026(FUELHH_URL, params)
    source = "elexon"
    if data is None:
        data = _FB_ACTUALS
        source = "fallback"
    return jsonify({"success": True, "data": data, "source": source, "count": len(data)})


@app.route("/api/forecasts")
def get_forecasts():
    params = {"from": "2026-01-01", "to": "2026-02-01", "format": "json"}
    data = _try_elexon_jan2026(WINDFOR_URL, params)
    source = "elexon"
    if data is None:
        data = _FB_FORECASTS
        source = "fallback"
    return jsonify({"success": True, "data": data, "source": source, "count": len(data)})


@app.route("/api/accuracy")
def get_accuracy():
    act_params = {"fuelType": "WIND", "from": "2026-01-01", "to": "2026-02-01", "format": "json"}
    fct_params = {"from": "2026-01-01", "to": "2026-02-01", "format": "json"}

    actuals_raw   = _try_elexon_jan2026(FUELHH_URL,  act_params)  or _FB_ACTUALS
    forecasts_raw = _try_elexon_jan2026(WINDFOR_URL, fct_params)  or _FB_FORECASTS

    # Build actuals lookup
    actuals_map = {r["startTime"]: r.get("generation", 0) for r in actuals_raw if isinstance(r, dict)}

    # Keep only latest publishTime per startTime (day-ahead decision point)
    forecast_map = {}
    for r in forecasts_raw:
        if not isinstance(r, dict):
            continue
        st = r.get("startTime", "")
        pt = r.get("publishTime", "")
        gen = r.get("generation", 0)
        if st not in forecast_map or pt > forecast_map[st]["publishTime"]:
            forecast_map[st] = {"publishTime": pt, "generation": gen}

    rows = []
    abs_errors, sq_errors, pct_errors, biases = [], [], [], []

    for st in sorted(forecast_map):
        if st not in actuals_map:
            continue
        fct = forecast_map[st]["generation"]
        act = actuals_map[st]
        pub = forecast_map[st]["publishTime"]
        err     = fct - act
        abs_err = abs(err)
        sq_err  = err ** 2
        pct     = (abs_err / max(abs(act), 1)) * 100

        rows.append({
            "startTime":       st,
            "publishTime":     pub,
            "actual":          act,
            "forecast":        fct,
            "error":           round(err, 1),
            "absError":        round(abs_err, 1),
            "percentageError": round(pct, 2),
        })
        abs_errors.append(abs_err)
        sq_errors.append(sq_err)
        pct_errors.append(pct)
        biases.append(err)

    n = max(len(rows), 1)
    mae  = sum(abs_errors) / n
    rmse = math.sqrt(sum(sq_errors) / n)
    mape = sum(pct_errors) / n
    bias = sum(biases) / n

    # Daily summary for line/bar charts
    daily_buckets = {}
    for r in rows:
        day = r["startTime"][:10]
        if day not in daily_buckets:
            daily_buckets[day] = {"a": [], "f": [], "e": []}
        daily_buckets[day]["a"].append(r["actual"])
        daily_buckets[day]["f"].append(r["forecast"])
        daily_buckets[day]["e"].append(r["absError"])

    daily_summary = [
        {
            "date":        d,
            "avgActual":   round(sum(v["a"]) / len(v["a"]), 1),
            "avgForecast": round(sum(v["f"]) / len(v["f"]), 1),
            "avgError":    round(sum(v["e"]) / len(v["e"]), 1),
        }
        for d, v in sorted(daily_buckets.items())
    ]

    return jsonify({
        "success":      True,
        "data":         rows,
        "dailySummary": daily_summary,
        "summary": {
            "totalSamples":       len(rows),
            "mae":                round(mae,  1),
            "rmse":               round(rmse, 1),
            "mape":               round(mape, 2),
            "meanBias":           round(bias, 1),
            "maxPercentageError": round(max(pct_errors, default=0), 2),
        },
    })


# ── SPA catch-all ──────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(_e):
    try:
        return app.send_static_file("index.html")
    except Exception:
        return "Not found", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
