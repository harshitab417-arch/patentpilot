'use client';

import { useState, useMemo } from 'react';
import { SlidersHorizontal, ArrowUpDown } from 'lucide-react';
import PatentCard from './PatentCard';

export default function PatentTable({ patents = [] }) {
  const [sortBy, setSortBy] = useState('score');
  const [sortDir, setSortDir] = useState('desc');

  const sorted = useMemo(() => {
    const arr = [...patents];
    arr.sort((a, b) => {
      let aVal, bVal;
      switch (sortBy) {
        case 'score':
          aVal = a.patent_score || 0;
          bVal = b.patent_score || 0;
          break;
        case 'similarity':
          aVal = a.similarity_score || 0;
          bVal = b.similarity_score || 0;
          break;
        case 'date':
          aVal = a.pub_date || '';
          bVal = b.pub_date || '';
          break;
        default:
          aVal = a.patent_score || 0;
          bVal = b.patent_score || 0;
      }
      if (sortDir === 'asc') return aVal > bVal ? 1 : -1;
      return aVal < bVal ? 1 : -1;
    });
    return arr;
  }, [patents, sortBy, sortDir]);

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
  };

  if (!patents.length) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center glass-card max-w-md mx-auto rounded-3xl gap-3 my-12">
        <div className="text-xl">📋</div>
        <h3 className="text-sm font-bold text-text-charcoal dark:text-text-offwhite font-heading">No Patents Found</h3>
        <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark">
          No similar patent matches were detected for this structure.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-6 text-left max-w-4xl mx-auto">
      {/* Table Controls Panel */}
      <div className="glass-card px-6 py-4 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-sage-gray-light/10 dark:border-sage-gray-dark/10">
        <span className="text-xs text-sage-gray-light dark:text-sage-gray-dark font-medium flex items-center gap-1.5">
          <SlidersHorizontal className="w-3.5 h-3.5 text-primary-green-light dark:text-primary-green-dark" />
          Showing <strong className="text-text-charcoal dark:text-text-offwhite">{sorted.length}</strong> of <strong className="text-text-charcoal dark:text-text-offwhite">{patents.length}</strong> patents
        </span>

        {/* Sort Controls */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-sage-gray-light dark:text-sage-gray-dark font-medium flex items-center gap-1">
            <ArrowUpDown className="w-3.5 h-3.5" />
            Sort by:
          </span>
          <button
            className={`px-3 py-1.5 rounded-lg border text-[11px] font-bold cursor-pointer transition-all duration-200 ${
              sortBy === 'score'
                ? 'border-primary-green-light/30 bg-primary-green-light/8 text-primary-green-light dark:border-primary-green-dark/30 dark:bg-primary-green-dark/8 dark:text-primary-green-dark'
                : 'border-sage-gray-light/10 dark:border-sage-gray-dark/10 text-sage-gray-light dark:text-sage-gray-dark hover:text-text-charcoal dark:hover:text-text-offwhite hover:bg-slate-500/5'
            }`}
            onClick={() => toggleSort('score')}
          >
            Risk Score {sortBy === 'score' ? (sortDir === 'desc' ? '↓' : '↑') : ''}
          </button>
          <button
            className={`px-3 py-1.5 rounded-lg border text-[11px] font-bold cursor-pointer transition-all duration-200 ${
              sortBy === 'similarity'
                ? 'border-primary-green-light/30 bg-primary-green-light/8 text-primary-green-light dark:border-primary-green-dark/30 dark:bg-primary-green-dark/8 dark:text-primary-green-dark'
                : 'border-sage-gray-light/10 dark:border-sage-gray-dark/10 text-sage-gray-light dark:text-sage-gray-dark hover:text-text-charcoal dark:hover:text-text-offwhite hover:bg-slate-500/5'
            }`}
            onClick={() => toggleSort('similarity')}
          >
            Similarity {sortBy === 'similarity' ? (sortDir === 'desc' ? '↓' : '↑') : ''}
          </button>
          <button
            className={`px-3 py-1.5 rounded-lg border text-[11px] font-bold cursor-pointer transition-all duration-200 ${
              sortBy === 'date'
                ? 'border-primary-green-light/30 bg-primary-green-light/8 text-primary-green-light dark:border-primary-green-dark/30 dark:bg-primary-green-dark/8 dark:text-primary-green-dark'
                : 'border-sage-gray-light/10 dark:border-sage-gray-dark/10 text-sage-gray-light dark:text-sage-gray-dark hover:text-text-charcoal dark:hover:text-text-offwhite hover:bg-slate-500/5'
            }`}
            onClick={() => toggleSort('date')}
          >
            Pub Date {sortBy === 'date' ? (sortDir === 'desc' ? '↓' : '↑') : ''}
          </button>
        </div>
      </div>

      {/* Patent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
        {sorted.map((patent, idx) => (
          <PatentCard key={patent.patent_id || idx} patent={patent} />
        ))}
      </div>
    </div>
  );
}
