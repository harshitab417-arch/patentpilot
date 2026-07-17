'use client';

import { useEffect, useState } from 'react';

const SYMBOLS = ['+', '○', '×', '∆'];

export default function AnimatedBackground() {
  const [mounted, setMounted] = useState(false);
  const [geometry, setGeometry] = useState([]);

  useEffect(() => {
    setMounted(true);
    
    // Generate random micro-geometry
    const geom = Array.from({ length: 15 }).map(() => ({
      id: Math.random().toString(36).substr(2, 9),
      symbol: SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
      left: Math.random() * 100,
      top: Math.random() * 100,
      size: Math.random() * 8 + 8,
      duration: Math.random() * 30 + 40,
      delay: Math.random() * -30,
    }));
    setGeometry(geom);
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-[#F8FAFC]">
      
      {/* ─── Liquid Aura Mesh Gradients ─────────────────────────── */}
      <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] rounded-full bg-emerald-400/15 blur-[140px] animate-[spin_60s_linear_infinite]" />
      <div className="absolute bottom-[-10%] right-[-20%] w-[60%] h-[80%] rounded-full bg-sky-400/10 blur-[130px] animate-[spin_50s_linear_infinite_reverse]" />
      <div className="absolute top-[20%] right-[10%] w-[50%] h-[50%] rounded-full bg-teal-300/10 blur-[120px] animate-pulse-glow" />
      <div className="absolute bottom-[10%] left-[20%] w-[40%] h-[40%] rounded-full bg-primary-green-light/10 blur-[150px] animate-[spin_40s_linear_infinite]" />

      {/* ─── SVG Honeycomb / Hex Grid ────────────────────────────── */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.06]">
        <defs>
          <pattern id="hex-grid" width="40" height="69.282" patternUnits="userSpaceOnUse">
            <path 
              d="M 40 17.3205 L 20 28.8675 L 0 17.3205 L 0 -5.7735 L 20 -17.3205 L 40 -5.7735 Z M 0 51.9615 L 20 63.5085 L 40 51.9615 M 20 63.5085 L 20 86.6025" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="1.5" 
              className="text-primary-green-light"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#hex-grid)" />
      </svg>

      {/* ─── Floating Micro-Geometry ─────────────────────────────── */}
      <div className="absolute inset-0 overflow-hidden">
        {geometry.map((geo) => (
          <div
            key={geo.id}
            className="absolute flex items-center justify-center font-mono font-bold text-primary-green-light/20"
            style={{
              fontSize: `${geo.size}px`,
              left: `${geo.left}%`,
              top: `${geo.top}%`,
              animation: `float ${geo.duration}s ease-in-out infinite`,
              animationDelay: `${geo.delay}s`,
            }}
          >
            {geo.symbol}
          </div>
        ))}
      </div>
      
      {/* ─── Soft Vignette Lighting ─────────────────────────────── */}
      <div className="absolute inset-0 shadow-[inset_0_0_150px_rgba(255,255,255,0.8)]" />
    </div>
  );
}
