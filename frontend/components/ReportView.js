'use client';

import { useState } from 'react';
import { ShieldAlert, FileText, CheckCircle2, AlertTriangle, Search, Info, HelpCircle } from 'lucide-react';
import RiskBadge from './RiskBadge';

export default function ReportView({ analysis }) {
  const [methodologyOpen, setMethodologyOpen] = useState(false);

  const report = analysis?.report || {};
  const {
    executive_summary,
    key_patents,
    novelty_concerns,
    manual_review_list,
  } = report;

  const overall_recommendation = analysis?.overall_recommendation || 'Requires Expert Review';
  const recommendation_reasoning = analysis?.recommendation_reasoning || '';
  const moleculeSvg = analysis?.molecule_svg || null;

  const molecule = {
    smiles: analysis?.canonical_smiles || analysis?.submitted_smiles || 'N/A',
    target: analysis?.target || 'Not specified',
    disease: analysis?.disease || 'Not specified',
  };

  const date = analysis?.created_at
    ? new Date(analysis.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Unknown date';

  return (
    <div className="w-full flex flex-col gap-6 text-left max-w-4xl mx-auto py-4">
      {/* ─── Header Card with Structure SVG ───────────────────── */}
      <div className="glass-card p-6 rounded-3xl flex flex-col md:flex-row items-center gap-6 justify-between">
        <div className="flex-1 flex flex-col gap-2.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-primary-green-light dark:text-primary-green-dark">
            Patentability Report Briefing
          </span>
          <h2 className="text-xl font-extrabold tracking-tight text-text-charcoal dark:text-text-offwhite font-heading leading-none">
            Molecular Landscape Report
          </h2>
          <span className="text-xs text-sage-gray-light dark:text-sage-gray-dark font-medium">
            Generated: {date}
          </span>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {molecule.target !== 'Not specified' && (
              <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold border border-primary-green-light/20 dark:border-primary-green-dark/20 bg-primary-green-light/5 dark:bg-primary-green-dark/5 text-primary-green-light dark:text-primary-green-dark">
                Target: {molecule.target}
              </span>
            )}
            {molecule.disease !== 'Not specified' && (
              <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold border border-primary-green-light/20 dark:border-primary-green-dark/20 bg-primary-green-light/5 dark:bg-primary-green-dark/5 text-primary-green-light dark:text-primary-green-dark">
                Indication: {molecule.disease}
              </span>
            )}
          </div>
          <div className="mt-3 flex flex-col gap-1">
            <span className="text-[9px] font-bold uppercase tracking-wider text-sage-gray-light dark:text-sage-gray-dark">SMILES String</span>
            <code className="text-[10px] font-mono p-2.5 rounded-xl bg-slate-500/5 text-text-charcoal dark:text-text-offwhite border border-sage-gray-light/10 dark:border-sage-gray-dark/10 break-all select-all">
              {molecule.smiles}
            </code>
          </div>
        </div>

        {/* Dynamic Molecule Vector Drawing Box */}
        {moleculeSvg && (
          <div className="w-full md:w-[160px] h-[160px] flex items-center justify-center rounded-2xl border border-sage-gray-light/10 dark:border-sage-gray-dark/10 bg-white/40 dark:bg-slate-950/20 p-4 shrink-0 shadow-inner">
            <div 
              className="w-full h-full flex items-center justify-center rdkit-svg-container dark:invert dark:hue-rotate-180" 
              dangerouslySetInnerHTML={{ __html: moleculeSvg }}
            />
          </div>
        )}
      </div>

      {/* ─── Legal Disclaimer ───────────────────────────────────── */}
      <div className="p-4 rounded-2xl border border-rose-500/20 dark:border-rose-500/20 bg-rose-500/5 dark:bg-rose-500/5 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
        <div className="flex flex-col gap-0.5 text-[11px] leading-relaxed">
          <span className="font-bold text-rose-500 text-xs">Disclaimer</span>
          <p className="text-sage-gray-light dark:text-sage-gray-dark">
            This is an automated machine-learning evaluation and does not constitute a formal legal FTO opinion. Results should be vetted by a licensed patent attorney prior to making commercial or R&D decisions.
          </p>
        </div>
      </div>

      {/* ─── Executive Summary ──────────────────────────────────── */}
      {executive_summary && (
        <div className="glass-card p-6 rounded-3xl flex flex-col gap-3">
          <h3 className="text-sm font-extrabold font-heading text-text-charcoal dark:text-text-offwhite flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
            Executive Summary
          </h3>
          <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark leading-relaxed">
            {executive_summary}
          </p>
        </div>
      )}

      {/* ─── Overall Recommendation ────────────────────────────── */}
      <div className="glass-card p-6 rounded-3xl flex flex-col gap-4">
        <h3 className="text-sm font-extrabold font-heading text-text-charcoal dark:text-text-offwhite flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
          Overall Risk Recommendation
        </h3>
        <div className="flex items-start justify-between w-full">
          <RiskBadge level={overall_recommendation} />
        </div>
        {recommendation_reasoning && (
          <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark leading-relaxed bg-slate-500/5 dark:bg-slate-500/5 p-4 rounded-2xl border border-sage-gray-light/10 dark:border-sage-gray-dark/10">
            {recommendation_reasoning}
          </p>
        )}
      </div>

      {/* ─── Key Similar Patents ───────────────────────────────── */}
      {key_patents && key_patents.length > 0 && (
        <div className="glass-card p-6 rounded-3xl flex flex-col gap-3">
          <h3 className="text-sm font-extrabold font-heading text-text-charcoal dark:text-text-offwhite flex items-center gap-2">
            <Search className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
            Key Overlapping Patents
          </h3>
          <ul className="flex flex-col gap-2">
            {key_patents.map((p, i) => (
              <li key={i} className="flex items-center gap-2 text-xs font-semibold text-text-charcoal dark:text-text-offwhite bg-slate-500/5 dark:bg-slate-500/5 px-4 py-2.5 rounded-xl border border-sage-gray-light/5 dark:border-sage-gray-dark/5">
                <span className="w-1.5 h-1.5 rounded-full bg-primary-green-light dark:bg-primary-green-dark shrink-0" />
                {typeof p === 'string' ? p : `${p.patent_id || ''} - ${p.title || 'No details'}`}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ─── Potential Novelty Concerns ────────────────────────── */}
      {novelty_concerns && novelty_concerns.length > 0 && (
        <div className="glass-card p-6 rounded-3xl flex flex-col gap-3 border-amber-500/20 dark:border-amber-500/20 bg-amber-500/5 dark:bg-amber-500/5">
          <h3 className="text-sm font-extrabold font-heading text-amber-600 dark:text-amber-400 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Potential Novelty Concerns
          </h3>
          <ul className="flex flex-col gap-2">
            {novelty_concerns.map((concern, i) => (
              <li key={i} className="flex items-start gap-2.5 text-xs text-sage-gray-light dark:text-sage-gray-dark">
                <span className="text-amber-500 font-bold mt-0.5">▲</span>
                {concern}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ─── Patents Requiring Manual Review ────────────────────── */}
      {manual_review_list && manual_review_list.length > 0 && (
        <div className="glass-card p-6 rounded-3xl flex flex-col gap-3">
          <h3 className="text-sm font-extrabold font-heading text-text-charcoal dark:text-text-offwhite flex items-center gap-2">
            <Info className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
            Patents Requiring Manual Review
          </h3>
          <ul className="flex flex-col gap-2">
            {manual_review_list.map((p, i) => (
              <li key={i} className="flex items-center gap-2 text-xs font-semibold text-text-charcoal dark:text-text-offwhite bg-slate-500/5 dark:bg-slate-500/5 px-4 py-2.5 rounded-xl border border-sage-gray-light/5 dark:border-sage-gray-dark/5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 shrink-0" />
                {typeof p === 'string' ? p : `${p.patent_id || ''} - ${p.reason || p.title || ''}`}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ─── Methodology Accordion ───────────────────────────────── */}
      <div className="glass-card p-6 rounded-3xl flex flex-col gap-1 transition-all duration-300">
        <button
          onClick={() => setMethodologyOpen(!methodologyOpen)}
          className="w-full flex items-center justify-between font-extrabold font-heading text-sm text-text-charcoal dark:text-text-offwhite cursor-pointer select-none"
        >
          <span className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
            Methodology & Scoring System
          </span>
          <span className="text-xs text-sage-gray-light dark:text-sage-gray-dark">
            {methodologyOpen ? '▲ Hide' : '▼ View'}
          </span>
        </button>

        {methodologyOpen && (
          <div className="flex flex-col gap-3 text-[11px] text-sage-gray-light dark:text-sage-gray-dark leading-relaxed mt-4 border-t border-sage-gray-light/10 dark:border-sage-gray-dark/10 pt-4 animate-slideUp">
            <p>
              The workspace utilizes a two-stage evaluation logic. First, structurally-similar compounds are fetched from databases. Next, the LLM classifies matching factors into Low, Medium, or High scores.
            </p>
            <p>
              <strong>Similarity Weight Formula:</strong><br />
              <code className="text-xs bg-slate-500/5 dark:bg-slate-500/5 px-2.5 py-1.5 rounded-md border border-sage-gray-light/10 dark:border-sage-gray-dark/10 block mt-1 select-all font-mono">
                Score = 0.40 x Molecule + 0.25 x Target + 0.20 x Indication + 0.15 x Mechanism
              </code>
            </p>
            <p>
              <strong>Risk Classification Thresholds:</strong><br />
              • High Patent Risk: Similarity score of 85+ or high molecule and high indication overlap.<br />
              • Requires Expert Review: Similarity score between 60 and 84.<br />
              • Low Patent Risk: Similarity score below 60.
            </p>
            <p>
              <strong>Confidence Attribute:</strong> Each patent includes a confidence level evaluated during Stage 1 based on available title and abstract data.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
