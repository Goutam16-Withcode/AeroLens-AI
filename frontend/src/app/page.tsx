'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

const DEMO_VIDEO_URL = process.env.NEXT_PUBLIC_DEMO_VIDEO_URL;

/* ── YouTube helper ────────────────────────────────────────────── */
function toYouTubeEmbedUrl(raw: string | undefined): string | null {
  if (!raw) return null;
  try {
    const url = new URL(raw);
    const host = url.hostname.replace(/^www\./, '');
    let videoId = '';

    if (host === 'youtu.be') {
      videoId = url.pathname.slice(1);
    } else if (host === 'youtube.com' || host === 'm.youtube.com') {
      if (url.pathname === '/watch') videoId = url.searchParams.get('v') || '';
      else if (url.pathname.startsWith('/embed/')) videoId = url.pathname.split('/embed/')[1] || '';
      else if (url.pathname.startsWith('/shorts/')) videoId = url.pathname.split('/shorts/')[1] || '';
    }

    videoId = videoId.split(/[?&]/)[0];
    return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
  } catch {
    return null;
  }
}

/* ── Data ──────────────────────────────────────────────────────── */
const CAPABILITIES: { title: string; body: string }[] = [
  { title: 'Scene intelligence & VQA', body: 'Ask a plain-language question about a single frame and get a grounded answer, cited against the pixels that support it — not a generic caption.' },
  { title: 'Target detection & grounding', body: 'Describe what you\u2019re looking for — aircraft, vessels, structures — and get bounding boxes with confidence, not a list of guesses.' },
  { title: 'Bi-temporal change detection', body: 'Feed in two passes of the same site and isolate what actually moved: new construction, flood extent, burn scars, fleet movement.' },
  { title: 'Optical + SAR fusion', body: 'Cross-reference optical imagery against SAR returns from the same site for confirmation that holds up through cloud cover and at night.' },
  { title: 'Persistent mission history', body: 'Every pass is saved to your account under Firebase Auth. Close the tab, come back tomorrow, and pick the analysis up exactly where you left it.' },
  { title: 'Exportable intelligence briefings', body: 'Turn any pass into a formatted PDF dossier — evidence imagery, detection tables, and telemetry — ready to hand off, not a browser screenshot.' },
];

const STEPS: { title: string; body: string }[] = [
  { title: 'Attach the pass', body: 'Upload one or two satellite frames — optical, SAR, or a mix of both.' },
  { title: 'State the objective', body: 'Type a question in your own words, or start from a mission preset.' },
  { title: 'Autonomous analysis', body: 'The VLM core reasons over the imagery and returns a cited, evidence-backed answer.' },
  { title: 'Review or export', body: 'Inspect the decoded evidence matrix and detections, or export the whole pass as a briefing.' },
];

const PIPELINE_STAGES: { title: string; body: string }[] = [
  { title: 'User input', body: 'Natural-language query plus a single image, an optical+SAR pair, or a bi-temporal pair.' },
  { title: 'Preprocessing', body: 'Data validation, radiometric correction, co-registration & alignment, cropping/ROI extraction, normalization & resampling.' },
  { title: 'Agentic controller', body: 'Understands the query, classifies the task, checks input compatibility, plans model/tool selection, and configures parameters.' },
  { title: 'Specialist model registry', body: 'VQA, captioning, grounding, change detection, change-VQA, and optical–SAR fusion models — invoked only as the task requires.' },
  { title: 'Result fusion & reasoning', body: 'Aggregates specialist outputs, applies cross-model reasoning, estimates confidence, and collects supporting evidence.' },
  { title: 'Output generation', body: 'Textual answer, visual evidence, change map, key findings, confidence score, execution summary, downloadable report.' },
  { title: 'Audit & traceability', body: 'Every response logs the selected task, models/tools used, parameters, execution time, and inputs — nothing is a black box.' },
  { title: 'Feedback loop', body: 'User feedback and usage logs feed back into model improvement and continuous accuracy/robustness gains.' },
];

const TECH_STACK: { category: string; items: string }[] = [
  { category: 'Frontend', items: 'Next.js · TypeScript · Tailwind CSS · Redux / Zustand' },
  { category: 'Backend', items: 'FastAPI (AI backend & API) · Python (Django) · Node.js (Express)' },
  { category: 'Machine Learning & AI', items: 'PyTorch · Hugging Face Transformers · Qwen2.5-VL / LLaVA · LLM orchestration' },
  { category: 'Database & Storage', items: 'PostgreSQL + PostGIS · Firebase Firestore · Cloudinary · AWS / local storage' },
  { category: 'Remote Sensing & GIS', items: 'GDAL / Rasterio · GeoPandas · Sentinel / Copernicus APIs' },
  { category: 'Deployment & Hardware', items: 'Docker · GPU-accelerated inference & fine-tuning' },
];

const RISKS: { risk: string; mitigation: string }[] = [
  { risk: 'Multimodal data complexity — optical and SAR images have different characteristics and formats.', mitigation: 'Modality-specific preprocessing and standardized input pipelines.' },
  { risk: 'Model selection & integration — different tasks require different specialist models and configurations.', mitigation: 'A predefined model registry with agent-based task selection.' },
  { risk: 'Image alignment & preprocessing — multi-temporal and optical–SAR pairs need accurate co-registration.', mitigation: 'Automated co-registration, normalization, resampling, and quality checks.' },
  { risk: 'AI hallucination & reliability — VLM/LLM answers may contain unsupported claims.', mitigation: 'Evidence-grounded outputs, confidence scores, and specialist-model cross-checks.' },
  { risk: 'Computational requirements — VLMs and multiple specialist models need real GPU resources.', mitigation: 'GPU-enabled inference, optimized models, and modular execution.' },
  { risk: 'Satellite data availability — cloud cover, missing data, or unsuitable acquisition dates.', mitigation: 'Metadata-based filtering for location, date, cloud cover, and image quality.' },
];

type Support = 'full' | 'partial' | 'none';
const COMPARISON: { feature: string; support: Support[] }[] = [
  { feature: 'Natural-language query', support: ['full', 'partial', 'none', 'none', 'none'] },
  { feature: 'AI agent / auto model selection', support: ['full', 'partial', 'none', 'partial', 'none'] },
  { feature: 'Multi-model AI orchestration', support: ['full', 'partial', 'partial', 'partial', 'partial'] },
  { feature: 'Optical image analysis', support: ['full', 'full', 'full', 'full', 'full'] },
  { feature: 'SAR image analysis', support: ['full', 'full', 'full', 'full', 'full'] },
  { feature: 'Optical + SAR analysis', support: ['full', 'partial', 'partial', 'partial', 'partial'] },
  { feature: 'Bi-temporal change analysis', support: ['full', 'full', 'full', 'full', 'full'] },
  { feature: 'VQA & visual grounding', support: ['full', 'none', 'none', 'none', 'none'] },
  { feature: 'AI scene description', support: ['full', 'partial', 'none', 'partial', 'none'] },
  { feature: 'Evidence + confidence output', support: ['full', 'partial', 'partial', 'partial', 'partial'] },
];
const COMPARISON_COLUMNS = ['SatQuery AI', 'Google Earth Engine', 'QGIS', 'ENVI', 'ESA SNAP'];

