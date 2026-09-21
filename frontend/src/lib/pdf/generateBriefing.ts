import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { AnalysisResponse } from '@/types/satquery';
import { renderMarkdownToPdf, sanitizeForPdf, type Cursor, type PdfLayout } from './markdownToPdf';

const PAGE_WIDTH = 595.28; // A4 pt
const PAGE_HEIGHT = 841.89;
const MARGIN = 48;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2;

const AMBER: [number, number, number] = [194, 109, 46];
const INK: [number, number, number] = [28, 25, 23];
const MUTED: [number, number, number] = [120, 113, 108];
const PANEL: [number, number, number] = [248, 244, 236];
const BORDER: [number, number, number] = [214, 205, 192];

const LAYOUT: PdfLayout = {
    marginX: MARGIN,
    contentWidth: CONTENT_WIDTH,
    pageHeight: PAGE_HEIGHT,
    bottomLimit: PAGE_HEIGHT - MARGIN - 24,
    colors: { ink: INK, muted: MUTED, amber: AMBER, panel: PANEL, border: BORDER },
};

/**
 * Loads an image (either a remote Cloudinary URL or an existing base64 data
 * URL) into a canvas and re-encodes it as a PNG data URL, so jsPDF always
 * receives a format it can embed regardless of the source's original
 * format. Cross-origin loads rely on Cloudinary sending permissive CORS
 * headers (the default for delivered assets); if a particular image can't
 * be loaded (network hiccup, misconfigured host, etc.) this resolves to
 * null instead of throwing, so one bad image never blocks the whole report.
 */
function loadImage(url: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error(`Could not load image: ${url}`));
        img.src = url;
    });
}

async function toEmbeddablePng(url: string): Promise<{ dataUrl: string; width: number; height: number } | null> {
    try {
        const img = await loadImage(url);
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth || 512;
        canvas.height = img.naturalHeight || 512;
        const ctx = canvas.getContext('2d');
        if (!ctx) return null;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        return { dataUrl: canvas.toDataURL('image/png'), width: canvas.width, height: canvas.height };
    } catch {
        return null;
    }
}

interface BriefingOptions {
    query: string;
    response: AnalysisResponse;
    missionRef?: string;
    onProgress?: (stage: string) => void;
}

