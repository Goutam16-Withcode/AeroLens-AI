import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SatQuery AI — Autonomous Multispectral Agentic VLM // Next.js + FastAPI Cockpit',
  description: 'SatQuery AI is an autonomous multispectral agentic vision-language model cockpit for satellite observation, spectral band math, and bi-temporal change detection.',
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
      <body>{children}</body>
    </html>
  );
}
