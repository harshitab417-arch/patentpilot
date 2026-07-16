'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Dna, Clock, Sparkles } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="fixed top-4 left-1/2 -translate-x-1/2 w-[90%] max-w-5xl z-50 rounded-2xl backdrop-blur-xl border border-sage-gray-light/10 dark:border-sage-gray-dark/10 bg-card-mint-light/80 dark:bg-card-mint-dark/80 shadow-[0_8px_32px_rgba(4,18,12,0.05)] dark:shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
      <div className="flex items-center justify-between h-14 px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-green-light/10 dark:bg-primary-green-dark/10 border border-primary-green-light/20 dark:border-primary-green-dark/20 text-primary-green-light dark:text-primary-green-dark shadow-inner shadow-glow-green/10 group-hover:scale-105 active:scale-95 transition-all duration-200">
            <Dna className="w-5 h-5 animate-pulse-glow" />
          </div>
          <span className="font-extrabold text-base tracking-tight bg-gradient-to-r from-primary-green-light to-emerald-600 dark:from-primary-green-dark to-glow-green bg-clip-text text-transparent">
            PatentPilot
          </span>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-2">
          <Link
            href="/"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all duration-200 ${
              pathname === '/'
                ? 'bg-primary-green-light/8 dark:bg-primary-green-dark/8 text-primary-green-light dark:text-primary-green-dark border border-primary-green-light/15 dark:border-primary-green-dark/15'
                : 'text-sage-gray-light dark:text-sage-gray-dark hover:text-text-charcoal dark:hover:text-text-offwhite hover:bg-sage-gray-light/5 dark:hover:bg-sage-gray-dark/5 border border-transparent'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Analyze
          </Link>
          <Link
            href="/history"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all duration-200 ${
              pathname === '/history'
                ? 'bg-primary-green-light/8 dark:bg-primary-green-dark/8 text-primary-green-light dark:text-primary-green-dark border border-primary-green-light/15 dark:border-primary-green-dark/15'
                : 'text-sage-gray-light dark:text-sage-gray-dark hover:text-text-charcoal dark:hover:text-text-offwhite hover:bg-sage-gray-light/5 dark:hover:bg-sage-gray-dark/5 border border-transparent'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            History
          </Link>
          
        </nav>
      </div>
    </header>
  );
}
