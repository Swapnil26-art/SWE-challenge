import os
import math
import random
import requests
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, request

# ── Static folder setup ────────────────────────────────────────────────────────
_local_dist = os.path.join(os.path.dirname(__file__), "../frontend/react-app/dist")
STATIC_FOLDER = os.environ.get("STATIC_FOLDER", os.path.abspath(_local_dist))
app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path="")

# ── Environment & API Keys ─────────────────────────────────────────────────────
# Elexon BMRS API key (optional - public API works without a key, but supports
# custom/subscription keys if provided)
ELEXON_API_KEY = (
    os.environ.get("ELEXON_API_KEY")
    or os.environ.get("BMRS_API_KEY")
    or os.environ.get("API_KEY")
    or ""
).strip()

# Internal API key to protect backend endpoints (optional)
APP_API_KEY = (
    os.environ.get("APP_API_KEY")
    or os.environ.get("BACKEND_API_KEY")
    or ""
).strip()

# ── CORS ───────────────────────────────────────────────────────────────────────
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, x-api-key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.before_request
def handle_preflight_and_auth():
    # Respond immediately to preflight OPTIONS requests
    if request.method == "OPTIONS":
        return "", 204

    # If an APP_API_KEY is configured, enforce it on API endpoints (health stays open)
    if APP_API_KEY and request.path.startswith("/api/") and not request.path.startswith("/api/health"):
        auth_header = request.headers.get("Authorization", "")
        key = request.headers.get("x-api-key") or request.args.get("api_key")
        if auth_header.startswith("Bearer "):
            key = auth_header.split(" ", 1)[1]
        if key != APP_API_KEY:
            return jsonify({"success": False, "error": "Unauthorized: Invalid or missing API key"}), 401
    return None

# ── Elexon BMRS API (Insights Solution, /stream endpoints) ────────────────────
# NOTE: The non-stream /datasets/{DATASET} endpoint ignores date-range params,
# so we use the /stream variants with server-side date filters.
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
FUELHH_URL  = f"{BASE_URL}/datasets/FUELHH/stream"    # actual half-hourly generation
WINDFOR_URL = f"{BASE_URL}/datasets/WINDFOR/stream"   # wind generation forecasts

# Analysis window: delivery days in January 2026 (all times UTC)
JAN_START = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
JAN_END   = datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc)

