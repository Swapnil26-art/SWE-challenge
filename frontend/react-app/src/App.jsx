import React, { useState } from 'react';
import './App.css';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend, Filler
);

const API = window.location.origin;

function StatCard({ label, value, unit = '', color = '#6366f1', sub = '' }) {
  return (
    <div className="stat-card" style={{ borderTop: `4px solid ${color}` }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color }}>
        {value}<span className="stat-unit">{unit}</span>
      </div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

function LoadingBar() {
  return (
    <div className="loading-container">
      <div className="loading-bar"><div className="loading-fill" /></div>
      <p>Fetching wind power data from Elexon BMRS API…</p>
    </div>
  );
}

export default function App() {
  const [state, setState] = useState({
    loading: false,
    error: null,
    accuracy: null,
    activeTab: 'overview',
    dataSource: '',
  });

  const fetchAll = async () => {
    setState(s => ({ ...s, loading: true, error: null, accuracy: null }));
    try {
      const res = await fetch(`${API}/api/accuracy`);
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const json = await res.json();
      if (!json.success) throw new Error(json.error || 'API returned failure');
      setState(s => ({
        ...s, loading: false, accuracy: json,
        dataSource: json.source === 'elexon' ? 'Live – Elexon BMRS API' : 'Demo – Simulated Jan 2026 data',
      }));
    } catch (err) {
      setState(s => ({ ...s, loading: false, error: err.message }));
    }
  };

  const { loading, error, accuracy, activeTab, dataSource } = state;
  const summary = accuracy?.summary;
  const daily = accuracy?.dailySummary || [];
  const rows = accuracy?.data || [];

  // ── Chart data ──────────────────────────────────────────────────────────────
  const lineData = {
    labels: daily.map(d => d.date.slice(5)),   // "MM-DD"
    datasets: [
      {
        label: 'Actual (MW)',
        data: daily.map(d => d.avgActual),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16,185,129,0.08)',
        fill: true,
        tension: 0.4,
        pointRadius: 2,
      },
      {
        label: 'Forecast (MW)',
        data: daily.map(d => d.avgForecast),
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99,102,241,0.08)',
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        borderDash: [5, 3],
      },
    ],
  };

  const errData = {
    labels: daily.map(d => d.date.slice(5)),
    datasets: [
      {
        label: 'Daily Avg Error (MW)',
        data: daily.map(d => Math.abs(d.avgForecast - d.avgActual)),
        backgroundColor: daily.map(d => {
          const e = Math.abs(d.avgForecast - d.avgActual);
          return e > 300 ? '#ef4444' : e > 150 ? '#f59e0b' : '#10b981';
        }),
        borderRadius: 4,
      },
    ],
  };

  const chartOpts = (title, yLabel) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: title, font: { size: 14, weight: '600' } },
    },
    scales: {
      x: { ticks: { maxTicksLimit: 10 } },
      y: { title: { display: true, text: yLabel } },
    },
  });

  // ── Error band: count slots by error bucket ──────────────────────────────────
  const buckets = { '0–5%': 0, '5–10%': 0, '10–20%': 0, '>20%': 0 };
  rows.forEach(r => {
    const p = r.percentageError;
    if (p < 5) buckets['0–5%']++;
    else if (p < 10) buckets['5–10%']++;
    else if (p < 20) buckets['10–20%']++;
    else buckets['>20%']++;
  });

  return (
    <div className="app">
      {/* ── HEADER ─────────────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-inner">
          <div className="header-brand">
            <span className="header-icon">⚡</span>
            <div>
              <h1>UK Wind Power Intelligence</h1>
              <p>Day-Ahead Market Planning · Elexon BMRS · January 2026</p>
            </div>
          </div>
          <button className="btn-generate" onClick={fetchAll} disabled={loading}>
            {loading ? '⏳ Loading…' : '▶ Generate Analysis'}
          </button>
        </div>
      </header>

      <main className="app-main">
        {/* ── ERROR ─────────────────────────────────────────────────────────── */}
        {error && (
          <div className="alert alert-error">
            <strong>⚠ Error:</strong> {error}
          </div>
        )}

        {/* ── LOADING ───────────────────────────────────────────────────────── */}
        {loading && <LoadingBar />}

        {/* ── WELCOME ───────────────────────────────────────────────────────── */}
        {!loading && !accuracy && !error && (
          <div className="welcome">
            <div className="welcome-icon">🌬️</div>
            <h2>Wind Power Forecast & Accuracy Dashboard</h2>
            <p>
              This tool helps the day-ahead procurement team understand renewable generation
              forecasts and quantify their accuracy — enabling smarter electricity purchasing decisions.
            </p>
            <ul className="welcome-list">
              <li>📊 Daily actual vs forecast comparison charts</li>
              <li>📉 Error distribution analysis (MAE, RMSE, MAPE)</li>
              <li>🗓️ Full January 2026 half-hourly data (1488 slots)</li>
              <li>🔄 Live data from Elexon BMRS API with intelligent fallback</li>
            </ul>
            <button className="btn-generate btn-welcome" onClick={fetchAll}>
              ▶ Generate Analysis
            </button>
          </div>
        )}

        {/* ── RESULTS ───────────────────────────────────────────────────────── */}
        {accuracy && (
          <>
            {/* Data source badge */}
            <div className="data-badge">
              <span className="badge-dot" /> {dataSource}
            </div>

            {/* ── KPI CARDS ──────────────────────────────────────────────────── */}
            <section className="kpi-grid">
              <StatCard label="Half-Hour Slots" value={summary.totalSamples.toLocaleString()} color="#6366f1" sub="Jan 2026 (31 days)" />
              <StatCard label="MAE" value={summary.mae.toLocaleString()} unit=" MW" color="#10b981" sub="Mean Absolute Error" />
              <StatCard label="RMSE" value={summary.rmse.toLocaleString()} unit=" MW" color="#f59e0b" sub="Root Mean Sq Error" />
              <StatCard label="MAPE" value={summary.mape} unit="%" color="#8b5cf6" sub="Mean Abs % Error" />
              <StatCard label="Mean Bias" value={summary.meanBias > 0 ? '+' + summary.meanBias : summary.meanBias} unit=" MW" color={summary.meanBias > 0 ? '#ef4444' : '#10b981'} sub={summary.meanBias > 0 ? 'Over-forecast' : 'Under-forecast'} />
              <StatCard label="Max % Error" value={summary.maxPercentageError} unit="%" color="#ef4444" sub="Worst-case slot" />
            </section>

            {/* ── ERROR BREAKDOWN ─────────────────────────────────────────────── */}
            <section className="error-breakdown">
              <h3>Error Distribution</h3>
              <div className="bucket-grid">
                {Object.entries(buckets).map(([label, count]) => {
                  const pct = rows.length > 0 ? ((count / rows.length) * 100).toFixed(1) : 0;
                  const colors = { '0–5%': '#10b981', '5–10%': '#f59e0b', '10–20%': '#f97316', '>20%': '#ef4444' };
                  return (
                    <div className="bucket-card" key={label} style={{ borderLeft: `4px solid ${colors[label]}` }}>
                      <div className="bucket-label">{label} error</div>
                      <div className="bucket-count" style={{ color: colors[label] }}>{pct}%</div>
                      <div className="bucket-sub">{count} slots</div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* ── TABS ───────────────────────────────────────────────────────── */}
            <div className="tabs">
              {['overview', 'error', 'table'].map(tab => (
                <button
                  key={tab}
                  className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
                  onClick={() => setState(s => ({ ...s, activeTab: tab }))}
                >
                  {tab === 'overview' ? '📈 Forecast vs Actual' : tab === 'error' ? '📉 Daily Error' : '📋 Data Table'}
                </button>
              ))}
            </div>

            {/* ── OVERVIEW CHART ──────────────────────────────────────────────── */}
            {activeTab === 'overview' && (
              <div className="chart-card">
                <div className="chart-wrap">
                  <Line data={lineData} options={chartOpts('Daily Average Wind Generation – January 2026', 'MW')} />
                </div>
                <p className="chart-note">
                  Each point represents the average generation across all 48 half-hour slots within that day.
                  A close alignment of the two lines indicates high forecast accuracy.
                </p>
              </div>
            )}

            {/* ── ERROR CHART ─────────────────────────────────────────────────── */}
            {activeTab === 'error' && (
              <div className="chart-card">
                <div className="chart-wrap">
                  <Bar data={errData} options={chartOpts('Daily Average Absolute Forecast Error – January 2026', 'MW')} />
                </div>
                <p className="chart-note">
                  Bars coloured <span style={{ color: '#10b981' }}>green</span> (&lt;150 MW), <span style={{ color: '#f59e0b' }}>amber</span> (150–300 MW), or <span style={{ color: '#ef4444' }}>red</span> (&gt;300 MW) show days when procurement decisions carry higher uncertainty.
                </p>
              </div>
            )}

            {/* ── DATA TABLE ──────────────────────────────────────────────────── */}
            {activeTab === 'table' && (
              <div className="table-card">
                <div className="table-info">Showing {rows.length} half-hour slots · scroll to explore</div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Start Time (UTC)</th>
                        <th>Publish Time</th>
                        <th>Actual (MW)</th>
                        <th>Forecast (MW)</th>
                        <th>Error (MW)</th>
                        <th>% Error</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, i) => (
                        <tr key={i} className={r.percentageError > 20 ? 'row-high-err' : r.percentageError > 10 ? 'row-med-err' : ''}>
                          <td>{r.startTime}</td>
                          <td>{r.publishTime}</td>
                          <td>{r.actual.toLocaleString()}</td>
                          <td>{r.forecast.toLocaleString()}</td>
                          <td className={r.error > 0 ? 'pos-err' : 'neg-err'}>
                            {r.error > 0 ? '+' : ''}{r.error}
                          </td>
                          <td>
                            <span className={`pct-badge ${r.percentageError > 20 ? 'badge-red' : r.percentageError > 10 ? 'badge-amber' : 'badge-green'}`}>
                              {r.percentageError}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Data source: <a href="https://bmrs.elexon.co.uk" target="_blank" rel="noreferrer">Elexon BMRS Insights Solution API</a>
          &nbsp;· FUELHH (Actual) &amp; WINDFOR (Forecast) · January 2026
        </p>
      </footer>
    </div>
  );
}
