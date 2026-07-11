import { NavLink, useNavigate } from 'react-router-dom';

const navItems = [
  { to: '/qa', label: 'Q&A' },
  { to: '/forecast', label: 'Forecasting' },
  { to: '/evaluate', label: 'Evaluation' }
];

const Navbar = () => {
  const navigate = useNavigate();
  const username = localStorage.getItem('finsight_user') || 'Analyst';

  const handleLogout = () => {
    localStorage.removeItem('finsight_token');
    localStorage.removeItem('finsight_user');
    navigate('/login');
  };

  return (
    <nav className="border-b border-slate-800 bg-slate-900/90 px-6 py-4 shadow-sm">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl font-semibold text-blue-500">FinSight</span>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-full px-4 py-2 text-sm font-medium transition ${isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-300">{username}</span>
          <button
            onClick={handleLogout}
            className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-200 transition hover:border-blue-500 hover:text-white"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
