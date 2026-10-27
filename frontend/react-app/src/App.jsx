import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [actualsData, setActualsData] = useState(null);
  const [forecastsData, setForecastsData] = useState(null);
  const [accuracyData, setAccuracyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchActuals = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/actuals');
      const data = await response.json();
      if (data.success) {
        setActualsData(data.data);
      } else {
        setError('Failed to fetch actuals: ' + (data.error || ''));
      }
    } catch (err) {
      setError('Error fetching actuals: ' + err);
    } finally {
      setLoading(false);
    }
  };

  const fetchForecasts = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/forecasts');
      const data = await response.json();
      if (data.success) {
        setForecastsData(data.data);
      } else {
        setError('Failed to fetch forecasts: ' + (data.error || ''));
      }
    } catch (err) {
      setError('Error fetching forecasts: ' + err);
    } finally {
      setLoading(false);
    }
  };

  const calculateAccuracy = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/accuracy');
      const data = await response.json();
      if (data.success) {
        setAccuracyData(data);
      } else {
        setError('Failed to calculate accuracy: ' + (data.error || ''));
      }
    } catch (err) {
      setError('Error calculating accuracy: ' + err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateClick = () => {
    fetchActuals();
    fetchForecasts();
    calculateAccuracy();
  };

  return (
    <div className="app-container">
      <header>
        <h1>UK Wind Power Forecast & Accuracy</h1>
        <p>Energy Utility - Day-Ahead Market Planning</p>
      </header>

      <main>
        <div class="controls">
          <button
            onClick={handleGenerateClick}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Generating...' : 'Generate Analysis'}
          </button>
        </div>

        {error && (
          <div className="error-banner">
            <p>{error}</p>
          </div>
        )}

        {loading && !accuracyData && (
          <div className="loading-spinner">
            <p>Loading data from Elexon APIs...</p>
          </div>
        )}

        {accuracyData && (
          <div class="results-section">
            <h2>Forecast Accuracy Analysis</h2>

            <div class="summary-stats">
              <div class="stat-card">
                <h3>Total Samples</h3>
                <p>{accuracyData.summary.totalSamples}</p>
              </div>
              <div class="stat-card">
                <h3>Avg Error (MW)</h3>
                <p>{accuracyData.summary.averageError}</p>
              </div>
              <div class="stat-card">
                <h3>Avg % Error</h3>
                <p>{accuracyData.averagePercentageError}%</p>
              </div>
              <div class="stat-card">
                <h3>Max % Error</h3>
                <p>{accuracyData.maxPercentageError}%</p>
              </div>
            </div>

            <div class="table-container">
              <h3>Detailed Accuracy Data</h3>
              <table>
                <thead>
                  <tr>
                    <th>Start Time</th>
                    <th>Publish Time</th>
                    <th>Forecast (MW)</th>
                    <th>Actual (MW)</th>
                    <th>Error (MW)</th>
                    <th>% Error</th>
                  </tr>
                </thead>
                <tbody>
                  {accuracyData.data.map((item, index) => (
                    <tr key={index}>
                      <td>{item.startTime}</td>
                      <td>{item.publishTime}</td>
                      <td>{item.forecast}</td>
                      <td>{item.actual}</td>
                      <td>{item.error}</td>
                      <td>{item.percentageError}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!accuracyData && (
          <div class="info-section">
            <p>Click 'Generate Analysis' to load wind power data from the Elexon APIs and calculate forecast accuracy.</p>
            <p>
              The application fetches actual wind generation data and forecasts from the UK
              day-ahead market, then compares them to quantify forecast accuracy.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;