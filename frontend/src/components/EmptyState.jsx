const EmptyState = ({ icon, title, description, action }) => {
  return (
    <div className="card flex flex-col items-center justify-center px-6 py-16 text-center animate-fade-in">
      {icon && (
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-800/80">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      {description && (
        <p className="mt-2 max-w-md text-sm leading-relaxed text-slate-400">
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
};

export default EmptyState;
