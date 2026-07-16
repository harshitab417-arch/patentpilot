'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Search as SearchIcon, Dna, Clock, Target, Calendar, ChevronRight } from 'lucide-react';
import RiskBadge from './RiskBadge';

function timeAgo(dateString) {
  if (!dateString) return 'Unknown';
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 172800) return 'Yesterday';
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function HistoryList({ analyses = [] }) {
  const router = useRouter();
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search.trim()) return analyses;
    const q = search.toLowerCase();
    return analyses.filter(
      (a) =>
        (a.submitted_smiles && a.submitted_smiles.toLowerCase().includes(q)) ||
        (a.canonical_smiles && a.canonical_smiles.toLowerCase().includes(q)) ||
        (a.target && a.target.toLowerCase().includes(q)) ||
        (a.disease && a.disease.toLowerCase().includes(q))
    );
  }, [analyses, search]);

  if (!analyses.length) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center glass-card max-w-md mx-auto rounded-3xl gap-4 my-12">
        <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-primary-green-light/10 dark:bg-primary-green-dark/10 text-primary-green-light dark:text-primary-green-dark border border-primary-green-light/20 dark:border-primary-green-dark/20 animate-bounce">
          <Dna className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-bold text-text-charcoal dark:text-text-offwhite font-heading">No Analyses Yet</h3>
        <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark leading-relaxed">
          Submit your first molecule query on the home screen to view your patent FTO history.
        </p>
        <button 
          className="btn-primary" 
          onClick={() => router.push('/')}
        >
          New Analysis
        </button>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-8 max-w-3xl mx-auto">
      {/* Search Input Bar */}
      <div className="relative w-full max-w-md mx-auto">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-sage-gray-light dark:text-sage-gray-dark" />
        <input
          type="text"
          className="w-full text-xs pl-11 pr-4 py-3 rounded-2xl border border-sage-gray-light/15 dark:border-sage-gray-dark/15 bg-card-mint-light/40 dark:bg-card-mint-dark/40 focus:bg-transparent focus:ring-1 focus:ring-glow-green focus:border-glow-green text-text-charcoal dark:text-text-offwhite placeholder-sage-gray-light/50 dark:placeholder-sage-gray-dark/40 outline-none transition-all duration-200"
          placeholder="Search by SMILES, target, or disease..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-center glass-card max-w-md mx-auto rounded-3xl gap-2">
          <div className="text-xl">🔎</div>
          <h3 className="text-sm font-bold text-text-charcoal dark:text-text-offwhite font-heading">No Results</h3>
          <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark">
            No analyses match your search criteria.
          </p>
        </div>
      ) : (
        /* Vertical Connecting Timeline Container */
        <div className="relative pl-8 pr-2 flex flex-col gap-6 text-left">
          {/* Vertical timeline green-glowing track */}
          <div className="absolute left-3.5 top-2 bottom-2 w-[2px] bg-gradient-to-b from-primary-green-light to-emerald-600 dark:from-primary-green-dark dark:to-glow-green opacity-40 dark:opacity-30" />

          {filtered.map((analysis) => {
            const recommendation =
              analysis.overall_recommendation || 'Requires Expert Review';
            const patentCount =
              analysis.patent_count || analysis.patents?.length || 0;
            const smilesStr = analysis.submitted_smiles || analysis.canonical_smiles || 'N/A';
            const smilesTruncated =
              smilesStr.length > 60
                ? smilesStr.substring(0, 60) + '...'
                : smilesStr;

            return (
              <div
                key={analysis.id}
                onClick={() => router.push(`/analysis/${analysis.id}`)}
                className="relative group cursor-pointer"
              >
                {/* Glowing Pulsing Timeline Node */}
                <div className="absolute -left-8 top-1/2 -translate-x-[2px] -translate-y-1/2 w-3.5 h-3.5 rounded-full border border-glow-green bg-bg-forest-light dark:bg-bg-forest-dark flex items-center justify-center z-10 shadow-[0_0_8px_rgba(0,237,100,0.5)]">
                  <div className="w-1.5 h-1.5 rounded-full bg-glow-green group-hover:scale-125 transition-transform duration-200" />
                </div>

                {/* History Glass Card */}
                <div className="glass-card p-5 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-sage-gray-light/10 dark:border-sage-gray-dark/10 hover:border-primary-green-light/30 dark:hover:border-primary-green-dark/30 hover:-translate-y-[1px] transition-all duration-300">
                  <div className="flex flex-col gap-2.5 max-w-xl">
                    {/* Structure SMILES */}
                    <div className="flex items-center gap-2">
                      <code className="text-[10px] font-mono p-1.5 rounded bg-slate-500/5 text-text-charcoal dark:text-text-offwhite border border-sage-gray-light/5 dark:border-sage-gray-dark/5">
                        {smilesTruncated}
                      </code>
                    </div>

                    {/* Metadata tags */}
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-sage-gray-light dark:text-sage-gray-dark">
                      {analysis.target && (
                        <span className="flex items-center gap-1 font-semibold">
                          <Target className="w-3.5 h-3.5 text-primary-green-light dark:text-primary-green-dark" />
                          {analysis.target}
                        </span>
                      )}
                      {analysis.disease && (
                        <span className="flex items-center gap-1 font-semibold">
                          <Clock className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                          {analysis.disease}
                        </span>
                      )}
                      <span className="flex items-center gap-1 font-medium">
                        <Calendar className="w-3.5 h-3.5" />
                        {analysis.created_at ? timeAgo(analysis.created_at) : 'Unknown'}
                      </span>
                    </div>
                  </div>

                  {/* Right indicators */}
                  <div className="flex items-center gap-4 shrink-0 justify-between w-full sm:w-auto mt-2 sm:mt-0 pt-3 sm:pt-0 border-t border-sage-gray-light/5 sm:border-0">
                    <div className="flex flex-col gap-1.5 items-start sm:items-end">
                      <RiskBadge level={recommendation} />
                      <span className="text-[10px] font-bold text-sage-gray-light dark:text-sage-gray-dark font-mono">
                        {patentCount} Overlapping Patent{patentCount !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <ChevronRight className="w-5 h-5 text-sage-gray-light/40 dark:text-sage-gray-dark/40 group-hover:text-primary-green-light dark:group-hover:text-primary-green-dark group-hover:translate-x-1 transition-all duration-300 shrink-0" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
