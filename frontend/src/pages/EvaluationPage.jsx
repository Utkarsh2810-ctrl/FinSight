import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip
} from 'recharts';
import { SkeletonCard, SkeletonChart } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const metricConfig = {
  faithfulness: { label: 'Faithfulness', icon: '🎯' },
  context_precision: { label: 'Context Precision', icon: '🔬' },
  context_recall: { label: 'Context Recall', icon: '📋' }
};

const getScoreColor = (value) => {
  if (value > 0.7) return { text: 'text-emerald-400', bg: 'bg-emerald-500', ring: 'stroke-emerald-500', badge: 'Strong' };
  if (value >= 0.4) return { text: 'text-amber-400', bg: 'bg-amber-500', ring: 'stroke-amber-500', badge: 'Moderate' };
  return { text: 'text-red-400', bg: 'bg-red-500', ring: 'stroke-red-500', badge: 'Needs work' };
};

const CircularProgress = ({ value, size = 72, strokeWidth = 5 }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalized = Math.max(0, Math.min(1, Number(value) || 0));
  const offset = circumference - normalized * circumference;
  const color = getScoreColor(normalized);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.04)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          className={color.ring}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={`text-base font-semibold ${color.text}`}>
          {(normalized * 100).toFixed(0)}
        </span>
      </div>
    </div>
  );
};

