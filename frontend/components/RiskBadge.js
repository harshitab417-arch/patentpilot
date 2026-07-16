'use client';

import { AlertTriangle, ShieldCheck, Search } from 'lucide-react';

export default function RiskBadge({ level }) {
  const config = {
    'High Patent Risk': { className: 'badge-high', icon: AlertTriangle },
    'Requires Expert Review': { className: 'badge-medium', icon: Search },
    'Low Patent Risk': { className: 'badge-low', icon: ShieldCheck },
    High: { className: 'badge-high', icon: AlertTriangle },
    Medium: { className: 'badge-medium', icon: Search },
    Low: { className: 'badge-low', icon: ShieldCheck },
  };

  const current = config[level] || config['Requires Expert Review'];
  const Icon = current.icon;

  return (
    <span className={`risk-badge ${current.className}`}>
      <Icon className="w-3.5 h-3.5" />
      <span>{level}</span>
    </span>
  );
}