const IMPACT_AREAS: { title: string; body: string }[] = [
  { title: 'Social', body: 'Makes satellite analysis accessible to non-experts and enables faster, better-informed decision-making.' },
  { title: 'Economic', body: 'Reduces analysis time and dependency on specialized expertise; optimizes resources in agriculture, infrastructure, and urban planning.' },
  { title: 'Environmental', body: 'Supports monitoring of forests, water bodies, and land-use change; enables early detection of environmental degradation.' },
  { title: 'Disaster management', body: 'Supports rapid satellite-based damage assessment and faster emergency response and planning.' },
];

const WHO_BENEFITS: { title: string; body: string }[] = [
  { title: 'Researchers & students', body: 'Simplifies exploration and interpretation of geospatial data.' },
  { title: 'Disaster management teams', body: 'Enables rapid change detection for timely response planning.' },
  { title: 'Agriculture & environment', body: 'Supports monitoring of land, vegetation, and environmental change.' },
  { title: 'Government & planners', body: 'Provides traceable, evidence-backed insight for data-driven policy decisions.' },
];

const REVENUE_MODEL: { title: string; body: string }[] = [
  { title: 'Freemium', body: 'Basic analysis free; advanced features paid.' },
  { title: 'Institutional licensing', body: 'Subscription plans for organizations and government agencies.' },
  { title: 'API-as-a-service', body: 'Charge for large-scale automated satellite analysis.' },
  { title: 'Custom solutions', body: 'Paid analytics and domain-specific deployments.' },
];

const REFERENCES: { title: string; body: string; href: string }[] = [
  { title: 'BigEarthNet', body: 'Remote-sensing dataset used for VLM adaptation and image understanding.', href: 'https://bigearth.net/' },
  { title: 'VRSBench', body: 'Benchmark for remote-sensing VQA, image captioning, and visual grounding.', href: 'https://github.com/lx709/VRSBench' },
  { title: 'RSVQA', body: 'Dataset and benchmark for visual question answering on remote-sensing images.', href: 'https://rsvqa.sylvainlobry.com/' },
  { title: 'CDVQA', body: 'Dataset for bi-temporal change detection and change-oriented VQA.', href: 'https://github.com/Chen-Yang-Liu/CDVQA' },
  { title: 'Copernicus Data Space Ecosystem', body: 'Satellite data access and API-based imagery retrieval by location and time.', href: 'https://dataspace.copernicus.eu/' },
  { title: 'Hugging Face Transformers', body: 'Open-source VLM/LLM models and tooling for model adaptation.', href: 'https://huggingface.co/docs/transformers/' },
  { title: 'GDAL', body: 'Geospatial raster processing and satellite-image preprocessing.', href: 'https://gdal.org/' },
  { title: 'Rasterio', body: 'Python interface to GDAL for reading and writing geospatial raster data.', href: 'https://rasterio.readthedocs.io/' },
];

const SUPPORT_STYLE: Record<Support, { glyph: string; color: string; bg: string }> = {
  full: { glyph: '✓', color: 'var(--accent-emerald)', bg: 'var(--accent-emerald-subtle)' },
  partial: { glyph: '△', color: 'var(--accent-amber)', bg: 'var(--accent-amber-subtle)' },
  none: { glyph: '—', color: 'var(--accent-coral)', bg: 'var(--accent-coral-subtle)' },
};

const LABEL_STYLE: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '10.5px',
  fontWeight: 700,
  letterSpacing: '0.08em',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
};

/* ── Hooks ─────────────────────────────────────────────────────── */

/**
 * Observe an element and return `true` once it has entered the viewport.
 * Fires once by default (`once = true`).
 */
function useInView<T extends HTMLElement>(options?: { threshold?: number; once?: boolean }) {
  const { threshold = 0.15, once = true } = options ?? {};
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === 'undefined') {
      setInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setInView(true);
            if (once) observer.unobserve(entry.target);
          } else if (!once) {
            setInView(false);
          }
        });
      },
      { threshold, rootMargin: '0px 0px -60px 0px' },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [threshold, once]);

  return { ref, inView };
}

/** Animate a number from 0 → target once `active` becomes true. */
function useCountUp(target: number, active: boolean, duration = 1400) {
  const [value, setValue] = useState(0);
  const frameRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) return;
    startRef.current = null;

    const tick = (now: number) => {
      if (startRef.current === null) startRef.current = now;
      const progress = Math.min((now - startRef.current) / duration, 1);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) frameRef.current = requestAnimationFrame(tick);
    };

    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    };
  }, [target, active, duration]);

  return value;
}

/** Mouse position tracker — used to drive card spotlight effects. */
function useMouseSpot<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const onMove = (e: MouseEvent) => {
      const rect = node.getBoundingClientRect();
      node.style.setProperty('--mx', `${e.clientX - rect.left}px`);
      node.style.setProperty('--my', `${e.clientY - rect.top}px`);
    };

    node.addEventListener('mousemove', onMove);
    return () => node.removeEventListener('mousemove', onMove);
  }, []);

  return ref;
}

/* ── Reusable components ──────────────────────────────────────── */

const Reveal: React.FC<{
  children: React.ReactNode;
  delay?: number;
  y?: number;
  className?: string;
  as?: 'div' | 'section';
}> = ({ children, delay = 0, y = 24, className, as = 'div' }) => {
  const { ref, inView } = useInView<HTMLDivElement>();
  const style: React.CSSProperties = {
    opacity: inView ? 1 : 0,
    transform: inView ? 'translateY(0)' : `translateY(${y}px)`,
    transition: `opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1) ${delay}ms, transform 0.7s cubic-bezier(0.22, 1, 0.36, 1) ${delay}ms`,
    willChange: 'opacity, transform',
  };
  const Tag = as;
  return (
    <Tag ref={ref as never} style={style} className={className}>
      {children}
    </Tag>
  );
};

const AnimatedProgressRing: React.FC<{
  value: number;
  size?: number;
  stroke?: number;
  color?: string;
  suffix?: string;
  delay?: number;
}> = ({ value, size = 88, stroke = 7, color = 'var(--accent-amber)', suffix = '%', delay = 0 }) => {
  const { ref, inView } = useInView<HTMLDivElement>({ threshold: 0.4 });
  const count = useCountUp(value, inView, 1500);
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - (inView ? value : 0) / 100);

  return (
    <div ref={ref} style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: 'rotate(-90deg)', display: 'block' }}
        aria-hidden="true"
      >
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--border-subtle)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: `stroke-dashoffset 1.5s cubic-bezier(0.22, 1, 0.36, 1) ${delay}ms`,
            filter: `drop-shadow(0 0 6px ${color}55)`,
          }}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'var(--font-hud)',
          fontWeight: 700,
          color: 'var(--text-pure)',
          fontSize: size > 80 ? '19px' : '14px',
          letterSpacing: '-0.01em',
        }}
      >
        {count}
        <span style={{ fontSize: size > 80 ? '13px' : '11px', marginLeft: '1px', color: 'var(--accent-amber)' }}>
          {suffix}
        </span>
      </div>
    </div>
  );
};