# Day-ahead gate closure: day-ahead market decisions must be made before
# 09:00 UTC on the day BEFORE delivery (D-1). WINDFOR forecasts published
# after this time are intraday updates and are not available at decision time.
GATE_HOUR = 9


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_z(ts):
    """Parse ISO timestamps like '2026-01-08T21:00:00Z' (or without seconds)."""
    if not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(ts.replace("Z", "+00:00") if "Z" in ts else ts, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


# ── Fallback sample data (only used if Elexon API is unreachable) ─────────────
def _build_jan2026():
    random.seed(42)
    start = JAN_START
    actuals, forecasts = [], []
    for i in range(1488):
        ts = start + timedelta(minutes=30 * i)
        iso = _iso(ts)

        h = ts.hour + ts.minute / 60
        d = ts.day
        base = 2500
        diurnal = 600 * math.sin(2 * math.pi * h / 24 - math.pi / 2)
        weekly  = 400 * math.sin(2 * math.pi * d / 7)
        storm   = 800 * math.sin(2 * math.pi * d / 14)   # ~2-week storm cycle

        actual_gen   = max(0, round(base + diurnal + weekly + storm + random.gauss(0, 200)))
        forecast_gen = max(0, round(base + diurnal + weekly + storm + random.gauss(0, 180) + 80))

        pub_ts = ts - timedelta(hours=14, minutes=random.choice([30, 90]))  # pre-gate publishes
        forecasts.append({"startTime": iso, "publishTime": _iso(pub_ts), "generation": forecast_gen})
        actuals.append({"startTime": iso, "fuelType": "WIND", "generation": actual_gen})
    return actuals, forecasts

_FB_ACTUALS, _FB_FORECASTS = _build_jan2026()


# ── Elexon fetch with in-process cache ─────────────────────────────────────────
_CACHE = {}
_CACHE_TTL = timedelta(hours=6)


def _fetch_json_cached(url, params):
    key = (url, tuple(sorted(params.items())))
    hit = _CACHE.get(key)
    if hit and datetime.now(timezone.utc) - hit[0] < _CACHE_TTL:
        return hit[1]

    headers = {"Accept": "application/json", "User-Agent": "UK-Wind-Power-Dashboard/1.0"}
    if ELEXON_API_KEY:
        headers["x-api-key"] = ELEXON_API_KEY
        headers["Ocp-Apim-Subscription-Key"] = ELEXON_API_KEY
        params = {**params, "api_key": ELEXON_API_KEY}

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    _CACHE[key] = (datetime.now(timezone.utc), data)
    return data


def _fetch_actuals():
    """Actual half-hourly WIND generation for every January 2026 delivery day."""
    body = _fetch_json_cached(FUELHH_URL, {
        "fuelType": "WIND",
        "settlementDateFrom": "2026-01-01",
        "settlementDateTo": "2026-01-31",
    })
    records = body if isinstance(body, list) else body.get("data", [])
    return [r for r in records
            if isinstance(r, dict)
            and (r.get("fuelType") in (None, "WIND"))
            and (r.get("startTime") or "").startswith("2026-01")]


def _fetch_forecasts():
    """
    All WINDFOR forecast publications covering January 2026 delivery slots.
    We request by publishTime so we definitely capture the publications that
    traders could see before each delivery day's day-ahead gate closure
    (including publications made on 31 Dec for 1 Jan delivery).
    """
    body = _fetch_json_cached(WINDFOR_URL, {
        "publishDateTimeFrom": "2025-12-30T00:00:00Z",
        "publishDateTimeTo":   "2026-02-01T00:00:00Z",
    })
    records = body if isinstance(body, list) else body.get("data", [])
    return [r for r in records
            if isinstance(r, dict)
            and (r.get("startTime") or "").startswith("2026-01")]


def _day_ahead_selection(forecasts_raw):
    """
    For each Jan-2026 delivery slot keep the LATEST forecast published BEFORE
    that slot's day-ahead gate closure (09:00 UTC on D-1), i.e. exactly the
    information a trader had available when committing purchases.
    """
    best = {}
    for r in forecasts_raw:
        st = r.get("startTime") or ""
        pt = _parse_z(r.get("publishTime", ""))
        st_dt = _parse_z(st)
        if not st or not pt or not st_dt:
            continue
        gate = (st_dt - timedelta(days=1)).replace(hour=GATE_HOUR, minute=0, second=0, microsecond=0)
        if pt > gate:                       # intraday update - not visible at gate
            continue
        cur = best.get(st)
        if not cur or pt > cur[0]:
            best[st] = (pt, r.get("generation") or 0)
    return best


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    try:
        return app.send_static_file("index.html")
    except Exception:
        return "<p>React build not found. Run <code>npm run build</code>.</p>", 404


@app.route("/api/health")
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "elexon_api_key_configured": bool(ELEXON_API_KEY),
        "app_api_key_configured": bool(APP_API_KEY),
        "environment": os.environ.get("VERCEL_ENV", "development"),
    })


@app.route("/api/actuals")
@app.route("/actuals")
def get_actuals():
    source = "elexon"
    try:
        data = _fetch_actuals()
    except Exception:
        data = _FB_ACTUALS
        source = "fallback"
    if not data:
        data, source = _FB_ACTUALS, "fallback"
    return jsonify({"success": True, "data": data, "source": source, "count": len(data)})


@app.route("/api/forecasts")
@app.route("/forecasts")
def get_forecasts():
    source = "elexon"
    data = None
    try:
        selected = _day_ahead_selection(_fetch_forecasts())
        data = [{"startTime": st, "publishTime": _iso(pt), "generation": gen}
                for st, (pt, gen) in sorted(selected.items())]
    except Exception:
        data = None
    if not data:
        data, source = _FB_FORECASTS, "fallback"
    return jsonify({"success": True, "data": data, "source": source, "count": len(data)})


