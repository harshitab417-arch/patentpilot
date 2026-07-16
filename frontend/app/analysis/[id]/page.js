'use client';

import { use, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Dna, Sparkles, FileText, Search, Activity, HeartPulse, ChevronLeft, ShieldAlert } from 'lucide-react';
import { getJobStatus, getAnalysis } from '@/lib/api';
import LoadingState from '@/components/LoadingState';
import RiskBadge from '@/components/RiskBadge';
import PatentTable from '@/components/PatentTable';
import ReportView from '@/components/ReportView';

const POLL_INTERVAL_MS = 3000;

export default function AnalysisPage({ params }) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;
  const router = useRouter();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('pending');
  const [pollCount, setPollCount] = useState(0);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!jobId) return;

    let mounted = true;
    let intervalId;

    const fetchStatus = async () => {
      try {
        const data = await getJobStatus(jobId);
        if (!mounted) return;

        setStatus(data.status);
        setPollCount((count) => count + 1);

        if (data.status === 'completed') {
          if (!data.analysis_id) {
            throw new Error('Job completed but no analysis ID was returned');
          }
          const analysisData = await getAnalysis(data.analysis_id);
          setAnalysis(analysisData);
          setLoading(false);
          clearInterval(intervalId);
        } else if (data.status === 'failed') {
          setError(data.error || 'Analysis failed during processing.');
          setLoading(false);
          clearInterval(intervalId);
        }
      } catch (err) {
        if (!mounted) return;
        setError(err.message || 'Failed to fetch job status.');
        setLoading(false);
        clearInterval(intervalId);
      }
    };

    fetchStatus();
    intervalId = setInterval(fetchStatus, POLL_INTERVAL_MS);

    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, [jobId]);

  if (loading) {
    return <LoadingState status={status} />;
  }

  if (error) {
    return (
      <div className="w-full max-w-5xl mx-auto px-6 py-24 flex items-center justify-center">
        <div className="glass-card p-8 rounded-3xl flex flex-col items-center justify-center text-center gap-4 max-w-md">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-500 flex items-center justify-center text-xl">
            ⚠️
          </div>
          <h2 className="text-base font-bold text-text-charcoal dark:text-text-offwhite font-heading">Analysis Error</h2>
          <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark break-words">{error}</p>
          <button
            className="btn-ghost flex items-center gap-1.5"
            onClick={() => router.push('/')}
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const recommendation = analysis?.overall_recommendation || 'Requires Expert Review';
  const executiveSummary = analysis?.report?.executive_summary || '';
  const patents = analysis?.patents || [];

  const TABS = [
    { key: 'overview', label: 'Overview', icon: Sparkles },
    { key: 'patents', label: 'Patents', icon: Search },
    { key: 'report', label: 'Report', icon: FileText },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto px-6 py-12 flex flex-col gap-8">
      <button
        className="self-start flex items-center gap-1 text-xs font-bold text-sage-gray-light dark:text-sage-gray-dark hover:text-primary-green-light dark:hover:text-primary-green-dark cursor-pointer py-1"
        onClick={() => router.push('/')}
      >
        <ChevronLeft className="w-4 h-4" />
        Back to Home
      </button>

      <div className="relative flex items-center gap-1 bg-slate-500/5 dark:bg-slate-500/5 p-1 rounded-2xl border border-sage-gray-light/10 dark:border-sage-gray-dark/10 self-start">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200 cursor-pointer ${
                isActive
                  ? 'bg-primary-green-light/8 dark:bg-primary-green-dark/8 border border-primary-green-light/15 dark:border-primary-green-dark/15 text-primary-green-light dark:text-primary-green-dark'
                  : 'text-sage-gray-light dark:text-sage-gray-dark hover:text-text-charcoal dark:hover:text-text-offwhite hover:bg-slate-500/5 dark:hover:bg-slate-500/5 border border-transparent'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
              {tab.key === 'patents' && (
                <span className="ml-1 px-1.5 py-0.5 rounded-md text-[10px] font-bold font-mono bg-slate-500/10 text-sage-gray-light dark:text-sage-gray-dark border border-sage-gray-light/10 dark:border-sage-gray-dark/10">
                  {patents.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="w-full">
        {activeTab === 'overview' && (
          <div className="flex flex-col gap-6 animate-slideUp">
            <div className="glass-card p-6 rounded-3xl flex flex-col gap-4 text-left">
              <h3 className="text-sm font-extrabold font-heading text-text-charcoal dark:text-text-offwhite flex items-center gap-2">
                <Dna className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
                Molecule Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="flex flex-col gap-1 border-r border-sage-gray-light/10 dark:border-sage-gray-dark/10 pr-4">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-sage-gray-light dark:text-sage-gray-dark">
                    Submitted SMILES
                  </span>
                  <code className="text-[10px] font-mono p-2.5 rounded-xl bg-slate-500/5 text-text-charcoal dark:text-text-offwhite border border-sage-gray-light/10 dark:border-sage-gray-dark/10 break-all select-all leading-normal">
                    {analysis?.canonical_smiles || analysis?.submitted_smiles || 'N/A'}
                  </code>
                </div>
                <div className="flex flex-col gap-4 pl-0 md:pl-4 justify-center">
                  {analysis?.target && (
                    <div className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-sage-gray-light dark:text-sage-gray-dark">Target Protein</span>
                        <span className="text-text-charcoal dark:text-text-offwhite font-bold">{analysis.target}</span>
                      </div>
                    </div>
                  )}
                  {analysis?.disease && (
                    <div className="flex items-center gap-2">
                      <HeartPulse className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-[9px] font-bold uppercase tracking-wider text-sage-gray-light dark:text-sage-gray-dark">Indication / Disease</span>
                        <span className="text-text-charcoal dark:text-text-offwhite font-bold">{analysis.disease}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              {!analysis?.evidence_sufficient && (
                <div className="p-3 text-[10px] font-semibold text-amber-500 dark:text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center gap-2 mt-2">
                  <ShieldAlert className="w-4 h-4 shrink-0" />
                  <span>Limited evidence: fewer than 3 patents found. Results should be interpreted with caution.</span>
                </div>
              )}
            </div>

            <div className="glass-card p-6 rounded-3xl flex flex-col gap-4 text-left">
              <h3 className="text-sm font-extrabold font-heading text-text-charcoal dark:text-text-offwhite flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
                Overall Risk Recommendation
              </h3>
              <div className="self-start">
                <RiskBadge level={recommendation} />
              </div>
              {analysis?.recommendation_reasoning && (
                <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark leading-relaxed bg-slate-500/5 dark:bg-slate-500/5 p-4 rounded-2xl border border-sage-gray-light/10 dark:border-sage-gray-dark/10">
                  {analysis.recommendation_reasoning}
                </p>
              )}
            </div>

            {executiveSummary && (
              <div className="glass-card p-6 rounded-3xl flex flex-col gap-3 text-left">
                <h3 className="text-sm font-extrabold font-heading text-text-charcoal dark:text-text-offwhite flex items-center gap-2">
                  <FileText className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
                  Executive Summary
                </h3>
                <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark leading-relaxed">
                  {executiveSummary}
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
              <div className="glass-card p-5 rounded-2xl flex flex-col gap-1 select-none hover:scale-[1.02] transition-transform duration-300">
                <span className="text-[10px] font-bold uppercase tracking-wider text-sage-gray-light dark:text-sage-gray-dark">Total Hits</span>
                <span className="text-3xl font-extrabold text-primary-green-light dark:text-primary-green-dark font-heading">{patents.length}</span>
                <span className="text-[9px] font-medium text-sage-gray-light dark:text-sage-gray-dark leading-tight">Similar patents found</span>
              </div>
              <div className="glass-card p-5 rounded-2xl flex flex-col gap-1 select-none hover:scale-[1.02] transition-transform duration-300 border-rose-500/10 bg-rose-500/5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-rose-500/80">High Risk</span>
                <span className="text-3xl font-extrabold text-rose-500 font-heading">
                  {patents.filter((p) => p.risk_label === 'High').length}
                </span>
                <span className="text-[9px] font-medium text-rose-500/80 leading-tight">Requires urgent review</span>
              </div>
              <div className="glass-card p-5 rounded-2xl flex flex-col gap-1 select-none hover:scale-[1.02] transition-transform duration-300 border-amber-500/10 bg-amber-500/5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">Review Required</span>
                <span className="text-3xl font-extrabold text-amber-600 dark:text-amber-400 font-heading">
                  {patents.filter((p) => p.risk_label === 'Medium').length}
                </span>
                <span className="text-[9px] font-medium text-amber-600/80 dark:text-amber-400/80 leading-tight">Manual audit recommended</span>
              </div>
              <div className="glass-card p-5 rounded-2xl flex flex-col gap-1 select-none hover:scale-[1.02] transition-transform duration-300 border-emerald-500/10 bg-emerald-500/5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">Low Risk</span>
                <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-heading">
                  {patents.filter((p) => p.risk_label === 'Low').length}
                </span>
                <span className="text-[9px] font-medium text-emerald-600/80 dark:text-emerald-400/80 leading-tight">No active overlap found</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'patents' && (
          <div className="w-full animate-slideUp">
            <PatentTable patents={patents} />
          </div>
        )}

        {activeTab === 'report' && (
          <div className="w-full animate-slideUp">
            <ReportView analysis={analysis} />
          </div>
        )}
      </div>
    </div>
  );
}
