const CustomTooltip = ({ active, payload, label, formatter }) => {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-xl border border-white/[0.06] bg-[#1a2236] px-4 py-3 shadow-xl shadow-black/40">
      {label !== undefined && (
        <p className="mb-1.5 text-xs font-semibold text-white">{label}</p>
      )}
      <div className="space-y-1">
        {payload.map((entry, index) => (
          <div key={`${entry.name}-${index}`} className="flex items-center gap-2 text-xs">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: entry.color || '#4f8ff7' }}
            />
            <span className="text-slate-400">{entry.name}:</span>
            <span className="font-medium text-white">
              {formatter ? formatter(entry.value, entry.name) : entry.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CustomTooltip;
