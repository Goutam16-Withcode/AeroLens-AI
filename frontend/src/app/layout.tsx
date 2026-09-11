import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SatQuery AI — Autonomous Orbital Vision-Language Intelligence',
  description: 'Next-generation geospatial foundation model & agentic VLM for multispectral satellite observation, bitemporal change detection, and SAR fusion.',
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