const SupportBadge: React.FC<{ level: Support }> = ({ level }) => {
  const s = SUPPORT_STYLE[level];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '22px',
        height: '22px',
        borderRadius: '50%',
        background: s.bg,
        color: s.color,
        fontWeight: 800,
        fontSize: '12px',
        fontFamily: 'var(--font-mono)',
      }}
    >
      {s.glyph}
    </span>
  );
};

const SectionHeading: React.FC<{ children: React.ReactNode; description?: string }> = ({
  children,
  description,
}) => (
  <Reveal>
    <div style={{ marginBottom: '24px' }}>
      <h2
        style={{
          fontFamily: 'var(--font-hud)',
          fontSize: '13px',
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'var(--text-muted)',
          marginBottom: description ? '8px' : 0,
        }}
      >
        {children}
      </h2>
      {description && (
        <p
          style={{
            fontSize: '14px',
            lineHeight: 1.55,
            color: 'var(--text-secondary)',
            margin: 0,
            maxWidth: '720px',
          }}
        >
          {description}
        </p>
      )}
    </div>
  </Reveal>
);

/** Card with cursor-following amber spotlight. */
const SpotlightCard: React.FC<{
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}> = ({ children, className = '', style }) => {
  const ref = useMouseSpot<HTMLDivElement>();
  return (
    <div ref={ref} className={`panel-card spotlight-card ${className}`} style={style}>
      {children}
    </div>
  );
};

/* ── Page ──────────────────────────────────────────────────────── */

