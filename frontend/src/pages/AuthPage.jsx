import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'http://localhost:8080';

const AuthPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = activeTab === 'register' ? '/api/auth/register' : '/api/auth/login';
      const payload = activeTab === 'register'
        ? { name: form.name, email: form.email, password: form.password }
        : { email: form.email, password: form.password };

      const response = await axios.post(`${AUTH_URL}${endpoint}`, payload, {
        headers: { 'Content-Type': 'application/json' }
      });

      localStorage.setItem('finsight_token', response.data.token);
      localStorage.setItem('finsight_user', response.data.name || response.data.email);
      navigate('/qa');
    } catch (err) {
      if (err.code === 'ERR_NETWORK' || !err.response) {
        setError('Unable to reach the FinSight backend. Make sure the Spring server is running on port 8080.');
      } else if (err.response?.status === 401) {
        setError('Invalid email or password.');
      } else if (err.response?.status === 400) {
        setError('Please check your details and try again.');
      } else {
        setError(err.response?.data?.message || 'Authentication failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left branding panel — hidden on mobile */}
      <div className="relative hidden flex-1 items-center justify-center overflow-hidden bg-surface-950 lg:flex">
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
            backgroundSize: '48px 48px'
          }}
        />
        {/* Radial glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-accent-600/10 via-transparent to-transparent" />

        <div className="relative z-10 max-w-md px-12">
          <div className="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-accent-500 to-accent-700 shadow-glow">
            <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white">
            Financial Intelligence,<br />
            <span className="bg-gradient-to-r from-accent-400 to-accent-200 bg-clip-text text-transparent">Reimagined.</span>
          </h1>
          <p className="mt-5 text-base leading-relaxed text-slate-400">
            Upload financial documents. Ask questions with grounded answers. Forecast revenue with ML models. Evaluate pipeline quality — all in one workspace.
          </p>

          <div className="mt-10 grid grid-cols-3 gap-4">
            {[
              { label: 'Document Q&A', value: 'RAG' },
              { label: 'LSTM Forecast', value: 'ML' },
              { label: 'RAGAS Eval', value: 'QA' }
            ].map((item) => (
              <div key={item.label} className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-3 text-center">
                <p className="text-lg font-semibold text-accent-400">{item.value}</p>
                <p className="mt-1 text-xs text-slate-500">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex w-full flex-col items-center justify-center px-6 py-10 lg:w-[480px] lg:min-w-[480px]">
        <div className="w-full max-w-sm">
          {/* Mobile-only branding */}
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-accent-500 to-accent-700">
              <svg className="h-4.5 w-4.5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
              </svg>
            </div>
            <span className="text-xl font-semibold text-white">FinSight</span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-semibold tracking-tight text-white">
              {activeTab === 'register' ? 'Create your account' : 'Welcome back'}
            </h2>
            <p className="mt-2 text-sm text-slate-400">
              {activeTab === 'register'
                ? 'Start analyzing financial documents in seconds.'
                : 'Sign in to continue to your workspace.'}
            </p>
          </div>

          {/* Tab switcher */}
          <div className="mb-6 flex rounded-xl border border-white/[0.06] bg-surface-900/70 p-1">
            <button
              type="button"
              onClick={() => setActiveTab('login')}
              className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-200 ${
                activeTab === 'login'
                  ? 'bg-white/[0.08] text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('register')}
              className={`flex-1 rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-200 ${
                activeTab === 'register'
                  ? 'bg-white/[0.08] text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {activeTab === 'register' && (
              <div className="animate-slide-up">
                <label className="label" htmlFor="auth-name">Full name</label>
                <input
                  id="auth-name"
                  name="name"
                  type="text"
                  required
                  value={form.name}
                  onChange={handleChange}
                  className="input"
                  placeholder="Alex Morgan"
                />
              </div>
            )}

            <div>
              <label className="label" htmlFor="auth-email">Email address</label>
              <input
                id="auth-email"
                name="email"
                type="email"
                required
                value={form.email}
                onChange={handleChange}
                className="input"
                placeholder="you@company.com"
              />
            </div>

            <div>
              <label className="label" htmlFor="auth-password">Password</label>
              <input
                id="auth-password"
                name="password"
                type="password"
                required
                value={form.password}
                onChange={handleChange}
                className="input"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="animate-slide-up rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3"
            >
              {loading ? (
                <span className="flex items-center gap-2.5">
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8.001 8.001 0 0112 4.001V0C5.373 0 0 5.373 0 12h4c0-2.29.92-4.37 2.414-5.9z" />
                  </svg>
                  Processing…
                </span>
              ) : activeTab === 'register' ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-slate-500">
            By continuing, you agree to FinSight's terms of service.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
