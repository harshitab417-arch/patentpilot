'use client';

import { useState } from 'react';
import { Building, Calendar, Scale, ExternalLink, ShieldCheck, HelpCircle } from 'lucide-react';
import RiskBadge from './RiskBadge';
import ConfidenceBadge from './ConfidenceBadge';

function formatPercent(score) {
  if (score === null || score === undefined) return '0%';
  const value = Number(score);
  if (Number.isNaN(value)) return '0%';
  if (value <= 1) return `${(value * 100).toFixed(0)}%`;
  return `${value.toFixed(0)}%`;
}

export default function PatentCard({ patent }) {
  const [expanded, setExpanded] = useState(false);

  const {
    patent_id,
    title,
    patent_url,
    assignee,
    pub_date,
    legal_status,
    similarity_score,
    risk_label,
    confidence_label,
    abstract,
    ai_explanation,
    source,
    abstract_summary,
    matched_factors = [],
    reason,
  } = patent;

  const similarityDisplay = formatPercent(similarity_score);
  const riskLevel = risk_label || 'Medium';
  const factors = Array.isArray(matched_factors) ? matched_factors : [];
  const explanation = reason || ai_explanation || 'No structured reasoning available.';

  const formatDate = (d) => {
    if (!d) return null;
    if (d.length === 8) {
      return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
    }
    return d;
  };

  return (
    <div className={`glass-card p-6 rounded-3xl flex flex-col gap-4 text-left transition-all duration-300 relative group overflow-hidden ${
      expanded ? 'border-primary-green-light/40 dark:border-primary-green-dark/40 shadow-[0_8px_32px_rgba(0,237,100,0.06)]' : ''
    }`}>
      {/* ─── Header Section ─────────────────────────────────────── */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            {patent_url ? (
              <a
                href={patent_url}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-xs font-bold text-primary-green-light dark:text-primary-green-dark hover:underline flex items-center gap-1 group/link cursor-pointer"
                title="Open in Google Patents"
              >
                {patent_id || 'Unknown ID'}
                <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover/link:opacity-100 transition-opacity duration-150" />
              </a>
            ) : (
              <span className="font-mono text-xs font-bold text-primary-green-light dark:text-primary-green-dark">
                {patent_id || 'Unknown ID'}
              </span>
            )}
          </div>
          <RiskBadge level={riskLevel} />
        </div>

        {patent_url ? (
          <a
            href={patent_url}
            target="_blank"
            rel="noreferrer"
            className="font-bold text-sm text-text-charcoal dark:text-text-offwhite hover:text-primary-green-light dark:hover:text-primary-green-dark transition-colors duration-250 cursor-pointer font-heading leading-tight"
          >
            {title || 'Title not available'}
          </a>
        ) : (
          <h3 className="font-bold text-sm text-text-charcoal dark:text-text-offwhite font-heading leading-tight">
            {title || 'Title not available'}
          </h3>
        )}
      </div>

      {/* ─── Metadata Grid ──────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[10px] text-sage-gray-light dark:text-sage-gray-dark border-t border-b border-sage-gray-light/10 dark:border-sage-gray-dark/10 py-2.5">
        {assignee && (
          <span className="flex items-center gap-1.5 font-medium">
            <Building className="w-3.5 h-3.5" />
            {assignee}
          </span>
        )}
        {pub_date && (
          <span className="flex items-center gap-1.5 font-medium">
            <Calendar className="w-3.5 h-3.5" />
            {formatDate(pub_date)}
          </span>
        )}
        {legal_status && (
          <span className="flex items-center gap-1.5 font-medium">
            <Scale className="w-3.5 h-3.5" />
            {legal_status}
          </span>
        )}
      </div>

      {/* ─── Scores Grid ───────────────────────────────────────── */}
      <div className="flex flex-col gap-2 py-1">
        <div className="flex items-center justify-between text-xs font-bold">
          <span className="text-sage-gray-light dark:text-sage-gray-dark">Similarity Score</span>
          <span className="text-text-charcoal dark:text-text-offwhite font-mono">{similarityDisplay}</span>
        </div>
        <div className="w-full h-1.5 bg-slate-500/10 dark:bg-slate-500/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-green-light to-glow-green dark:from-primary-green-dark dark:to-glow-green rounded-full shadow-[0_0_8px_rgba(0,237,100,0.3)] transition-all duration-300"
            style={{ width: similarityDisplay }}
          />
        </div>
      </div>

      {/* ─── Structured Explanation ──────────────────────────────── */}
      <div className="bg-slate-500/5 dark:bg-slate-500/5 p-4 rounded-2xl flex flex-col gap-3 text-xs leading-relaxed">
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-sage-gray-light dark:text-sage-gray-dark">
            AI Relevance Explanation
          </span>
          <p className="text-text-charcoal dark:text-text-offwhite font-medium">
            {explanation}
          </p>
        </div>

        {factors.length > 0 && (
          <div className="flex flex-col gap-1.5 border-t border-sage-gray-light/10 dark:border-sage-gray-dark/10 pt-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-sage-gray-light dark:text-sage-gray-dark">
              Matched Factors
            </span>
            <div className="flex flex-wrap gap-1.5">
              {factors.map((factor, index) => (
                <span 
                  key={`${factor}-${index}`} 
                  className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-primary-green-light/8 dark:bg-primary-green-dark/8 border border-primary-green-light/15 dark:border-primary-green-dark/15 text-primary-green-light dark:text-primary-green-dark"
                >
                  {factor}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ─── Badges row ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between text-xs mt-1">
        <div className="flex items-center gap-2">
          {confidence_label && <ConfidenceBadge level={confidence_label} />}
          {source && (
            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold border border-sage-gray-light/10 dark:border-sage-gray-dark/10 bg-slate-500/5 text-sage-gray-light dark:text-sage-gray-dark">
              {source}
            </span>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs font-semibold text-primary-green-light dark:text-primary-green-dark hover:underline cursor-pointer py-1"
        >
          {expanded ? '▲ Hide details' : '▼ Show details'}
        </button>
      </div>

      {/* ─── Expandable Details Section ─────────────────────────── */}
      {expanded && (
        <div className="flex flex-col gap-4 border-t border-sage-gray-light/10 dark:border-sage-gray-dark/10 pt-4 text-xs animate-slideUp">
          {abstract_summary && (
            <div className="flex flex-col gap-1 text-left">
              <h4 className="font-bold text-text-charcoal dark:text-text-offwhite font-heading">
                Abstract Summary
              </h4>
              <p className="text-sage-gray-light dark:text-sage-gray-dark">
                {abstract_summary}
              </p>
            </div>
          )}
          <div className="flex flex-col gap-1 text-left">
            <h4 className="font-bold text-text-charcoal dark:text-text-offwhite font-heading">
              Full Abstract
            </h4>
            <p className="text-sage-gray-light dark:text-sage-gray-dark leading-relaxed">
              {abstract || 'Abstract not available'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