export async function generateMissionBriefingPdf({ query, response, missionRef, onProgress }: BriefingOptions): Promise<void> {
    const doc = new jsPDF({ unit: 'pt', format: 'a4' });
    const ref = missionRef || `SQ-EO-${new Date().getFullYear()}-${Math.floor(Math.random() * 9000 + 1000)}`;
    let y = MARGIN;

    const ensureSpace = (needed: number) => {
        if (y + needed > PAGE_HEIGHT - MARGIN - 24) {
            doc.addPage();
            y = MARGIN;
        }
    };

    const sectionHeading = (text: string) => {
        ensureSpace(28);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor(...AMBER);
        doc.text(text.toUpperCase(), MARGIN, y);
        y += 6;
        doc.setDrawColor(...BORDER);
        doc.setLineWidth(0.75);
        doc.line(MARGIN, y, PAGE_WIDTH - MARGIN, y);
        y += 16;
    };

    const bodyParagraph = (text: string, opts?: { size?: number; color?: [number, number, number]; leading?: number }) => {
        const size = opts?.size ?? 10.5;
        const color = opts?.color ?? INK;
        const leading = opts?.leading ?? size * 1.45;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(size);
        doc.setTextColor(...color);
        const lines = doc.splitTextToSize(text, CONTENT_WIDTH) as string[];
        for (const line of lines) {
            ensureSpace(leading);
            doc.text(line, MARGIN, y);
            y += leading;
        }
    };

    // ── Header ────────────────────────────────────────────────────────────
    doc.setFillColor(...INK);
    doc.rect(0, 0, PAGE_WIDTH, 6, 'F');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(...AMBER);
    doc.text('NATIONAL REMOTE SENSING & GEOSPATIAL INTELLIGENCE // AEROLENS AI', MARGIN, (y += 26));

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(19);
    doc.setTextColor(...INK);
    doc.text('ORBITAL MISSION INTELLIGENCE BRIEFING', MARGIN, (y += 22));

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(...MUTED);
    doc.text(`PASS REF: ${ref}  ·  GENERATED: ${new Date().toUTCString()}`, MARGIN, (y += 16));

    doc.setDrawColor(...AMBER);
    doc.setFillColor(255, 249, 240);
    doc.roundedRect(PAGE_WIDTH - MARGIN - 130, MARGIN - 10, 130, 20, 3, 3, 'FD');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...AMBER);
    doc.text('UNCLASSIFIED // SCIENTIFIC', PAGE_WIDTH - MARGIN - 65, MARGIN + 4, { align: 'center' });

    y += 18;
    doc.setDrawColor(...INK);
    doc.setLineWidth(1.2);
    doc.line(MARGIN, y, PAGE_WIDTH - MARGIN, y);
    y += 22;

    // ── Mission inquiry ───────────────────────────────────────────────────
    doc.setFillColor(...PANEL);
    doc.setDrawColor(...BORDER);
    const queryLines = doc.splitTextToSize(`"${sanitizeForPdf(query)}"`, CONTENT_WIDTH - 24) as string[];
    const queryBoxHeight = 34 + queryLines.length * 15;
    ensureSpace(queryBoxHeight);
    doc.roundedRect(MARGIN, y, CONTENT_WIDTH, queryBoxHeight, 4, 4, 'FD');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...MUTED);
    doc.text('MISSION INQUIRY & TARGET OBJECTIVE', MARGIN + 12, y + 16);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(...INK);
    queryLines.forEach((line, i) => doc.text(line, MARGIN + 12, y + 32 + i * 15));
    y += queryBoxHeight + 22;

    // ── Section 1: VLM synthesis ──────────────────────────────────────────
    sectionHeading('1.0  Autonomous VLM Intelligence Synthesis');
    if (response.answer && response.answer.trim()) {
        // The model's answer is Markdown (headings, **bold**, GFM tables) — render
        // it as real PDF primitives instead of dumping raw markdown syntax as
        // wrapped plain text (which is what produced garbled tables/headings before).
        const cursor: Cursor = { y };
        renderMarkdownToPdf(doc, cursor, LAYOUT, response.answer);
        y = cursor.y;
    } else {
        bodyParagraph('No synthesis text was returned for this pass.');
    }
    y += 12;

    // ── Section 2: Evidence matrix (real embedded images, not a UI screenshot) ──
    onProgress?.('Embedding evidence imagery…');
    const slots: { key: keyof typeof response.evidence; label: string; color: [number, number, number] }[] = [
        { key: 'slot1_original', label: 'SLOT 01 · OPTICAL', color: INK },
        { key: 'slot2_attention_or_diff', label: 'SLOT 02 · ATTENTION/DIFF', color: AMBER },
        { key: 'slot3_reticle_or_sar', label: 'SLOT 03 · RETICLE/SAR', color: [27, 106, 72] },
        { key: 'slot4_after', label: 'SLOT 04 · T2 AFTER', color: [190, 70, 60] },
    ];
    const loaded = await Promise.all(
        slots.map(async (s) => {
            const url = response.evidence[s.key] as string | null;
            if (!url) return null;
            const img = await toEmbeddablePng(url);
            return img ? { ...s, ...img } : null;
        })
    );
    const availableImages = loaded.filter((x): x is NonNullable<typeof x> => !!x);

    if (availableImages.length > 0) {
        sectionHeading('2.0  Multi-Spectral Decoded Evidence Matrix');
        const cols = 2;
        const gap = 12;
        const cellW = (CONTENT_WIDTH - gap * (cols - 1)) / cols;
        const cellImgH = cellW * 0.62;
        const cellH = cellImgH + 24;

        availableImages.forEach((img, i) => {
            const col = i % cols;
            if (col === 0) ensureSpace(cellH + gap);
            const x = MARGIN + col * (cellW + gap);
            doc.setFillColor(...PANEL);
            doc.setDrawColor(...BORDER);
            doc.roundedRect(x, y, cellW, cellH, 3, 3, 'FD');

            const ratio = img.width / img.height;
            let drawW = cellW - 12;
            let drawH = drawW / ratio;
            if (drawH > cellImgH - 6) {
                drawH = cellImgH - 6;
                drawW = drawH * ratio;
            }
            doc.addImage(img.dataUrl, 'PNG', x + (cellW - drawW) / 2, y + 6, drawW, drawH);

            doc.setFont('helvetica', 'bold');
            doc.setFontSize(7.5);
            doc.setTextColor(...img.color);
            doc.text(img.label, x + 8, y + cellImgH + 16);

            if (col === cols - 1 || i === availableImages.length - 1) {
                y += cellH + gap;
            }
        });
        y += 6;
    } else if (availableImages.length === 0 && slots.some((s) => response.evidence[s.key])) {
        bodyParagraph('(Evidence imagery could not be embedded — the source images may be unreachable from this browser session.)', {
            size: 9,
            color: MUTED,
        });
    }

    // ── Section 3: Detected objects ───────────────────────────────────────
    if (response.detected_objects && response.detected_objects.length > 0) {
        sectionHeading('3.0  Target Detection & Classification Log');
        autoTable(doc, {
            startY: y,
            margin: { left: MARGIN, right: MARGIN },
            head: [['Label', 'Category', 'Confidence', 'Bounding Box (xmin, ymin, xmax, ymax)']],
            body: response.detected_objects.map((o) => [
                sanitizeForPdf(o.label),
                sanitizeForPdf(o.category),
                `${Math.round(o.confidence * 100)}%`,
                `${o.xmin.toFixed(3)}, ${o.ymin.toFixed(3)}, ${o.xmax.toFixed(3)}, ${o.ymax.toFixed(3)}`,
            ]),
            styles: { font: 'helvetica', fontSize: 8.5, textColor: INK, lineColor: BORDER },
            headStyles: { fillColor: INK, textColor: 255 },
            alternateRowStyles: { fillColor: PANEL },
        });
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        y = (doc as any).lastAutoTable.finalY + 22;
    }

    // ── Section 4: Execution telemetry ────────────────────────────────────
    const trace = response.trace;
    sectionHeading(`${response.detected_objects?.length ? '4.0' : '3.0'}  Pipeline Execution Telemetry`);
    const confidencePct = Math.round((trace?.confidence ?? 0.9) * 100);
    bodyParagraph(
        `Confidence: ${confidencePct}%   ·   Latency: ${trace?.elapsed_seconds?.toFixed(2) ?? '—'}s   ·   Task: ${trace?.task ?? 'N/A'}`,
        { size: 9.5, color: MUTED }
    );
    if (trace?.tools_used?.length) {
        bodyParagraph(`Tools invoked: ${sanitizeForPdf(trace.tools_used.join(', '))}`, { size: 9.5, color: MUTED });
    }
    if (trace?.rs_adaptation) {
        bodyParagraph(`Remote-sensing adaptation: ${sanitizeForPdf(trace.rs_adaptation)}`, { size: 9.5, color: MUTED });
    }
    if (trace?.warnings?.length) {
        bodyParagraph(`Warnings: ${sanitizeForPdf(trace.warnings.join('; '))}`, { size: 9.5, color: [176, 80, 40] });
    }

    // ── Footer (page numbers) on every page ───────────────────────────────
    const pageCount = doc.getNumberOfPages();
    for (let p = 1; p <= pageCount; p++) {
        doc.setPage(p);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(...MUTED);
        doc.text('AEROLENS AI // AUTONOMOUS ORBITAL EARTH OBSERVATION COCKPIT', MARGIN, PAGE_HEIGHT - 24);
        doc.text(`Page ${p} of ${pageCount}`, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 24, { align: 'right' });
    }

    onProgress?.('Finalizing document…');
    const fileName = `AeroLens_Mission_Briefing_${ref}.pdf`;
    doc.save(fileName);
}