import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Elexon API endpoints
ACTUALS_URL = "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream"
FORECAST_URL = "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/actuals")
def get_actuals():
    """Fetch actual wind generation data from Elexon."""
    try:
        params = {
            "fuelType": "WIND",
        }
        response = requests.get(ACTUALS_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            # Filter for January 2026 data
            jan_2026 = []
            for item in data.get("data", []):
                start_time = item.get("startTime", "")
                if start_time.startswith("2026-01"):
                    jan_2026.append(item)
            return jsonify({"success": True, "data": jan_2026})
        else:
            return jsonify({"success": False, "error": f"API returned {response.status_code}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/forecasts")
def get_forecasts():
    """Fetch wind forecast data from Elexon."""
    try:
        params = {}
        response = requests.get(FORECAST_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            # Filter for January 2026 data
            jan_2026 = []
            for item in data.get("data", []):
                start_time = item.get("startTime", "")
                if start_time.startswith("2026-01"):
                    jan_2026.append(item)
            return jsonify({"success": True, "data": jan_2026})
        else:
            return jsonify({"success": False, "error": f"API returned {response.status_code}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/accuracy")
def get_accuracy():
    """Calculate accuracy of forecasts vs actuals."""
    try:
        actuals_response = requests.get("/api/actuals")
        forecasts_response = requests.get("/api/forecasts")

        if actuals_response.status_code != 200 or forecasts_response.status_code != 200:
            return jsonify({"success": False, "error": "Failed to fetch data"})

        actuals = actuals_response.json().get("data", [])
        forecasts = forecasts_response.json().get("data", [])

        # Build a lookup of actuals by startTime
        actuals_by_time = {}
        for item in actuals:
            start_time = item.get("startTime", "")
            generation = item.get("generation", 0)
            actuals_by_time[start_time] = generation

        # Match forecasts with actuals and calculate errors
        accuracy_data = []
        total_error = 0
        count = 0

        for forecast in forecasts:
            start_time = forecast.get("startTime", "")
            publish_time = forecast.get("publishTime", "")
            forecast_generation = forecast.get("generation", 0)

            actual_generation = actuals_by_time.get(start_time, 0)
            error = abs(forecast_generation - actual_generation)
            percentage_error = (error / max(actual_generation, 1)) * 100

            accuracy_data.append({
                "startTime": start_time,
                "publishTime": publish_time,
                "forecast": forecast_generation,
                "actual": actual_generation,
                "error": error,
                "percentageError": round(percentage_error, 2)
            })

            total_error += error
            count += 1

        avg_error = total_error / max(count, 1)
        avg_percentage_error = (avg_error / max(avg_error, 1)) * 100 if count > 0 else 0

        summary = {
            "totalSamples": count,
            "averageError": round(avg_error, 2),
            "averagePercentageError": round(avg_percentage_error, 2),
            "maxPercentageError": max([d["percentageError"] for d in accuracy_data], default=0)
        }

        return jsonify({
            "success": True,
            "data": accuracy_data,
            "summary": summary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)