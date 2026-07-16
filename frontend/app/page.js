'use client';

import { Sparkles, Search, BrainCircuit, ShieldAlert, FileText, History, Compass, CheckCircle2 } from 'lucide-react';
import MoleculeForm from '@/components/MoleculeForm';
import Molecule3D from '@/components/Molecule3D';

const CAPABILITIES = [
  {
    icon: Search,
    title: 'Patent Search',
    description: 'Semantic search across millions of prior art and chemical patent databases.',
  },
  {
    icon: BrainCircuit,
    title: 'AI Analysis',
    description: 'Automated claim dissection, structure mapping, and novelty assessment.',
  },
  {
    icon: FileText,
    title: 'Patentability Report',
    description: 'Instant generation of structured FTO briefs with factor attribution.',
  },
  {
    icon: Compass,
    title: 'Molecule Viz',
    description: '3D structural mapping against claimed scaffolds and similarity zones.',
  },
  {
    icon: History,
    title: 'Patent History',
    description: 'Track family trees, litigation status, and historic filings in real-time.',
  },
];

export default function HomePage() {
  const scrollToForm = () => {
    const el = document.getElementById('search-anchor');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-12 flex flex-col gap-24">
      {/* ─── Hero Section ───────────────────────────────────────── */}
      <section className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:min-h-[55vh]">
        {/* Left text column */}
        <div className="flex-1 flex flex-col items-start text-left gap-6 max-w-xl">
          {/* Eyebrow Pill */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary-green-light/20 dark:border-primary-green-dark/20 bg-primary-green-light/5 dark:bg-primary-green-dark/5 text-primary-green-light dark:text-primary-green-dark">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-glow-green opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-glow-green"></span>
            </span>
            <span className="text-[11px] font-bold uppercase tracking-wider">AI-Powered Patent Intelligence</span>
          </div>

          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight leading-none text-text-charcoal dark:text-text-offwhite font-heading">
            AI Patent <br />
            <span className="bg-gradient-to-r from-primary-green-light via-emerald-600 to-glow-green dark:from-primary-green-dark dark:via-emerald-400 dark:to-glow-green bg-clip-text text-transparent">
              Intelligence
            </span>
          </h1>

          <p className="text-sm md:text-base text-sage-gray-light dark:text-sage-gray-dark leading-relaxed">
            Analyze molecules against millions of patents using AI-powered similarity analysis and patentability assessment. Accelerate your R&D with hyper-precision insights.
          </p>

          <div className="flex items-center gap-4 mt-2">
            <button onClick={scrollToForm} className="btn-primary flex items-center gap-2 group">
              Analyze Molecule
              <Sparkles className="w-4 h-4 text-white dark:text-[#04120C] group-hover:rotate-12 transition-transform duration-300" />
            </button>
            <button onClick={scrollToForm} className="btn-ghost">
              View Demo
            </button>
          </div>

          {/* Quick trust stats */}
          <div className="flex items-center gap-6 mt-6 border-t border-sage-gray-light/10 dark:border-sage-gray-dark/10 pt-6 w-full text-xs text-sage-gray-light dark:text-sage-gray-dark">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
              <span>10M+ Patents</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
              <span>98% Accuracy</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-primary-green-light dark:text-primary-green-dark" />
              <span>Real-Time AI</span>
            </div>
          </div>
        </div>

        {/* Right 3D Molecule visual column */}
        <div className="flex-1 flex justify-center items-center relative lg:min-h-[400px]">
          <div className="absolute inset-0 bg-radial-gradient from-glow-green/10 to-transparent blur-3xl rounded-full w-[250px] h-[250px] mx-auto pointer-events-none" />
          <div className="relative animate-float">
            <Molecule3D size="lg" />
          </div>
        </div>
      </section>

      {/* ─── Search Form Section (Target of scroll) ─────────────── */}
      <section id="search-anchor" className="scroll-mt-24 flex flex-col items-center">
        <MoleculeForm />
      </section>

      {/* ─── Capabilities Bento-Grid ────────────────────────────── */}
      <section className="flex flex-col gap-8">
        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-text-charcoal dark:text-text-offwhite font-heading text-left">
          Core Capabilities
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {CAPABILITIES.map((cap, i) => {
            const Icon = cap.icon;
            return (
              <div 
                key={i} 
                className="glass-card p-6 rounded-2xl flex flex-col gap-3 text-left hover:scale-[1.02] transition-transform duration-300"
              >
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary-green-light/8 dark:bg-primary-green-dark/8 border border-primary-green-light/15 dark:border-primary-green-dark/15 text-primary-green-light dark:text-primary-green-dark">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-sm text-text-charcoal dark:text-text-offwhite tracking-tight leading-none mt-1">
                  {cap.title}
                </h3>
                <p className="text-[11px] text-sage-gray-light dark:text-sage-gray-dark leading-relaxed leading-normal mt-1">
                  {cap.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ─── Legal Disclaimer Footer ───────────────────────────── */}
      <footer className="glass-card p-6 rounded-2xl flex items-start gap-4 border-rose-500/20 dark:border-rose-500/20 bg-rose-500/5 dark:bg-rose-500/5 text-left max-w-3xl mx-auto">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-rose-500/10 text-rose-500 shrink-0">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div className="flex flex-col gap-1 text-[11px] leading-relaxed">
          <span className="font-bold text-rose-500 text-xs">Legal Disclaimer</span>
          <p className="text-sage-gray-light dark:text-sage-gray-dark">
            PatentPilot is an automated pre-screening triage tool designed for research acceleration. It is not a substitute for professional legal Freedom-to-Operate (FTO) opinions. Always consult a qualified patent attorney for formal legal advice before making synthesis, manufacturing, or commercialization decisions.
          </p>
        </div>
      </footer>
    </div>
  );
}
