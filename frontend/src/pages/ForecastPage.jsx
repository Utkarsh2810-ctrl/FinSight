import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  BarChart,
  Bar,
  CartesianGrid,
  Cell,
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';

const formatRevenue = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toFixed(2)}`;
};

const ForecastPage = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('finsight_token');
  const userName = localStorage.getItem('finsight_user') || 'Analyst';

  const [ticker, setTicker] = useState('AAPL');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [forecastData, setForecastData] = useState(null);

  useEffect(() => {
    if (!token) {
      navigate('/login');
    }
  }, [navigate, token]);

  const revenueChartData = useMemo(() => {
    if (!forecastData?.history) return [];
    const history = forecastData.history.map((item, index) => ({
      name: item.date || `Q${index + 1}`,
      revenue: Number(item.revenue) || 0,
      type: 'history'
    }));
    if (forecastData.prediction?.predicted_revenue !== undefined) {
      history.push({
        name: 'Predicted',
        revenue: Number(forecastData.prediction.predicted_revenue) || 0,
        type: 'prediction'
      });
    }
    return history;
  }, [forecastData]);

  const lossChartData = useMemo(() => {
    if (!forecastData?.train_losses || !forecastData?.val_losses) return [];
    return forecastData.train_losses.map((trainLoss, index) => ({
      epoch: index + 1,
      trainLoss: Number(trainLoss) || 0,
      valLoss: Number(forecastData.val_losses[index]) || 0
    }));
  }, [forecastData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ticker.trim()) {
      setError('Please enter a ticker symbol.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        'http://localhost:8000/api/forecast',
        { ticker: ticker.trim() },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      setForecastData(response.data);
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Your session has expired. Please log in again.');
      } else if (err.response?.status === 400 || err.response?.status === 404) {
        setError('Unable to forecast that ticker. Please try another symbol.');
      } else {
        setError('Forecast generation failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('finsight_token');
    localStorage.removeItem('finsight_user');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-2xl shadow-blue-950/20">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-blue-400">Forecasting</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Revenue and loss modeling</h2>
              <p className="mt-2 text-sm text-slate-400">Welcome back, {userName}. Run a forecast to inspect historical revenue and model performance.</p>
            </div>
            <form onSubmit={handleSubmit} className="flex w-full max-w-xl flex-col gap-3 sm:flex-row">
              <input
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                placeholder="Ticker (e.g. AAPL)"
                className="flex-1 rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-blue-500"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? 'Training LSTM model...' : 'Run Forecast'}
              </button>
            </form>
          </div>
          {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        </div>

        {loading ? (
          <div className="flex items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/80 px-6 py-16 shadow-2xl shadow-blue-950/20">
            <div className="flex items-center gap-3 text-slate-300">
              <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8.001 8.001 0 0112 4.001V0C5.373 0 0 5.373 0 12h4c0-2.29.92-4.37 2.414-5.9z" />
              </svg>
              <span>Training LSTM model...</span>
            </div>
          </div>
        ) : forecastData ? (
          <>
            <div className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 shadow-2xl shadow-blue-950/20">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">Revenue Forecast</h3>
                  <span className="text-sm text-slate-400">{forecastData.ticker}</span>
                </div>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={revenueChartData}>
                      <CartesianGrid stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} tickFormatter={(value) => `$${(value / 1e9).toFixed(1)}B`} />
                      <Tooltip formatter={(value) => formatRevenue(value)} />
                      <Bar dataKey="revenue" radius={[6, 6, 0, 0]}>
                        {revenueChartData.map((entry) => (
                          <Cell key={`${entry.name}-${entry.type}`} fill={entry.type === 'prediction' ? '#f97316' : '#3b82f6'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 shadow-2xl shadow-blue-950/20">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">Training Loss</h3>
                  <span className="text-sm text-slate-400">Epochs</span>
                </div>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={lossChartData}>
                      <CartesianGrid stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="epoch" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="trainLoss" stroke="#3b82f6" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="valLoss" stroke="#f97316" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-2xl shadow-blue-950/20">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-blue-400">Prediction Summary</p>
                  <h3 className="mt-2 text-xl font-semibold text-white">{forecastData.ticker}</h3>
                </div>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                    <p className="text-sm text-slate-400">Predicted Revenue</p>
                    <p className="mt-2 text-lg font-semibold text-white">{formatRevenue(forecastData.prediction?.predicted_revenue)}</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                    <p className="text-sm text-slate-400">Last Actual Revenue</p>
                    <p className="mt-2 text-lg font-semibold text-white">{formatRevenue(forecastData.prediction?.last_actual_revenue)}</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                    <p className="text-sm text-slate-400">QoQ Growth %</p>
                    <p className={`mt-2 text-lg font-semibold ${Number(forecastData.prediction?.qoq_growth_pct) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {Number(forecastData.prediction?.qoq_growth_pct) >= 0 ? '▲' : '▼'} {Math.abs(Number(forecastData.prediction?.qoq_growth_pct || 0)).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-4 text-sm text-slate-400">
                Features used: {forecastData.features_used?.join(', ') || 'n/a'}
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/80 p-10 text-center text-slate-400">
            Enter a ticker and run a forecast to view revenue and loss metrics.
          </div>
        )}
      </div>
    </div>
  );
};

export default ForecastPage;
