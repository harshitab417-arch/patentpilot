import { Inter, JetBrains_Mono, Plus_Jakarta_Sans } from 'next/font/google';
import Navbar from '@/components/Navbar';
import AnimatedBackground from '@/components/AnimatedBackground';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-heading',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata = {
  title: 'PatentPilot — AI-Assisted FTO Analysis',
  description:
    'Accelerate freedom-to-operate analysis with AI-powered patent search, molecular similarity matching, and automated risk assessment.',
};

export default function RootLayout({ children }) {
  return (
    <html 
      lang="en" 
      className={`dark ${inter.variable} ${plusJakartaSans.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body className="antialiased">
        <AnimatedBackground />
        <Navbar />
        <main className="main-container relative z-10">{children}</main>
      </body>
    </html>
  );
}
