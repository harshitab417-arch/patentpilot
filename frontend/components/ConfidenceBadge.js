'use client';

export default function ConfidenceBadge({ level }) {
  const styles = {
    High: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    Medium: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
    Low: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
  }[level] || 'bg-slate-500/10 text-sage-gray-light dark:text-sage-gray-dark border-slate-500/20';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold border ${styles}`}>
      {level} Confidence
    </span>
  );
}
