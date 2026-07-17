'use client';

import { useEffect, useState } from 'react';

export default function AnimatedBackground() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      {/* ─── Ambient Glow Blobs ─────────────────────────────────── */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-[100%] bg-gradient-to-br from-emerald-400/15 to-teal-400/5 blur-[120px] animate-[spin_40s_linear_infinite]" />
      <div className="absolute bottom-[-10%] right-[-20%] w-[55%] h-[55%] rounded-[100%] bg-gradient-to-bl from-glow-green/15 to-emerald-300/5 blur-[120px] animate-[spin_30s_linear_infinite_reverse]" />
      <div className="absolute top-[20%] right-[10%] w-[40%] h-[40%] rounded-full bg-emerald-300/10 blur-[100px] animate-pulse-glow" />

      {/* ─── Fine Grid Overlay ─────────────────────────────────────── */}
      <div 
        className="absolute inset-0 opacity-[0.03] dark:opacity-[0.04]"
        style={{
          backgroundImage: `
            linear-gradient(to right, var(--color-primary-green-light) 1px, transparent 1px),
            linear-gradient(to bottom, var(--color-primary-green-light) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
        }}
      />

      {/* ─── Soft Mesh Dot Grid ───────────────────────────────────── */}
      <div 
        className="absolute inset-0 opacity-[0.08] dark:opacity-[0.1]"
        style={{
          backgroundImage: `radial-gradient(var(--color-primary-green-light) 1px, transparent 1px)`,
          backgroundSize: '24px 24px',
        }}
      />

      {/* ─── Drifting Particles ────────────────────────────────────── */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(12)].map((_, i) => {
          const size = Math.random() * 4 + 2;
          const left = Math.random() * 100;
          const top = Math.random() * 100;
          const duration = Math.random() * 20 + 20;
          const delay = Math.random() * -20;
          return (
            <div
              key={i}
              className="absolute rounded-full bg-glow-green/15 dark:bg-glow-green/25"
              style={{
                width: `${size}px`,
                height: `${size}px`,
                left: `${left}%`,
                top: `${top}%`,
                animation: `float ${duration}s ease-in-out infinite`,
                animationDelay: `${delay}s`,
                filter: 'blur(0.5px)',
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