const EvaluationPage = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('finsight_token');
  const userName = localStorage.getItem('finsight_user') || 'Analyst';

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [expandedRow, setExpandedRow] = useState(null);

  useEffect(() => {
    if (!token) {
      navigate('/login');
    }
  }, [navigate, token]);

  const chartData = useMemo(() => {
    if (!result) return [];
    return [
      { metric: 'Faithfulness', value: Number(result.faithfulness) || 0, fullMark: 1 },
      { metric: 'Context Precision', value: Number(result.context_precision) || 0, fullMark: 1 },
      { metric: 'Context Recall', value: Number(result.context_recall) || 0, fullMark: 1 }
    ];
  }, [result]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please upload a benchmark JSON file.');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/api/evaluate`, formData, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setResult(response.data);
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Your session expired. Please log in again.');
      } else {
        setError('Evaluation failed. Please ensure the benchmark file is valid and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)]">
      <div className="mx-auto flex max-w-[1440px] flex-col gap-5 px-4 py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="card p-5 animate-fade-in">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="section-label">Evaluation</p>
              <h2 className="mt-2 text-xl font-semibold text-white">RAGAS Benchmark Review</h2>
              <p className="mt-1.5 text-sm text-slate-400">
                Upload a benchmark JSON to evaluate answer quality across multiple dimensions.
              </p>
            </div>
            <form onSubmit={handleSubmit} className="flex w-full max-w-xl items-center gap-3 lg:w-auto">
              <div className="relative flex-1">
                <input
                  type="file"
                  accept="application/json"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="input text-slate-400 file:mr-3 file:rounded-lg file:border-0 file:bg-accent-600/15 file:px-3 file:py-1 file:text-xs file:font-medium file:text-accent-400 file:transition-colors file:cursor-pointer hover:file:bg-accent-600/25"
                />
                {file && (
                  <p className="mt-1.5 text-xs text-emerald-400">{file.name}</p>
                )}
              </div>
              <button type="submit" disabled={loading} className="btn-primary shrink-0">
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8.001 8.001 0 0112 4.001V0C5.373 0 0 5.373 0 12h4c0-2.29.92-4.37 2.414-5.9z" />
                    </svg>
                    Evaluating…
                  </span>
                ) : 'Run Evaluation'}
              </button>
            </form>
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Expected: JSON array of objects with <code className="rounded bg-surface-800 px-1.5 py-0.5 text-accent-400">question</code>,{' '}
            <code className="rounded bg-surface-800 px-1.5 py-0.5 text-accent-400">ground_truth</code>, and{' '}
            <code className="rounded bg-surface-800 px-1.5 py-0.5 text-accent-400">document_id</code> fields.
          </p>
          {error && (
            <div className="mt-4 animate-slide-up rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <>
            <div className="grid gap-4 sm:grid-cols-3">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
            <SkeletonChart />
          </>
        ) : result ? (
          <>
            {/* Metric cards with circular gauges */}
            <div className="grid gap-4 sm:grid-cols-3 animate-fade-in">
              {['faithfulness', 'context_precision', 'context_recall'].map((key) => {
                const value = Number(result[key] || 0);
                const color = getScoreColor(value);
                return (
                  <div key={key} className="card p-5">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                          {metricConfig[key].label}
                        </p>
                        <p className={`mt-3 text-2xl font-semibold ${color.text}`}>
                          {value.toFixed(2)}
                        </p>
                        <span className={`mt-2 inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                          value > 0.7
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : value >= 0.4
                              ? 'bg-amber-500/10 text-amber-400'
                              : 'bg-red-500/10 text-red-400'
                        }`}>
                          {color.badge}
                        </span>
                      </div>
                      <CircularProgress value={value} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Radar chart */}
            <div className="card p-5 animate-fade-in">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white">Metric Overview</h3>
                <span className="text-xs text-slate-500">Score distribution (0–1 scale)</span>
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={chartData}>
                    <PolarGrid stroke="rgba(255,255,255,0.06)" />
                    <PolarAngleAxis
                      dataKey="metric"
                      tick={{ fill: '#94a3b8', fontSize: 12 }}
                    />
                    <PolarRadiusAxis
                      angle={30}
                      domain={[0, 1]}
                      tick={{ fill: '#475569', fontSize: 10 }}
                    />
                    <Radar
                      dataKey="value"
                      stroke="#4f8ff7"
                      fill="#4f8ff7"
                      fillOpacity={0.15}
                      strokeWidth={2}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Per-question results table */}
            <div className="card overflow-hidden animate-fade-in">
              <div className="border-b border-white/[0.06] px-5 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white">Per-question Results</h3>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {result.n_questions || 0} questions evaluated
                    </p>
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/[0.04]">
                      <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Question</th>
                      <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Answer</th>
                      <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500">Ground Truth</th>
                      <th className="px-5 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500">Faith.</th>
                      <th className="px-5 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500">Prec.</th>
                      <th className="px-5 py-3 text-center text-xs font-medium uppercase tracking-wider text-slate-500">Recall</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.03]">
                    {result.per_question?.map((row, index) => {
                      const scores = [
                        Number(row.faithfulness) || 0,
                        Number(row.context_precision) || 0,
                        Number(row.context_recall) || 0
                      ];
                      const lowest = Math.min(...scores);
                      const isExpanded = expandedRow === index;

                      return (
                        <tr
                          key={`${row.question}-${index}`}
                          onClick={() => setExpandedRow(isExpanded ? null : index)}
                          className={`cursor-pointer transition-colors ${
                            lowest > 0.7
                              ? 'hover:bg-emerald-500/[0.03]'
                              : lowest >= 0.4
                                ? 'hover:bg-amber-500/[0.03]'
                                : 'hover:bg-red-500/[0.03]'
                          }`}
                        >
                          <td className="max-w-[200px] px-5 py-3.5 align-top">
                            <p className={`text-sm text-slate-300 ${isExpanded ? '' : 'line-clamp-2'}`}>{row.question}</p>
                          </td>
                          <td className="max-w-[200px] px-5 py-3.5 align-top">
                            <p className={`text-sm text-slate-400 ${isExpanded ? '' : 'line-clamp-2'}`}>{row.answer}</p>
                          </td>
                          <td className="max-w-[200px] px-5 py-3.5 align-top">
                            <p className={`text-sm text-slate-400 ${isExpanded ? '' : 'line-clamp-2'}`}>{row.ground_truth}</p>
                          </td>
                          {scores.map((score, i) => {
                            const c = getScoreColor(score);
                            return (
                              <td key={i} className="px-5 py-3.5 text-center align-top">
                                <span className={`inline-flex h-7 min-w-[42px] items-center justify-center rounded-md text-xs font-semibold ${
                                  score > 0.7
                                    ? 'bg-emerald-500/10 text-emerald-400'
                                    : score >= 0.4
                                      ? 'bg-amber-500/10 text-amber-400'
                                      : 'bg-red-500/10 text-red-400'
                                }`}>
                                  {score.toFixed(2)}
                                </span>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <EmptyState
            icon={
              <svg className="h-7 w-7 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            }
            title="No evaluation yet"
            description="Upload a benchmark JSON file with questions and ground truth answers to run a RAGAS evaluation and see per-question quality metrics."
          />
        )}
      </div>
    </div>
  );
};

export default EvaluationPage;
