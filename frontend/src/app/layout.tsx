import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';

export const metadata: Metadata = {
  title: 'AeroLens AI — Autonomous Orbital Earth Observation Cockpit',
  description: 'AeroLens AI is an autonomous orbital Earth observation cockpit for satellite vision-language analysis, spectral band math, and bi-temporal change detection.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {/* AuthProvider stays global (cheap, needed for the landing page's nav
            to know whether to say "Launch Console" vs "Sign In"), but the
            hard AuthGate now lives only in app/cockpit/layout.tsx — the
            landing page itself is public. */}
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}