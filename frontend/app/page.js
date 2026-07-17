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

          <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tighter leading-[1.1] text-text-charcoal font-heading">
            AI Patent <br />
            <span className="bg-gradient-to-r from-primary-green-light via-emerald-500 to-glow-green bg-clip-text text-transparent drop-shadow-[0_0_20px_rgba(21,128,61,0.2)]">
              Intelligence
            </span>
          </h1>

          <p className="text-sm md:text-base text-sage-gray-light dark:text-sage-gray-dark leading-relaxed">
            Analyze molecules against millions of patents using AI-powered similarity analysis and patentability assessment. Accelerate your R&D with hyper-precision insights.
          </p>

          <div className="flex items-center gap-4 mt-2">
            <button onClick={scrollToForm} className="btn-primary flex items-center gap-2 group relative overflow-hidden animate-pulse-glow hover:animate-none">
              <span className="relative z-10 flex items-center gap-2">
                Analyze Molecule
                <Sparkles className="w-4 h-4 text-white group-hover:rotate-12 transition-transform duration-300" />
              </span>
              <div className="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:animate-[shine_1s_ease-out_forwards]" />
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
                className="glass-card p-6 rounded-3xl flex flex-col gap-3 text-left group"
              >
                <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-primary-green-light/8 border border-primary-green-light/15 text-primary-green-light transition-transform duration-300 group-hover:scale-110 group-hover:bg-primary-green-light/15">
                  <Icon className="w-6 h-6 transition-transform duration-300 group-hover:-rotate-6" />
                </div>
                <h3 className="font-extrabold text-base text-text-charcoal tracking-tight leading-none mt-2">
                  {cap.title}
                </h3>
                <p className="text-xs text-sage-gray-light leading-relaxed mt-1">
                  {cap.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>


    </div>
  );
}