def _hour_key(ts_str):
    """Collapse any 30-min/hourly startTime to its containing hour as a datetime."""
    dt = _parse_z(ts_str)
    if not dt:
        return None
    return dt.replace(minute=0, second=0, microsecond=0)


def _hourly_average(records, value_field="generation"):
    """Average records into hourly buckets. FUELHH is half-hourly: the two
    half-hourly readings of an hour are averaged to match WINDFOR's hourly
    forecast resolution."""
    buckets = {}
    for r in records:
        hk = _hour_key(r.get("startTime", ""))
        if hk is None:
            continue
        buckets.setdefault(hk, []).append(r.get(value_field) or 0)
    return {hk: sum(v) / len(v) for hk, v in buckets.items()}


def _build_rows(actuals_raw, forecasts_raw):
    """Join day-ahead forecasts with actuals on the hour (both series are
    hourly-resolved after aggregation)."""
    actuals_hourly = _hourly_average(actuals_raw)

    # Day-ahead forecast per delivery slot, grouped by hour
    selected = _day_ahead_selection(forecasts_raw)
    forecast_hourly, publish_hourly = {}, {}
    for st, (pt, gen) in selected.items():
        hk = _hour_key(st)
        if hk is None:
            continue
        forecast_hourly.setdefault(hk, []).append(gen)
        if hk not in publish_hourly or pt > publish_hourly[hk]:
            publish_hourly[hk] = pt

    rows = []
    for hk in sorted(forecast_hourly):
        if hk not in actuals_hourly:
            continue
        fct = sum(forecast_hourly[hk]) / len(forecast_hourly[hk])
        act = actuals_hourly[hk]
        err = fct - act
        abs_err = abs(err)
        pct = (abs_err / max(abs(act), 1)) * 100
        rows.append({
            "startTime":       _iso(hk),
            "publishTime":     _iso(publish_hourly[hk]),
            "actual":          round(act, 1),
            "forecast":        round(fct, 1),
            "error":           round(err, 1),
            "absError":        round(abs_err, 1),
            "percentageError": round(pct, 2),
        })
    return rows


FORECAST_BASIS = ("Day-ahead view: latest WINDFOR forecast published before 09:00 UTC on "
                  "the day before delivery (day-ahead gate closure). Forecasts are hourly; "
                  "half-hourly actuals are averaged to the hour for comparison.")


@app.route("/api/accuracy")
@app.route("/accuracy")
def get_accuracy():
    source = "elexon"
    try:
        actuals_raw, forecasts_raw = _fetch_actuals(), _fetch_forecasts()
        if not actuals_raw or not forecasts_raw:
            raise ValueError("Elexon returned no January 2026 data")
    except Exception:
        # API unreachable / bad shape -> fall back so the dashboard still works,
        # and be transparent that data is simulated.
        actuals_raw, forecasts_raw = _FB_ACTUALS, _FB_FORECASTS
        source = "fallback"

    rows = _build_rows(actuals_raw, forecasts_raw)
    if not rows:
        # One side live, other empty -> never show a blank dashboard.
        actuals_raw, forecasts_raw = _FB_ACTUALS, _FB_FORECASTS
        source = "fallback"
        rows = _build_rows(actuals_raw, forecasts_raw)

    abs_errors = [r["absError"] for r in rows]
    sq_errors  = [r["error"] ** 2 for r in rows]
    pct_errors = [r["percentageError"] for r in rows]
    biases     = [r["error"] for r in rows]

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
        "success":        True,
        "source":         source,
        "forecastBasis":  FORECAST_BASIS,
        "data":           rows,
        "dailySummary":   daily_summary,
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
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Not found"}), 404
    try:
        return app.send_static_file("index.html")
    except Exception:
        return "Not found", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