export default function LandingPage() {
  const { user, loading } = useAuth();
  const demoEmbedUrl = toYouTubeEmbedUrl(DEMO_VIDEO_URL);

  /* Hero parallax — subtle vertical offset on scroll */
  const heroRef = useRef<HTMLElement | null>(null);
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const heroOffset = Math.min(scrollY * 0.12, 40);

  return (
    <div className="landing-page" style={{ position: 'relative', minHeight: '100vh' }}>
      <div className="space-canvas" />
      <div className="grid-overlay animated-grid" />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: '1180px', margin: '0 auto', padding: '20px 24px 0' }}>
        {/* ── Nav ─────────────────────────────────────────────────── */}
        <nav
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 4px',
            marginBottom: '8px',
          }}
        >
          <Link
            href="/"
            aria-label="AeroLens AI home"
            style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none' }}
          >
            <span className="logo-mark" aria-hidden="true">
              <span className="logo-orbit logo-orbit-outer" />
              <span className="logo-orbit logo-orbit-inner" />
              <span className="logo-orbit logo-orbit-sweep" />
              <span className="logo-core">🛰️</span>
            </span>
            <span
              style={{
                fontFamily: 'var(--font-hud)',
                fontSize: '17px',
                fontWeight: 700,
                color: 'var(--text-pure)',
              }}
            >
              AERO<span style={{ color: 'var(--accent-amber)' }}>LENS</span> AI
            </span>
          </Link>

          <Link
            href="/cockpit"
            className="nav-btn"
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '12px',
              fontWeight: 700,
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              padding: '8px 16px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-light)',
            }}
          >
            {!loading && user ? 'Open console →' : 'Sign in'}
          </Link>
        </nav>

        {/* ── Hackathon strip ─────────────────────────────────────── */}
        <div
          className="hackathon-strip"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            flexWrap: 'wrap',
            padding: '8px 12px',
            marginBottom: '4px',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            fontFamily: 'var(--font-mono)',
            fontSize: '10.5px',
            color: 'var(--text-muted)',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <span style={{ fontWeight: 700, color: 'var(--text-secondary)' }}>SMART INDIA HACKATHON 2026</span>
          <span>·</span>
          <span>PS ID SIH26167</span>
          <span>·</span>
          <span>THEME: SPACE TECHNOLOGY</span>
          <span>·</span>
          <span>TEAM ORB8X_26 (ID 133279)</span>
        </div>

        {/* ── Section nav ─────────────────────────────────────────── */}
        <div
          style={{
            display: 'flex',
            gap: '6px',
            overflowX: 'auto',
            padding: '10px 4px',
            marginBottom: '8px',
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            fontWeight: 700,
            whiteSpace: 'nowrap',
          }}
        >
          {[
            ['#innovation', 'Innovation'],
            ['#capabilities', 'Capabilities'],
            ['#how-it-works', 'How it works'],
            ['#architecture', 'Architecture'],
            ['#tech-stack', 'Tech stack'],
            ['#feasibility', 'Feasibility'],
            ['#comparison', 'Comparison'],
            ['#impact', 'Impact'],
            ['#references', 'References'],
          ].map(([href, label]) => (
            <a key={href} href={href} className="nav-link">
              {label}
            </a>
          ))}
        </div>

        {/* ── Hero ────────────────────────────────────────────────── */}
        <section
          ref={heroRef}
          className="landing-hero-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: '1.05fr 0.95fr',
            gap: '48px',
            alignItems: 'center',
            padding: '56px 4px 40px',
          }}
        >
          <div style={{ transform: `translateY(${-heroOffset}px)`, transition: 'transform 0.05s linear' }}>
            <div
              style={{
                display: 'inline-block',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--accent-amber)',
                background: 'var(--accent-amber-subtle)',
                border: '1px solid var(--accent-amber-border)',
                borderRadius: '20px',
                padding: '4px 12px',
                marginBottom: '20px',
              }}
              className="hero-eyebrow"
            >
              <span className="pulse-dot" style={{ marginRight: '6px' }} />
              Autonomous VLM Engine · Zero-Latency Neural Core
            </div>

            <h1
              className="hero-title"
              style={{
                fontFamily: 'var(--font-hud)',
                fontWeight: 700,
                fontSize: 'clamp(32px, 4vw, 46px)',
                lineHeight: 1.12,
                color: 'var(--text-pure)',
                letterSpacing: '-0.01em',
                marginBottom: '20px',
                maxWidth: '560px',
              }}
            >
              Ask a satellite pass{' '}
              <span className="hero-underline">
                anything
                <svg viewBox="0 0 300 12" preserveAspectRatio="none" aria-hidden="true">
                  <path d="M2 8 Q 75 2, 150 6 T 298 5" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                </svg>
              </span>
              .
            </h1>

            <p
              style={{
                fontSize: '16px',
                lineHeight: 1.65,
                color: 'var(--text-secondary)',
                maxWidth: '480px',
                marginBottom: '30px',
              }}
            >
              AeroLens AI reads optical and SAR imagery the way a photo interpretation analyst would —
              spotting change, grounding targets, and writing up the finding — starting from one query
              and a couple of frames.
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '18px', flexWrap: 'wrap' }}>
              <Link
                href="/cockpit"
                className="btn-primary"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '14px 26px',
                  background: 'var(--accent-amber)',
                  border: '1px solid #a3561f',
                  borderRadius: 'var(--radius-md)',
                  color: '#ffffff',
                  fontFamily: 'var(--font-hud)',
                  fontSize: '13.5px',
                  fontWeight: 700,
                  letterSpacing: '0.04em',
                  textDecoration: 'none',
                  boxShadow: '0 4px 14px rgba(194, 109, 46, 0.28)',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                <span className="btn-shine" aria-hidden="true" />
                Launch mission console →
              </Link>
              <a
                href="#innovation"
                className="hero-secondary-link"
                style={{
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  textDecoration: 'none',
                }}
              >
                See what&apos;s new ↓
              </a>
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '34px', flexWrap: 'wrap' }}>
              {['OPTICAL + SAR FUSION', 'SUB-METER GROUNDING', 'BI-TEMPORAL DELTA', 'PERSISTENT HISTORY'].map(
                (tag, i) => (
                  <span
                    key={tag}
                    className="pill-badge tag-pop"
                    style={{ animationDelay: `${400 + i * 100}ms` }}
                  >
                    {tag}
                  </span>
                ),
              )}
            </div>
          </div>

          {/* Hero visual */}
          <div className="panel-card hero-card" style={{ padding: '18px', transform: `translateY(${heroOffset * 0.6}px)` }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '14px',
              }}
            >
              <span className="panel-title">
                <span>🛰️</span> LIVE PASS · SQ-EO-2026
              </span>
              <span className="pill-badge active" style={{ fontSize: '9.5px' }}>
                <span className="pulse-dot" /> ANALYZING
              </span>
            </div>

            <div
              style={{
                marginLeft: 'auto',
                maxWidth: '92%',
                background: 'var(--accent-amber-subtle)',
                border: '1px solid var(--accent-amber-border)',
                borderRadius: 'var(--radius-md)',
                padding: '9px 12px',
                fontSize: '12px',
                color: 'var(--text-main)',
                marginBottom: '12px',
              }}
            >
              &ldquo;Locate and highlight all parked airplanes with a bounding box.&rdquo;
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
              {[
                { label: 'OPTICAL', from: '#dbe8d0', to: '#8fae72' },
                { label: 'ATTENTION', from: '#f4d9b8', to: '#c26d2e' },
                { label: 'RETICLE', from: '#cfe3df', to: '#1b6a48' },
                { label: 'SAR', from: '#3a2622', to: '#be123c' },
              ].map((slot, i) => (
                <div
                  key={slot.label}
                  className="hero-tile"
                  style={{
                    borderRadius: 'var(--radius-sm)',
                    overflow: 'hidden',
                    border: '1px solid var(--border-subtle)',
                    animationDelay: `${i * 120}ms`,
                    position: 'relative',
                  }}
                >
                  <div style={{ height: '52px', background: `linear-gradient(135deg, ${slot.from}, ${slot.to})` }} />
                  <div className="hero-tile-scan" aria-hidden="true" />
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '8.5px',
                      fontWeight: 700,
                      color: 'var(--text-muted)',
                      padding: '4px 6px',
                    }}
                  >
                    {slot.label}
                  </div>
                </div>
              ))}
            </div>

            <div
              className="hero-answer"
              style={{
                borderLeft: '3px solid var(--accent-amber)',
                background: '#fff',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 12px',
                fontSize: '11.5px',
                lineHeight: 1.5,
                color: 'var(--text-main)',
              }}
            >
              Two wide-body aircraft identified on the NW/NE apron, nose-to-nose orientation confirmed
              against taxiway geometry.
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginTop: '10px',
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                color: 'var(--text-muted)',
              }}
            >
              <span>CONFIDENCE 96%</span>
              <span>LATENCY 28.9s</span>
            </div>
          </div>
        </section>

        {/* ── Uniqueness & Innovation ─────────────────────────────── */}
        <section id="innovation" style={{ padding: '48px 4px' }}>
          <SectionHeading description="An indigenous AI-powered satellite intelligence platform built for faster, smarter, and evidence-backed geospatial analysis.">
            Uniqueness &amp; Innovation in Our Solution
          </SectionHeading>

          <div
            className="innovation-metrics-grid"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '14px',
              marginBottom: '14px',
            }}
          >
            {/* Card 1 — Deployment + 85% */}
            <Reveal delay={0}>
              <SpotlightCard style={{ padding: '22px 20px', height: '100%' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '16px',
                  }}
                >
                  <span style={LABEL_STYLE}>Solution Status</span>
                  <span className="deployed-badge">
                    <span className="pulse-dot" />
                    DEPLOYED
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <AnimatedProgressRing value={85} size={88} stroke={7} color="var(--accent-amber)" />
                  <div>
                    <div
                      style={{
                        fontFamily: 'var(--font-hud)',
                        fontSize: '15px',
                        fontWeight: 700,
                        color: 'var(--text-pure)',
                        marginBottom: '4px',
                      }}
                    >
                      85% complete
                    </div>
                    <div style={{ fontSize: '12.5px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>
                      Already deployed and running live — you can use it today.
                    </div>
                  </div>
                </div>
              </SpotlightCard>
            </Reveal>

            {/* Card 2 — ML accuracy 95% */}
            <Reveal delay={120}>
              <SpotlightCard style={{ padding: '22px 20px', height: '100%' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '16px',
                  }}
                >
                  <span style={LABEL_STYLE}>ML Model Accuracy</span>
                  <span style={{ fontSize: '15px' }} aria-hidden="true">🎯</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <AnimatedProgressRing value={95} size={88} stroke={7} color="var(--accent-emerald)" delay={200} />
                  <div>
                    <div
                      style={{
                        fontFamily: 'var(--font-hud)',
                        fontSize: '15px',
                        fontWeight: 700,
                        color: 'var(--text-pure)',
                        marginBottom: '4px',
                      }}
                    >
                      95% accuracy
                    </div>
                    <div style={{ fontSize: '12.5px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>
                      Measured on our internal evaluation set.
                    </div>
                  </div>
                </div>
              </SpotlightCard>
            </Reveal>

            {/* Card 3 — Response time */}
            <Reveal delay={240}>
              <SpotlightCard style={{ padding: '22px 20px', height: '100%' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '16px',
                  }}
                >
                  <span style={LABEL_STYLE}>Response Time</span>
                  <span className="pill-badge active" style={{ fontSize: '9.5px' }}>
                    <span className="pulse-dot" /> LOW LATENCY
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div className="bolt-orb" aria-hidden="true">⚡</div>
                  <div>
                    <div
                      style={{
                        fontFamily: 'var(--font-hud)',
                        fontSize: '18px',
                        fontWeight: 700,
                        color: 'var(--text-pure)',
                        marginBottom: '4px',
                      }}
                    >
                      Milliseconds
                    </div>
                    <div style={{ fontSize: '12.5px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>
                      Fast, near-instant feedback on every query.
                    </div>
                  </div>
                </div>
              </SpotlightCard>
            </Reveal>
          </div>

          <div
            className="innovation-agent-grid"
            style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}
          >
            {/* AI Agent */}
            <Reveal delay={0}>
              <SpotlightCard style={{ padding: '24px 22px', height: '100%' }}>
                <div style={{ ...LABEL_STYLE, marginBottom: '14px' }}>Indigenous AI Innovation</div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                  <span className="brain-pulse" style={{ fontSize: '22px' }} aria-hidden="true">🧠</span>
                  <h3
                    style={{
                      fontFamily: 'var(--font-hud)',
                      fontSize: '18px',
                      fontWeight: 700,
                      color: 'var(--text-pure)',
                      letterSpacing: '-0.01em',
                      margin: 0,
                    }}
                  >
                    Our Own AI Agent
                  </h3>
                </div>

                <p
                  style={{
                    fontSize: '13.5px',
                    lineHeight: 1.65,
                    color: 'var(--text-secondary)',
                    margin: 0,
                    marginBottom: '16px',
                    maxWidth: '560px',
                  }}
                >
                  We built our own indigenous AI agent that intelligently coordinates satellite image
                  analysis tasks — planning execution, selecting the right specialist model for each
                  query, and grounding every answer in the evidence it was derived from.
                </p>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <span className="pill-badge tag-hover">Task planning</span>
                  <span className="pill-badge tag-hover">Model orchestration</span>
                  <span className="pill-badge tag-hover">Evidence grounding</span>
                </div>
              </SpotlightCard>
            </Reveal>

            {/* YouTube demo */}
            <Reveal delay={160}>
              <SpotlightCard style={{ padding: '22px 20px', height: '100%' }}>
                <div style={{ ...LABEL_STYLE, marginBottom: '10px' }}>Live Solution Demonstration</div>
                <h3
                  style={{
                    fontFamily: 'var(--font-hud)',
                    fontSize: '17px',
                    fontWeight: 700,
                    color: 'var(--text-pure)',
                    letterSpacing: '-0.01em',
                    margin: 0,
                    marginBottom: '14px',
                  }}
                >
                  Watch Our 3-Minute Demo
                </h3>

                {demoEmbedUrl ? (
                  <div className="video-frame">
                    <div className="video-frame-glow" aria-hidden="true" />
                    <div
                      style={{
                        position: 'relative',
                        width: '100%',
                        paddingBottom: '56.25%',
                        borderRadius: 'var(--radius-md)',
                        overflow: 'hidden',
                        border: '1px solid var(--border-subtle)',
                        background: '#000',
                        zIndex: 1,
                      }}
                    >
                      <iframe
                        src={demoEmbedUrl}
                        title="AeroLens AI — 3-Minute Solution Demo"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowFullScreen
                        loading="lazy"
                        referrerPolicy="strict-origin-when-cross-origin"
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          height: '100%',
                          border: 0,
                        }}
                      />
                    </div>
                  </div>
                ) : (
                  <div
                    className="video-placeholder"
                    style={{
                      width: '100%',
                      aspectRatio: '16 / 9',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      background: 'var(--bg-secondary)',
                      border: '1px dashed var(--border-subtle)',
                      borderRadius: 'var(--radius-md)',
                      padding: '20px',
                      color: 'var(--text-muted)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '12px',
                      letterSpacing: '0.04em',
                      textAlign: 'center',
                    }}
                  >
                    <span style={{ fontSize: '26px' }} aria-hidden="true">📹</span>
                    <span>Demo video coming soon.</span>
                  </div>
                )}
              </SpotlightCard>
            </Reveal>
          </div>
        </section>

        {/* ── Capabilities ────────────────────────────────────────── */}
        <section id="capabilities" style={{ padding: '48px 4px' }}>
          <SectionHeading description="Six core analysis tasks AeroLens AI performs on any satellite pass — from plain-language questions to evidence-backed briefings.">
            What it can do
          </SectionHeading>
          <div style={{ borderTop: '1px solid var(--border-subtle)' }}>
            {CAPABILITIES.map((cap, i) => (
              <Reveal key={cap.title} delay={i * 60}>
                <div
                  className="capability-row capability-hover"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '260px 1fr',
                    gap: '24px',
                    padding: '20px 0',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}
                >
                  <div
                    style={{
                      fontFamily: 'var(--font-sans)',
                      fontSize: '15.5px',
                      fontWeight: 700,
                      color: 'var(--text-pure)',
                    }}
                  >
                    {cap.title}
                  </div>
                  <div
                    style={{
                      fontSize: '13.5px',
                      lineHeight: 1.6,
                      color: 'var(--text-secondary)',
                      maxWidth: '640px',
                    }}
                  >
                    {cap.body}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── How it works ────────────────────────────────────────── */}
        <section id="how-it-works" style={{ padding: '48px 4px' }}>
          <SectionHeading description="From attaching a pass to exporting a briefing — four steps, no remote-sensing expertise required.">
            How a pass works
          </SectionHeading>
          <div className="steps-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            {STEPS.map((step, i) => (
              <Reveal key={step.title} delay={i * 120}>
                <SpotlightCard style={{ padding: '20px 18px', height: '100%' }}>
                  <div className="step-number">{String(i + 1).padStart(2, '0')}</div>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-pure)', marginBottom: '6px' }}>
                    {step.title}
                  </div>
                  <div style={{ fontSize: '12.5px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>
                    {step.body}
                  </div>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── System architecture ─────────────────────────────────── */}
        <section id="architecture" style={{ padding: '48px 4px' }}>
          <SectionHeading description="The eight-stage pipeline that powers every query — from raw imagery to a traceable, evidence-backed answer.">
            System architecture
          </SectionHeading>
          <div style={{ position: 'relative', paddingLeft: '28px' }}>
            <div
              className="pipeline-line"
              style={{
                position: 'absolute',
                left: '9px',
                top: '10px',
                bottom: '10px',
                width: '2px',
                background: 'var(--border-subtle)',
              }}
            />
            {PIPELINE_STAGES.map((stage, i) => (
              <Reveal key={stage.title} delay={i * 60}>
                <div style={{ position: 'relative', paddingBottom: i === PIPELINE_STAGES.length - 1 ? 0 : '22px' }}>
                  <div className="pipeline-dot" style={{ animationDelay: `${i * 150}ms` }}>
                    {i + 1}
                  </div>
                  <div style={{ fontSize: '14.5px', fontWeight: 700, color: 'var(--text-pure)', marginBottom: '3px' }}>
                    {stage.title}
                  </div>
                  <div
                    style={{
                      fontSize: '13px',
                      lineHeight: 1.55,
                      color: 'var(--text-secondary)',
                      maxWidth: '620px',
                    }}
                  >
                    {stage.body}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── Tech stack ──────────────────────────────────────────── */}
        <section id="tech-stack" style={{ padding: '48px 4px' }}>
          <SectionHeading description="The tools, frameworks, and platforms AeroLens AI is built on.">
            Built with
          </SectionHeading>
          <div className="tech-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
            {TECH_STACK.map((t, i) => (
              <Reveal key={t.category} delay={i * 80}>
                <SpotlightCard style={{ padding: '16px 18px', height: '100%' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-pure)', marginBottom: '6px' }}>
                    {t.category}
                  </div>
                  <div
                    style={{
                      fontSize: '12px',
                      lineHeight: 1.6,
                      color: 'var(--text-secondary)',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {t.items}
                  </div>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── Feasibility ─────────────────────────────────────────── */}
        <section id="feasibility" style={{ padding: '48px 4px' }}>
          <SectionHeading description="Six known challenges we've identified, and the engineering answer to each.">
            Challenges &amp; how we handle them
          </SectionHeading>
          <div style={{ borderTop: '1px solid var(--border-subtle)' }}>
            {RISKS.map((r, i) => (
              <Reveal key={r.risk} delay={i * 60}>
                <div
                  className="capability-row capability-hover"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '24px',
                    padding: '18px 0',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontSize: '13px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>{r.risk}</div>
                  <div
                    className="mitigation-cell"
                    style={{
                      fontSize: '13px',
                      lineHeight: 1.55,
                      color: 'var(--text-main)',
                      borderLeft: '2px solid var(--accent-emerald-border)',
                      paddingLeft: '14px',
                    }}
                  >
                    {r.mitigation}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── Comparison ──────────────────────────────────────────── */}
        <section id="comparison" style={{ padding: '48px 4px' }}>
          <SectionHeading description="How AeroLens AI stacks up against existing satellite-analysis tools.">
            How it compares
          </SectionHeading>
          <Reveal>
            <div className="panel-card comparison-card" style={{ padding: 0, overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px', minWidth: '620px' }}>
                <thead>
                  <tr>
                    <th
                      style={{
                        textAlign: 'left',
                        padding: '12px 14px',
                        borderBottom: '1px solid var(--border-subtle)',
                        color: 'var(--text-muted)',
                        fontSize: '10.5px',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      FEATURE
                    </th>
                    {COMPARISON_COLUMNS.map((col, i) => (
                      <th
                        key={col}
                        style={{
                          textAlign: 'center',
                          padding: '12px 10px',
                          borderBottom: '1px solid var(--border-subtle)',
                          color: i === 0 ? 'var(--accent-amber)' : 'var(--text-muted)',
                          fontSize: '11px',
                          fontWeight: 700,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {COMPARISON.map((row) => (
                    <tr key={row.feature} className="comparison-row">
                      <td
                        style={{
                          padding: '10px 14px',
                          borderBottom: '1px solid var(--border-subtle)',
                          color: 'var(--text-main)',
                        }}
                      >
                        {row.feature}
                      </td>
                      {row.support.map((level, i) => (
                        <td
                          key={i}
                          style={{
                            padding: '10px',
                            borderBottom: '1px solid var(--border-subtle)',
                            textAlign: 'center',
                          }}
                        >
                          <SupportBadge level={level} />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Reveal>
          <div
            style={{
              display: 'flex',
              gap: '18px',
              marginTop: '12px',
              fontSize: '11px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <span><SupportBadge level="full" /> Full support</span>
            <span><SupportBadge level="partial" /> Partial</span>
            <span><SupportBadge level="none" /> Not supported</span>
          </div>
        </section>

        {/* ── Impact & benefits ───────────────────────────────────── */}
        <section id="impact" style={{ padding: '48px 4px' }}>
          <SectionHeading description="Who benefits, how the platform is used, and how it sustains itself.">
            Impact &amp; benefits
          </SectionHeading>

          <div
            className="impact-grid"
            style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '32px' }}
          >
            {IMPACT_AREAS.map((area, i) => (
              <Reveal key={area.title} delay={i * 80}>
                <SpotlightCard style={{ padding: '16px 18px', height: '100%' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-pure)', marginBottom: '6px' }}>
                    {area.title}
                  </div>
                  <div style={{ fontSize: '12.5px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>
                    {area.body}
                  </div>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>

          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: 700,
              letterSpacing: '0.06em',
              color: 'var(--text-muted)',
              marginBottom: '14px',
            }}
          >
            WHO BENEFITS
          </div>
          <div style={{ borderTop: '1px solid var(--border-subtle)', marginBottom: '32px' }}>
            {WHO_BENEFITS.map((w, i) => (
              <Reveal key={w.title} delay={i * 60}>
                <div
                  className="capability-row capability-hover"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '260px 1fr',
                    gap: '24px',
                    padding: '16px 0',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-pure)' }}>{w.title}</div>
                  <div style={{ fontSize: '13px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>{w.body}</div>
                </div>
              </Reveal>
            ))}
          </div>

          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: 700,
              letterSpacing: '0.06em',
              color: 'var(--text-muted)',
              marginBottom: '14px',
            }}
          >
            BUSINESS &amp; REVENUE MODEL
          </div>
          <div
            className="impact-grid"
            style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}
          >
            {REVENUE_MODEL.map((r, i) => (
              <Reveal key={r.title} delay={i * 80}>
                <SpotlightCard style={{ padding: '16px 18px', height: '100%' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-pure)', marginBottom: '6px' }}>
                    {r.title}
                  </div>
                  <div style={{ fontSize: '12px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>{r.body}</div>
                </SpotlightCard>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── References ──────────────────────────────────────────── */}
        <section id="references" style={{ padding: '48px 4px' }}>
          <SectionHeading description="Open datasets, benchmarks, and libraries that underpin the platform.">
            Research &amp; references
          </SectionHeading>
          <div style={{ borderTop: '1px solid var(--border-subtle)' }}>
            {REFERENCES.map((ref, i) => (
              <Reveal key={ref.title} delay={i * 50}>
                <a
                  href={ref.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="capability-row ref-row"
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '220px 1fr',
                    gap: '24px',
                    padding: '14px 0',
                    borderBottom: '1px solid var(--border-subtle)',
                    textDecoration: 'none',
                  }}
                >
                  <div className="ref-title" style={{ fontSize: '13.5px', fontWeight: 700, color: 'var(--accent-amber)' }}>
                    {ref.title} ↗
                  </div>
                  <div style={{ fontSize: '12.5px', lineHeight: 1.55, color: 'var(--text-secondary)' }}>
                    {ref.body}
                  </div>
                </a>
              </Reveal>
            ))}
          </div>
        </section>

        {/* ── Closing CTA ─────────────────────────────────────────── */}
        <section style={{ padding: '20px 4px 64px' }}>
          <Reveal>
            <div
              className="intel-report-box cta-box"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '18px',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              <div className="cta-glow" aria-hidden="true" />
              <div style={{ position: 'relative', zIndex: 1 }}>
                <div
                  style={{
                    fontFamily: 'var(--font-hud)',
                    fontSize: '18px',
                    fontWeight: 700,
                    color: 'var(--text-pure)',
                    marginBottom: '4px',
                  }}
                >
                  Your first pass is one query away.
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Sign in, attach a frame, and ask it something.
                </div>
              </div>
              <Link
                href="/cockpit"
                className="btn-primary"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '13px 24px',
                  background: 'var(--accent-amber)',
                  border: '1px solid #a3561f',
                  borderRadius: 'var(--radius-md)',
                  color: '#ffffff',
                  fontFamily: 'var(--font-hud)',
                  fontSize: '13px',
                  fontWeight: 700,
                  letterSpacing: '0.04em',
                  textDecoration: 'none',
                  whiteSpace: 'nowrap',
                  position: 'relative',
                  overflow: 'hidden',
                  zIndex: 1,
                }}
              >
                <span className="btn-shine" aria-hidden="true" />
                Launch mission console →
              </Link>
            </div>
          </Reveal>
        </section>

        <footer
          style={{
            textAlign: 'center',
            padding: '24px 0 48px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            letterSpacing: '0.06em',
          }}
        >
          <div>AEROLENS AI // AUTONOMOUS ORBITAL EARTH OBSERVATION COCKPIT</div>
          <div style={{ marginTop: '4px', fontSize: '10px', opacity: 0.75 }}>
            Built for Smart India Hackathon 2026 · PS ID SIH26167 · Team ORB8X_26
          </div>
        </footer>
      </div>

      {/* ── Page-scoped styles ──────────────────────────────────── */}
      <style>{`
        html { scroll-behavior: smooth; }

        /* ── Logo animation ── */
        @keyframes orbitSpin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes orbitSpinReverse {
          from { transform: rotate(360deg); }
          to   { transform: rotate(0deg); }
        }
        @keyframes logoPulse {
          0%, 100% { transform: scale(1); }
          50%      { transform: scale(1.1); }
        }
        @keyframes sweepRotate {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }

        .landing-page .logo-mark {
          position: relative;
          width: 34px;
          height: 34px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }
        .landing-page .logo-orbit {
          position: absolute;
          border-radius: 50%;
          border: 1.5px solid transparent;
          pointer-events: none;
        }
        .landing-page .logo-orbit-outer {
          inset: 0;
          border-top-color: var(--accent-amber);
          border-right-color: rgba(194, 109, 46, 0.25);
          animation: orbitSpin 6s linear infinite;
        }
        .landing-page .logo-orbit-inner {
          inset: 6px;
          border-bottom-color: var(--accent-amber);
          border-left-color: rgba(194, 109, 46, 0.25);
          animation: orbitSpinReverse 4s linear infinite;
        }
        .landing-page .logo-orbit-sweep {
          inset: -3px;
          border: none;
          background: conic-gradient(
            from 0deg,
            transparent 0deg,
            rgba(194, 109, 46, 0.35) 40deg,
            transparent 90deg
          );
          mask: radial-gradient(circle, transparent 60%, black 62%, black 100%);
          -webkit-mask: radial-gradient(circle, transparent 60%, black 62%, black 100%);
          animation: sweepRotate 3s linear infinite;
          opacity: 0.55;
        }
        .landing-page .logo-core {
          font-size: 16px;
          animation: logoPulse 3s ease-in-out infinite;
          filter: drop-shadow(0 0 6px rgba(194, 109, 46, 0.55));
          z-index: 1;
        }

        /* ── Grid overlay animated ── */
        @keyframes gridDrift {
          0%   { background-position: 0 0, 0 0; }
          100% { background-position: 40px 40px, 40px 40px; }
        }
        .landing-page .animated-grid {
          animation: gridDrift 30s linear infinite;
        }

        /* ── Hackathon strip shimmer ── */
        @keyframes stripShimmer {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        .landing-page .hackathon-strip::after {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(194, 109, 46, 0.12) 50%,
            transparent 100%
          );
          animation: stripShimmer 4s ease-in-out infinite;
          pointer-events: none;
        }

        /* ── Nav links ── */
        .landing-page .nav-link {
          color: var(--text-muted);
          text-decoration: none;
          padding: 4px 8px;
          border-radius: 4px;
          position: relative;
          transition: color 0.18s ease, background 0.18s ease, transform 0.18s ease;
        }
        .landing-page .nav-link:hover {
          color: var(--accent-amber);
          background: var(--accent-amber-subtle);
          transform: translateY(-1px);
        }

        /* ── Nav button ── */
        .landing-page .nav-btn {
          transition: border-color 0.18s ease, color 0.18s ease, background 0.18s ease, transform 0.18s ease;
        }
        .landing-page .nav-btn:hover {
          border-color: var(--accent-amber-border) !important;
          color: var(--accent-amber) !important;
          background: var(--accent-amber-subtle) !important;
          transform: translateY(-1px);
        }

        /* ── Primary CTA + shine sweep ── */
        @keyframes btnShine {
          0%   { transform: translateX(-120%) skewX(-15deg); }
          100% { transform: translateX(220%) skewX(-15deg); }
        }
        .landing-page .btn-primary {
          transition: transform 0.18s ease, box-shadow 0.22s ease, background 0.18s ease;
        }
        .landing-page .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 26px rgba(194, 109, 46, 0.46) !important;
          background: #d47a34 !important;
        }
        .landing-page .btn-primary .btn-shine {
          position: absolute;
          top: 0;
          left: 0;
          width: 40%;
          height: 100%;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.35) 50%,
            transparent 100%
          );
          pointer-events: none;
          transform: translateX(-120%) skewX(-15deg);
        }
        .landing-page .btn-primary:hover .btn-shine {
          animation: btnShine 0.9s ease-out;
        }

        /* ── Spotlight card ── */
        .landing-page .panel-card {
          transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
                      box-shadow 0.26s ease,
                      border-color 0.22s ease;
        }
        .landing-page .panel-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
          border-color: var(--accent-amber-border);
        }
        .landing-page .spotlight-card {
          position: relative;
          overflow: hidden;
          isolation: isolate;
        }
        .landing-page .spotlight-card::before {
          content: '';
          position: absolute;
          inset: 0;
          background: radial-gradient(
            260px circle at var(--mx, -200px) var(--my, -200px),
            rgba(194, 109, 46, 0.10),
            transparent 60%
          );
          opacity: 0;
          transition: opacity 0.25s ease;
          pointer-events: none;
          z-index: 0;
        }
        .landing-page .spotlight-card:hover::before {
          opacity: 1;
        }
        .landing-page .spotlight-card > * {
          position: relative;
          z-index: 1;
        }

        /* ── Hero ── */
        .landing-page .hero-eyebrow {
          animation: fadeUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.1s both;
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(14px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .landing-page .hero-title {
          animation: fadeUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both;
        }

        /* ── Hero animated underline ── */
        .landing-page .hero-underline {
          position: relative;
          display: inline-block;
          color: var(--accent-amber);
        }
        .landing-page .hero-underline svg {
          position: absolute;
          left: 0;
          right: 0;
          bottom: -6px;
          width: 100%;
          height: 10px;
          color: var(--accent-amber);
          overflow: visible;
        }
        .landing-page .hero-underline svg path {
          stroke-dasharray: 300;
          stroke-dashoffset: 300;
          animation: drawUnderline 1.2s cubic-bezier(0.22, 1, 0.36, 1) 0.9s forwards;
        }
        @keyframes drawUnderline {
          to { stroke-dashoffset: 0; }
        }

        .landing-page .hero-secondary-link {
          position: relative;
          transition: color 0.18s ease, transform 0.18s ease;
          display: inline-block;
        }
        .landing-page .hero-secondary-link:hover {
          color: var(--accent-amber) !important;
          transform: translateY(2px);
        }

        /* ── Tag pill pop-in ── */
        .landing-page .tag-pop {
          animation: tagPop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
        }
        @keyframes tagPop {
          from { opacity: 0; transform: scale(0.85) translateY(6px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
        .landing-page .tag-hover {
          transition: transform 0.18s ease, border-color 0.18s ease, color 0.18s ease;
        }
        .landing-page .tag-hover:hover {
          transform: translateY(-2px);
          border-color: var(--accent-amber-border);
          color: var(--accent-amber);
        }

        /* ── Hero card ── */
        .landing-page .hero-card {
          transition: transform 0.1s linear;
        }

        /* ── Hero tile scan sweep ── */
        @keyframes tileScan {
          0%   { transform: translateY(-100%); }
          100% { transform: translateY(400%); }
        }
        .landing-page .hero-tile {
          animation: fadeUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        .landing-page .hero-tile-scan {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 20%;
          background: linear-gradient(
            180deg,
            transparent 0%,
            rgba(194, 109, 46, 0.35) 50%,
            transparent 100%
          );
          animation: tileScan 3s linear infinite;
          pointer-events: none;
          opacity: 0.7;
        }

        /* ── Hero answer reveal ── */
        .landing-page .hero-answer {
          animation: fadeUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) 1.1s both;
        }

        /* ── Deployed badge ── */
        @keyframes badgeGlow {
          0%, 100% { box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.25); }
          50%      { box-shadow: 0 0 0 6px rgba(22, 163, 74, 0); }
        }
        .landing-page .deployed-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          background: var(--accent-emerald-subtle);
          border: 1px solid var(--accent-emerald-border);
          border-radius: 20px;
          font-family: var(--font-mono);
          font-size: 10px;
          font-weight: 700;
          color: var(--accent-emerald);
          letter-spacing: 0.06em;
          animation: badgeGlow 2.5s ease-in-out infinite;
        }

        /* ── Bolt orb ── */
        @keyframes orbPulse {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(194, 109, 46, 0.25);
          }
          50% {
            transform: scale(1.05);
            box-shadow: 0 0 0 8px rgba(194, 109, 46, 0);
          }
        }
        .landing-page .bolt-orb {
          width: 88px;
          height: 88px;
          border-radius: 50%;
          border: 2px solid var(--accent-amber-border);
          background: var(--accent-amber-subtle);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 34px;
          flex-shrink: 0;
          animation: orbPulse 2.4s ease-in-out infinite;
        }

        /* ── Brain pulse ── */
        @keyframes brainPulse {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 0 rgba(194, 109, 46, 0)); }
          50%      { transform: scale(1.12); filter: drop-shadow(0 0 8px rgba(194, 109, 46, 0.55)); }
        }
        .landing-page .brain-pulse {
          display: inline-block;
          animation: brainPulse 2.6s ease-in-out infinite;
        }

        /* ── Video glow frame ── */
        @keyframes videoGlow {
          0%, 100% { opacity: 0.5; }
          50%      { opacity: 1; }
        }
        .landing-page .video-frame {
          position: relative;
        }
        .landing-page .video-frame-glow {
          position: absolute;
          inset: -2px;
          border-radius: var(--radius-md);
          background: conic-gradient(
            from 0deg,
            var(--accent-amber),
            transparent 40%,
            var(--accent-amber) 80%,
            transparent 100%
          );
          filter: blur(6px);
          opacity: 0.5;
          animation: videoGlow 3s ease-in-out infinite;
          pointer-events: none;
        }

        /* ── Video placeholder ── */
        @keyframes placeholderPulse {
          0%, 100% { border-color: var(--border-subtle); }
          50%      { border-color: var(--accent-amber-border); }
        }
        .landing-page .video-placeholder {
          animation: placeholderPulse 3s ease-in-out infinite;
        }

        /* ── Step number badge ── */
        .landing-page .step-number {
          font-family: var(--font-mono);
          font-size: '11px';
          font-weight: 700;
          color: var(--accent-amber);
          marginBottom: '10px';
          display: inline-block;
          padding: '2px 8px';
          border-radius: 4px;
          background: var(--accent-amber-subtle);
          border: 1px solid var(--accent-amber-border);
          font-size: 11px;
          margin-bottom: 10px;
          letter-spacing: 0.06em;
        }

        /* ── Capability row hover ── */
        .landing-page .capability-hover {
          transition: background 0.22s ease, padding-left 0.22s ease;
          padding-left: 0;
        }
        .landing-page .capability-hover:hover {
          background: linear-gradient(90deg, var(--accent-amber-subtle) 0%, transparent 60%);
          padding-left: 12px;
        }
        .landing-page .mitigation-cell {
          transition: border-color 0.2s ease;
        }
        .landing-page .capability-hover:hover .mitigation-cell {
          border-color: var(--accent-amber);
        }

        /* ── Pipeline dots ── */
        .landing-page .pipeline-dot {
          position: absolute;
          left: -28px;
          top: 2px;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: var(--accent-amber);
          color: #fff;
          font-family: var(--font-mono);
          font-size: 9.5px;
          font-weight: 800;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 0 0 rgba(194, 109, 46, 0.5);
          animation: dotPulse 2.6s ease-in-out infinite;
        }
        @keyframes dotPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(194, 109, 46, 0.4); }
          50%      { box-shadow: 0 0 0 6px rgba(194, 109, 46, 0); }
        }

        /* ── Comparison row hover ── */
        .landing-page .comparison-row {
          transition: background 0.18s ease;
        }
        .landing-page .comparison-row:hover {
          background: var(--accent-amber-subtle);
        }

        /* ── References ── */
        .landing-page .ref-row {
          transition: background 0.22s ease, padding-left 0.22s ease;
        }
        .landing-page .ref-row:hover {
          background: var(--accent-amber-subtle);
          padding-left: 12px;
        }
        .landing-page .ref-title {
          transition: transform 0.2s ease;
        }
        .landing-page .ref-row:hover .ref-title {
          transform: translateX(3px);
        }

        /* ── CTA glow ── */
        @keyframes ctaGlow {
          0%, 100% { transform: translateX(-30%) scale(1); opacity: 0.4; }
          50%      { transform: translateX(30%) scale(1.2); opacity: 0.7; }
        }
        .landing-page .cta-glow {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 60%;
          height: 200%;
          background: radial-gradient(circle, rgba(194, 109, 46, 0.35) 0%, transparent 60%);
          transform: translate(-50%, -50%);
          pointer-events: none;
          animation: ctaGlow 6s ease-in-out infinite;
          filter: blur(20px);
        }

        /* ── Reduced motion ── */
        @media (prefers-reduced-motion: reduce) {
          .landing-page *,
          .landing-page *::before,
          .landing-page *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }

        /* ── Responsive ── */
        @media (max-width: 860px) {
          .landing-page .landing-hero-grid {
            grid-template-columns: 1fr !important;
          }
          .landing-page .steps-grid {
            grid-template-columns: 1fr 1fr !important;
          }
          .landing-page .capability-row {
            grid-template-columns: 1fr !important;
            gap: 6px !important;
          }
          .landing-page .tech-grid {
            grid-template-columns: 1fr 1fr !important;
          }
          .landing-page .impact-grid {
            grid-template-columns: 1fr 1fr !important;
          }
          .landing-page .innovation-metrics-grid {
            grid-template-columns: 1fr 1fr !important;
          }
          .landing-page .innovation-agent-grid {
            grid-template-columns: 1fr !important;
          }
        }
        @media (max-width: 520px) {
          .landing-page .steps-grid,
          .landing-page .tech-grid,
          .landing-page .impact-grid,
          .landing-page .innovation-metrics-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}