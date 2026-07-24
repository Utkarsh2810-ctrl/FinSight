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
import { SkeletonCard, SkeletonChart } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import CustomTooltip from '../components/CustomTooltip';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
        `${API_URL}/api/forecast`,
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

  const qoqGrowth = Number(forecastData?.prediction?.qoq_growth_pct || 0);

  return (
    <div className="min-h-[calc(100vh-64px)]">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="card p-5 animate-fade-in">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="section-label">Forecasting</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Revenue & Loss Modeling</h2>
              <p className="mt-1.5 text-sm text-slate-400">
                Train an LSTM model on quarterly revenue and view projections.
              </p>
            </div>
            <form onSubmit={handleSubmit} className="flex w-full max-w-md items-center gap-3 lg:w-auto">
              <div className="relative flex-1">
                <svg className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                <input
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  placeholder="Ticker (e.g. AAPL)"
                  className="input pl-10"
                />
              </div>
              <button type="submit" disabled={loading} className="btn-primary shrink-0">
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8.001 8.001 0 0112 4.001V0C5.373 0 0 5.373 0 12h4c0-2.29.92-4.37 2.414-5.9z" />
                    </svg>
                    Training…
                  </span>
                ) : 'Run Forecast'}
              </button>
            </form>
          </div>
          {error && (
            <div className="mt-4 animate-slide-up rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <>
            <div className="grid gap-5 xl:grid-cols-3">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
            <div className="grid gap-5 xl:grid-cols-2">
              <SkeletonChart />
              <SkeletonChart />
            </div>
          </>
        ) : forecastData ? (
          <>
            {/* Summary cards */}
            <div className="grid gap-4 sm:grid-cols-3 animate-fade-in">
              <div className="card p-5">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Predicted Revenue</p>
                <p className="mt-3 text-2xl font-semibold text-white">
                  {formatRevenue(forecastData.prediction?.predicted_revenue)}
                </p>
                <div className="mt-2 flex items-center gap-1.5">
                  <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                    qoqGrowth >= 0
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : 'bg-red-500/10 text-red-400'
                  }`}>
                    {qoqGrowth >= 0 ? '↑' : '↓'} {Math.abs(qoqGrowth).toFixed(2)}%
                  </span>
                  <span className="text-xs text-slate-500">QoQ</span>
                </div>
              </div>

              <div className="card p-5">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Last Actual Revenue</p>
                <p className="mt-3 text-2xl font-semibold text-white">
                  {formatRevenue(forecastData.prediction?.last_actual_revenue)}
                </p>
                <p className="mt-2 text-xs text-slate-500">Most recent quarter</p>
              </div>

              <div className="card p-5">
                <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Ticker & Features</p>
                <p className="mt-3 text-2xl font-semibold text-accent-400">{forecastData.ticker}</p>
                <p className="mt-2 truncate text-xs text-slate-500">
                  {forecastData.features_used?.join(', ') || 'n/a'}
                </p>
              </div>
            </div>

            {/* Charts */}
            <div className="grid gap-5 xl:grid-cols-2 animate-fade-in">
              <div className="card p-5">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">Revenue Forecast</h3>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-accent-500" />
                      <span className="text-[11px] text-slate-500">Historical</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-orange-500" />
                      <span className="text-[11px] text-slate-500">Predicted</span>
                    </div>
                  </div>
                </div>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={revenueChartData}>
                      <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        tickFormatter={(value) => `$${(value / 1e9).toFixed(1)}B`}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip content={<CustomTooltip formatter={(v) => formatRevenue(v)} />} />
                      <Bar dataKey="revenue" radius={[6, 6, 0, 0]}>
                        {revenueChartData.map((entry) => (
                          <Cell
                            key={`${entry.name}-${entry.type}`}
                            fill={entry.type === 'prediction' ? '#f97316' : '#4f8ff7'}
                            fillOpacity={entry.type === 'prediction' ? 0.85 : 0.7}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="card p-5">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">Training Loss</h3>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-accent-500" />
                      <span className="text-[11px] text-slate-500">Train</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-orange-500" />
                      <span className="text-[11px] text-slate-500">Validation</span>
                    </div>
                  </div>
                </div>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={lossChartData}>
                      <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="epoch" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line type="monotone" dataKey="trainLoss" stroke="#4f8ff7" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="valLoss" stroke="#f97316" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </>
        ) : (
          <EmptyState
            icon={
              <svg className="h-7 w-7 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            }
            title="No forecast yet"
            description="Enter a ticker symbol like AAPL, MSFT, or GOOGL and run the forecast to see revenue projections and model training metrics."
          />
        )}
      </div>
    </div>
  );
};

export default ForecastPage;
