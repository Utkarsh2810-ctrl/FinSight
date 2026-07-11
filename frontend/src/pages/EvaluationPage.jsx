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

const metricConfig = {
  faithfulness: { label: 'Faithfulness', color: 'text-emerald-400' },
  answer_relevancy: { label: 'Answer Relevancy', color: 'text-emerald-400' },
  context_precision: { label: 'Context Precision', color: 'text-emerald-400' },
  context_recall: { label: 'Context Recall', color: 'text-emerald-400' }
};

const getMetricColor = (value) => {
  if (value > 0.7) return 'text-emerald-400';
  if (value >= 0.4) return 'text-amber-400';
  return 'text-red-400';
};

const getMetricBar = (value) => {
  const normalized = Math.max(0, Math.min(1, Number(value) || 0));
  return `${Math.round(normalized * 100)}%`;
};

const EvaluationPage = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('finsight_token');
  const userName = localStorage.getItem('finsight_user') || 'Analyst';

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!token) {
      navigate('/login');
    }
  }, [navigate, token]);

  const chartData = useMemo(() => {
    if (!result) return [];
    return [
      {
        metric: 'Faithfulness',
        value: Number(result.faithfulness) || 0,
        fullMark: 1
      },
      {
        metric: 'Answer Relevancy',
        value: Number(result.answer_relevancy) || 0,
        fullMark: 1
      },
      {
        metric: 'Context Precision',
        value: Number(result.context_precision) || 0,
        fullMark: 1
      },
      {
        metric: 'Context Recall',
        value: Number(result.context_recall) || 0,
        fullMark: 1
      }
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
      const response = await axios.post('http://localhost:8000/api/evaluate', formData, {
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

  const logout = () => {
    localStorage.removeItem('finsight_token');
    localStorage.removeItem('finsight_user');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-2xl shadow-blue-950/20">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-blue-400">Evaluation</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">RAGAS benchmark review</h2>
              <p className="mt-2 text-sm text-slate-400">Welcome back, {userName}. Upload a benchmark JSON file to evaluate answer quality.</p>
            </div>
            <form onSubmit={handleSubmit} className="flex w-full max-w-2xl flex-col gap-3 sm:flex-row">
              <input
                type="file"
                accept="application/json"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="flex-1 rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-3 text-sm text-slate-200 file:mr-3 file:rounded-full file:border-0 file:bg-blue-600 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? 'Running RAGAS evaluation...' : 'Run Evaluation'}
              </button>
            </form>
          </div>
          <p className="mt-4 text-sm text-slate-500">Expected format: a JSON array of objects with question, ground_truth, and document_id fields.</p>
          {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        </div>

        {loading ? (
          <div className="flex items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/80 px-6 py-16 shadow-2xl shadow-blue-950/20">
            <div className="flex items-center gap-3 text-slate-300">
              <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8.001 8.001 0 0112 4.001V0C5.373 0 0 5.373 0 12h4c0-2.29.92-4.37 2.414-5.9z" />
              </svg>
              <span>Running RAGAS evaluation...</span>
            </div>
          </div>
        ) : result ? (
          <>
            <div className="grid gap-4 xl:grid-cols-4">
              {['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall'].map((key) => {
                const value = Number(result[key] || 0);
                const colorClass = getMetricColor(value);
                return (
                  <div key={key} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 shadow-2xl shadow-blue-950/20">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-slate-300">{metricConfig[key].label}</p>
                      <span className={`text-xs font-semibold ${colorClass}`}>{value > 0.7 ? 'Strong' : value >= 0.4 ? 'Moderate' : 'Needs work'}</span>
                    </div>
                    <p className={`mt-4 text-3xl font-semibold ${colorClass}`}>{value.toFixed(2)}</p>
                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
                      <div className={`h-full rounded-full ${value > 0.7 ? 'bg-emerald-500' : value >= 0.4 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: getMetricBar(value) }} />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 shadow-2xl shadow-blue-950/20">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Metric Overview</h3>
                <span className="text-sm text-slate-400">Score distribution</span>
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={chartData}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: '#cbd5e1', fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                    <Radar dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 shadow-2xl shadow-blue-950/20">
              <div className="border-b border-slate-800 p-4">
                <h3 className="text-lg font-semibold text-white">Per-question Results</h3>
                <p className="text-sm text-slate-400">{result.n_questions || 0} questions evaluated</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-800 text-sm">
                  <thead className="bg-slate-950/70 text-left text-slate-300">
                    <tr>
                      <th className="px-4 py-3 font-medium">Question</th>
                      <th className="px-4 py-3 font-medium">Answer</th>
                      <th className="px-4 py-3 font-medium">Ground Truth</th>
                      <th className="px-4 py-3 font-medium">Faithfulness</th>
                      <th className="px-4 py-3 font-medium">Answer Relevancy</th>
                      <th className="px-4 py-3 font-medium">Context Precision</th>
                      <th className="px-4 py-3 font-medium">Context Recall</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-900/70 text-slate-300">
                    {result.per_question?.map((row, index) => {
                      const scores = [
                        Number(row.faithfulness) || 0,
                        Number(row.answer_relevancy) || 0,
                        Number(row.context_precision) || 0,
                        Number(row.context_recall) || 0
                      ];
                      const lowest = Math.min(...scores);
                      const rowColor = lowest > 0.7 ? 'bg-emerald-500/10' : lowest >= 0.4 ? 'bg-amber-500/10' : 'bg-red-500/10';
                      return (
                        <tr key={`${row.question}-${index}`} className={rowColor}>
                          <td className="max-w-[220px] px-4 py-3 align-top">
                            <p className="line-clamp-3 text-sm">{row.question}</p>
                          </td>
                          <td className="max-w-[220px] px-4 py-3 align-top">
                            <p className="line-clamp-3 text-sm">{row.answer}</p>
                          </td>
                          <td className="max-w-[220px] px-4 py-3 align-top">
                            <p className="line-clamp-3 text-sm">{row.ground_truth}</p>
                          </td>
                          <td className={`px-4 py-3 align-top ${getMetricColor(Number(row.faithfulness) || 0)}`}>{Number(row.faithfulness || 0).toFixed(2)}</td>
                          <td className={`px-4 py-3 align-top ${getMetricColor(Number(row.answer_relevancy) || 0)}`}>{Number(row.answer_relevancy || 0).toFixed(2)}</td>
                          <td className={`px-4 py-3 align-top ${getMetricColor(Number(row.context_precision) || 0)}`}>{Number(row.context_precision || 0).toFixed(2)}</td>
                          <td className={`px-4 py-3 align-top ${getMetricColor(Number(row.context_recall) || 0)}`}>{Number(row.context_recall || 0).toFixed(2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/80 p-10 text-center text-slate-400">
            Upload a benchmark JSON file to start a RAGAS evaluation.
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationPage;
