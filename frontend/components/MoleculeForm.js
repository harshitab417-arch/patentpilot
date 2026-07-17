'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, HelpCircle, Activity, HeartPulse } from 'lucide-react';
import { submitAnalysis } from '@/lib/api';
import LoadingState from './LoadingState';

const EXAMPLES = [
  {
    label: 'Aspirin',
    smiles: 'CC(=O)Oc1ccccc1C(=O)O',
    target: 'COX-2',
    disease: 'Rheumatoid Arthritis',
  },
  {
    label: 'Ibuprofen',
    smiles: 'CC(C)Cc1ccc(cc1)C(C)C(=O)O',
    target: 'COX-1/COX-2',
    disease: 'Pain/Inflammation',
  },
  {
    label: 'Caffeine',
    smiles: 'Cn1c(=O)c2c(ncn2C)n(C)c1=O',
    target: 'Adenosine Receptor',
    disease: 'Fatigue/Alertness',
  },
  {
    label: 'Acetaminophen',
    smiles: 'CC(=O)Nc1ccc(O)cc1',
    target: 'COX',
    disease: 'Pain/Fever',
  },
  {
    label: 'Diazepam',
    smiles: 'CN1C(=O)CN=C(C2=C1C=CC(=C2)Cl)C3=CC=CC=C3',
    target: 'GABA Receptor',
    disease: 'Anxiety',
  },
];

export default function MoleculeForm() {
  const router = useRouter();
  const [smiles, setSmiles] = useState('');
  const [target, setTarget] = useState('');
  const [disease, setDisease] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fillExample = (example) => {
    setSmiles(example.smiles);
    setTarget(example.target);
    setDisease(example.disease);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!smiles.trim()) {
      setError('SMILES structure is required');
      return;
    }

    setLoading(true);
    try {
      const data = { smiles: smiles.trim() };
      if (target.trim()) data.target = target.trim();
      if (disease.trim()) data.disease = disease.trim();

      const result = await submitAnalysis(data);
      router.push(`/analysis/${result.job_id}`);
    } catch (err) {
      setError(err.message || 'Failed to submit analysis. Ensure backend is running.');
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingState />;
  }

  return (
    <div className="w-full max-w-2xl px-2">
      <form 
        className="glass-card p-8 rounded-3xl flex flex-col gap-6 text-left" 
        onSubmit={handleSubmit}
      >
        <div className="flex flex-col gap-1.5 border-b border-sage-gray-light/10 dark:border-sage-gray-dark/10 pb-4">
          <h2 className="text-xl font-bold tracking-tight text-text-charcoal dark:text-text-offwhite font-heading flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-green-light dark:text-primary-green-dark" />
            Analyze a Molecule
          </h2>
          <p className="text-xs text-sage-gray-light dark:text-sage-gray-dark">
            Enter molecular details to run a pre-screening Freedom-to-Operate scan.
          </p>
        </div>

        {/* SMILES input */}
        <div className="flex flex-col gap-2">
          <label htmlFor="smiles" className="text-xs font-bold text-text-charcoal dark:text-text-offwhite tracking-wide flex items-center gap-1">
            Molecule Structure (SMILES) <span className="text-primary-green-light dark:text-primary-green-dark font-extrabold">*</span>
          </label>
          <textarea
            id="smiles"
            className="w-full font-mono text-xs p-4 rounded-xl border border-sage-gray-light/15 bg-white/50 focus:bg-white focus:ring-2 focus:ring-primary-green-light/30 focus:border-primary-green-light focus:shadow-[0_0_15px_rgba(21,128,61,0.15)] text-text-charcoal placeholder-sage-gray-light/50 outline-none transition-all duration-300 resize-y"
            value={smiles}
            onChange={(e) => { setSmiles(e.target.value); setError(''); }}
            placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
            rows={3}
            required
          />
        </div>

        {/* Target and Indication Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <label htmlFor="target" className="text-xs font-bold text-text-charcoal dark:text-text-offwhite tracking-wide flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-sage-gray-light dark:text-sage-gray-dark" />
              Target Protein (Optional)
            </label>
            <input
              id="target"
              type="text"
              className="w-full text-xs px-4 py-3 rounded-xl border border-sage-gray-light/15 bg-white/50 focus:bg-white focus:ring-2 focus:ring-primary-green-light/30 focus:border-primary-green-light focus:shadow-[0_0_15px_rgba(21,128,61,0.15)] text-text-charcoal placeholder-sage-gray-light/50 outline-none transition-all duration-300"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="e.g. COX-2, EGFR"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label htmlFor="disease" className="text-xs font-bold text-text-charcoal dark:text-text-offwhite tracking-wide flex items-center gap-1">
              <HeartPulse className="w-3.5 h-3.5 text-sage-gray-light dark:text-sage-gray-dark" />
              Indication (Optional)
            </label>
            <input
              id="disease"
              type="text"
              className="w-full text-xs px-4 py-3 rounded-xl border border-sage-gray-light/15 bg-white/50 focus:bg-white focus:ring-2 focus:ring-primary-green-light/30 focus:border-primary-green-light focus:shadow-[0_0_15px_rgba(21,128,61,0.15)] text-text-charcoal placeholder-sage-gray-light/50 outline-none transition-all duration-300"
              value={disease}
              onChange={(e) => setDisease(e.target.value)}
              placeholder="e.g. Rheumatoid Arthritis"
            />
          </div>
        </div>

        {/* Quick Fill Pills */}
        <div className="flex flex-wrap items-center gap-2 text-xs py-1">
          <span className="text-sage-gray-light dark:text-sage-gray-dark font-medium mr-1 flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5" />
            Quick fill:
          </span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex.label}
              type="button"
              className="px-3 py-1.5 text-[11px] font-medium rounded-lg border border-sage-gray-light/15 bg-white/60 shadow-sm hover:bg-primary-green-light hover:border-primary-green-light hover:text-white hover:shadow-md text-sage-gray-light cursor-pointer transition-all duration-300 active:scale-95"
              onClick={() => fillExample(ex)}
            >
              {ex.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-3 text-[11px] font-semibold text-rose-500 dark:text-rose-400 bg-rose-500/10 dark:bg-rose-500/15 border border-rose-500/20 rounded-xl flex items-center gap-2">
            <span>⚠️</span>
            {error}
          </div>
        )}

        <button type="submit" className="btn-primary w-full mt-2 select-none">
          Run FTO Analysis
        </button>
      </form>
    </div>
  );
}
