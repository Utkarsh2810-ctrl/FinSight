const Skeleton = ({ className = '', variant = 'rect' }) => {
  const baseClasses = 'skeleton';

  if (variant === 'circle') {
    return <div className={`${baseClasses} rounded-full ${className}`} />;
  }

  if (variant === 'text') {
    return <div className={`${baseClasses} h-4 ${className}`} />;
  }

  return <div className={`${baseClasses} ${className}`} />;
};

const SkeletonCard = ({ className = '' }) => (
  <div className={`card p-5 ${className}`}>
    <Skeleton variant="text" className="mb-3 w-24" />
    <Skeleton className="mb-4 h-8 w-32" />
    <Skeleton className="h-2 w-full rounded-full" />
  </div>
);

const SkeletonChart = ({ className = '' }) => (
  <div className={`card p-5 ${className}`}>
    <div className="mb-4 flex items-center justify-between">
      <Skeleton variant="text" className="w-32" />
      <Skeleton variant="text" className="w-16" />
    </div>
    <Skeleton className="h-72 w-full rounded-xl" />
  </div>
);

export { Skeleton, SkeletonCard, SkeletonChart };
export default Skeleton;
