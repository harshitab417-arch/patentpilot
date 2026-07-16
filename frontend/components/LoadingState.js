'use client';

import { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, Search, Database, BrainCircuit, FileSpreadsheet } from 'lucide-react';
import Molecule3D from './Molecule3D';

const STEPS = [
  { id: 1, label: 'Searching SureChEMBL', icon: Search },
  { id: 2, label: 'Searching EPO Database', icon: Database },
  { id: 3, label: 'Analyzing Patents with AI', icon: BrainCircuit },
  { id: 4, label: 'Generating AI Report', icon: FileSpreadsheet },
];

export default function LoadingState({ status = 'pending' }) {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(1);

  useEffect(() => {
    // Increment progress and step status smoothly over ~7 seconds
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        const nextProgress = prev + 1.5;
        
        // Update current step index based on progress threshold
        if (nextProgress < 25) {
          setCurrentStep(1);
        } else if (nextProgress < 50) {
          setCurrentStep(2);
        } else if (nextProgress < 75) {
          setCurrentStep(3);
        } else {
          setCurrentStep(4);
        }
        
        return Math.min(nextProgress, 100);
      });
    }, 100);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-bg-forest-light dark:bg-bg-forest-dark z-50 overflow-y-auto px-4 py-8">
      {/* ─── Big Scanning Molecule 3D Visual ────────────────────── */}
      <div className="mb-6 relative flex items-center justify-center">
        <Molecule3D size="xl" scanning={true} />
      </div>

      {/* ─── Stepper Card ───────────────────────────────────────── */}
      <div className="w-full max-w-sm glass-card p-6 rounded-3xl flex flex-col gap-6 text-left shadow-[0_12px_40px_rgba(0,0,0,0.1)]">
        {/* Title & Progress Header */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-primary-green-light dark:text-primary-green-dark">
              Analysis in Progress
            </span>
            <span className="text-xs font-mono font-bold text-text-charcoal dark:text-text-offwhite">
              {status}
            </span>
          </div>
          {/* Progress bar container */}
          <div className="w-full h-1 bg-slate-500/10 dark:bg-slate-500/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-green-light to-glow-green dark:from-primary-green-dark dark:to-glow-green rounded-full shadow-[0_0_8px_rgba(0,237,100,0.5)] transition-all duration-100"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Vertical Stepper list */}
        <div className="flex flex-col gap-4 relative pl-4 mt-2">
          {/* Connector timeline line */}
          <div className="absolute left-7 top-4 bottom-4 w-[2px] bg-slate-500/10 dark:bg-slate-500/20 z-0" />

          {STEPS.map((step) => {
            const Icon = step.icon;
            const isCompleted = currentStep > step.id;
            const isActive = currentStep === step.id;
            
            return (
              <div 
                key={step.id} 
                className={`flex items-center gap-4 relative z-10 transition-all duration-300 ${
                  isCompleted || isActive ? 'opacity-100' : 'opacity-30'
                }`}
              >
                {/* Node circle */}
                <div className={`flex items-center justify-center w-6 h-6 rounded-full border ${
                  isCompleted
                    ? 'bg-primary-green-light/10 dark:bg-primary-green-dark/10 border-primary-green-light/35 dark:border-primary-green-dark/35 text-primary-green-light dark:text-primary-green-dark'
                    : isActive
                    ? 'bg-glow-green/10 border-glow-green text-glow-green animate-pulse-glow'
                    : 'bg-slate-500/5 border-slate-500/20 text-sage-gray-light dark:text-sage-gray-dark'
                }`}>
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : isActive ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <div className="w-1.5 h-1.5 rounded-full bg-current" />
                  )}
                </div>

                {/* Step contents */}
                <div className="flex flex-col">
                  <span className={`text-[10px] font-bold uppercase tracking-wider ${
                    isActive ? 'text-primary-green-light dark:text-primary-green-dark' : 'text-sage-gray-light dark:text-sage-gray-dark'
                  }`}>
                    Step {step.id} {isActive && '(Active)'}
                  </span>
                  <span className="text-xs font-bold text-text-charcoal dark:text-text-offwhite">
                    {step.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer info/tagline */}
        <div className="flex items-center justify-center gap-1.5 border-t border-sage-gray-light/10 dark:border-sage-gray-dark/10 pt-4 text-[10px] text-sage-gray-light dark:text-sage-gray-dark justify-center font-bold tracking-wide">
          <svg className="w-3.5 h-3.5 text-primary-green-light dark:text-primary-green-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 2L2 22h20L12 2z" />
          </svg>
          PatentPilot
        </div>
      </div>
    </div>
  );
}
