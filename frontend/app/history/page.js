'use client';

import { useState, useEffect } from 'react';
import { Clock, AlertCircle } from 'lucide-react';
import { listAnalyses } from '@/lib/api';
import HistoryList from '@/components/HistoryList';

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showLoading, setShowLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setShowLoading(true), 200);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const data = await listAnalyses();
        setAnalyses(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message || 'Failed to load analysis history');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto px-6 py-12 flex flex-col gap-8">
      {/* Page Header */}
      <div className="flex flex-col gap-1.5 text-left">
        <h1 className="text-2xl font-extrabold tracking-tight text-text-charcoal font-heading flex items-center gap-2">
          <Clock className="w-6 h-6 text-primary-green-light" />
          Search History
        </h1>
        <p className="text-xs text-sage-gray-light">
          Revisit previous molecular structures and their corresponding patent FTO reports.
        </p>
      </div>

      {loading && showLoading && (
        /* Loading Pulsing Steppers */
        <div className="flex flex-col gap-4 max-w-3xl mx-auto w-full">
          {[...Array(4)].map((_, i) => (
            <div 
              key={i} 
              className="w-full h-24 rounded-2xl bg-slate-500/5 border border-sage-gray-light/10 animate-pulse flex flex-col gap-3 p-5"
            >
              <div className="h-4 w-1/4 bg-slate-500/10 rounded-full" />
              <div className="h-3 w-1/2 bg-slate-500/10 rounded-full" />
            </div>
          ))}
        </div>
      )}

      {loading && !showLoading && (
        <div className="min-h-[50vh]" />
      )}

      {!loading && error && (
        /* Error Card */
        <div className="glass-card p-8 rounded-3xl flex flex-col items-center justify-center text-center gap-4 max-w-md mx-auto">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-500 flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-text-charcoal font-heading">Failed to Load History</h3>
          <p className="text-xs text-sage-gray-light">{error}</p>
          <button 
            className="btn-primary flex items-center gap-2" 
            onClick={() => window.location.reload()}
          >
            Try Again
          </button>
        </div>
      )}

      {!loading && !error && (
        <HistoryList analyses={analyses} />
      )}
    </div>
  );
}
