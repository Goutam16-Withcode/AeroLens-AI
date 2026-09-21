import type { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

export type RGB = [number, number, number];

export interface Cursor {
    y: number;
}

export interface PdfLayout {
    marginX: number;
    contentWidth: number;
    pageHeight: number;
    bottomLimit: number; // y beyond which we must start a new page
    colors: { ink: RGB; muted: RGB; amber: RGB; panel: RGB; border: RGB };
}

/**
 * jsPDF's built-in standard fonts (helvetica etc.) only support the WinAnsi
 * (roughly Latin-1 + common punctuation) character set. Emoji and other
 * pictographic Unicode characters silently render as garbled glyphs
 * (mojibake) instead of failing loudly, which is exactly what showed up in
 * the generated briefings. Stripping them here is far more legible than
 * shipping a whole Unicode font just to render decorative emoji.
 */
export function sanitizeForPdf(text: string): string {
    return text
        .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}\u{2190}-\u{21FF}]/gu, '')
        .replace(/[^\x09\x0A\x0D\x20-\x7E\u00A0-\u017F\u2010-\u2027\u2030-\u203A\u20AC\u2122\u2122]/g, '')
        .replace(/[ \t]{2,}/g, ' ');
}

/** Splits "some **bold** text" into alternating plain/bold segments. Only handles non-nested **bold**. */
function splitBoldSegments(text: string): { text: string; bold: boolean }[] {
    return text
        .split(/(\*\*[^*]+\*\*)/g)
        .filter((part) => part.length > 0)
        .map((part) => {
            if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
                return { text: part.slice(2, -2), bold: true };
            }
            return { text: part, bold: false };
        });
}

/** Tokenizes bold/plain segments into words + whitespace, preserving each token's bold flag, for word-by-word wrapping. */
function tokenize(segments: { text: string; bold: boolean }[]): { text: string; bold: boolean }[] {
    const tokens: { text: string; bold: boolean }[] = [];
    for (const seg of segments) {
        const parts = seg.text.split(/(\s+)/).filter((p) => p.length > 0);
        for (const p of parts) tokens.push({ text: p, bold: seg.bold });
    }
    return tokens;
}

function ensureSpace(doc: jsPDF, cursor: Cursor, layout: PdfLayout, needed: number) {
    if (cursor.y + needed > layout.bottomLimit) {
        doc.addPage();
        cursor.y = layout.marginX;
    }
}

/** Draws left-aligned, word-wrapped text that may contain **bold** runs, advancing cursor.y as it goes. */
function drawRichText(
    doc: jsPDF,
    cursor: Cursor,
    layout: PdfLayout,
    rawText: string,
    opts: { x?: number; maxWidth?: number; fontSize?: number; leading?: number; color?: RGB } = {}
) {
    const x = opts.x ?? layout.marginX;
    const maxWidth = opts.maxWidth ?? layout.contentWidth;
    const fontSize = opts.fontSize ?? 10.5;
    const leading = opts.leading ?? fontSize * 1.45;
    const color = opts.color ?? layout.colors.ink;

    const tokens = tokenize(splitBoldSegments(sanitizeForPdf(rawText)));
    let line: { text: string; bold: boolean }[] = [];
    let lineWidth = 0;

    const measure = (t: { text: string; bold: boolean }) => {
        doc.setFont('helvetica', t.bold ? 'bold' : 'normal');
        doc.setFontSize(fontSize);
        return doc.getTextWidth(t.text);
    };

    const flushLine = () => {
        if (line.length === 0) return;
        // Trim a single trailing whitespace token so lines don't end with a visible gap.
        if (line[line.length - 1].text.trim() === '') line = line.slice(0, -1);
        ensureSpace(doc, cursor, layout, leading);
        let cx = x;
        for (const t of line) {
            doc.setFont('helvetica', t.bold ? 'bold' : 'normal');
            doc.setFontSize(fontSize);
            doc.setTextColor(...color);
            doc.text(t.text, cx, cursor.y);
            cx += doc.getTextWidth(t.text);
        }
        cursor.y += leading;
        line = [];
        lineWidth = 0;
    };

    for (const token of tokens) {
        // Never start a new line with a bare whitespace token.
        if (line.length === 0 && token.text.trim() === '') continue;
        const w = measure(token);
        if (lineWidth + w > maxWidth && line.length > 0) {
            flushLine();
        }
        line.push(token);
        lineWidth += w;
    }
    flushLine();
}

const TABLE_ROW_RE = /^\s*\|(.*)\|\s*$/;
const TABLE_SEPARATOR_RE = /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/;
const HEADING_RE = /^(#{1,6})\s+(.*)$/;
const HR_RE = /^(-{3,}|\*{3,}|_{3,})\s*$/;
const BULLET_RE = /^[-*]\s+(.*)$/;
const NUMBERED_RE = /^\d+[.)]\s+(.*)$/;

function parseTableRow(line: string): string[] {
    const inner = line.trim().replace(/^\|/, '').replace(/\|$/, '');
    return inner.split('|').map((cell) => sanitizeForPdf(cell.replace(/\*\*/g, '').trim()));
}

/**
 * Renders a (deliberately limited, LLM-output-focused) Markdown subset:
 * headings (#..######), tables (GFM pipe tables), bullet/numbered lists,
 * horizontal rules, and paragraphs with inline **bold** — as real PDF
 * primitives (drawn text, an actual autoTable, drawn rules) rather than
 * dumping the raw markdown syntax as wrapped plain text.
 */
export function renderMarkdownToPdf(doc: jsPDF, cursor: Cursor, layout: PdfLayout, markdown: string) {
    const lines = markdown.replace(/\r\n/g, '\n').split('\n');

    let buffer: string[] = [];
    let bufferIndent = 0; // 0 = plain paragraph, >0 = bullet/number indent in points

    const flushParagraph = () => {
        if (buffer.length === 0) return;
        const joined = buffer.join(' ').replace(/\s+/g, ' ').trim();
        buffer = [];
        if (!joined) return;
        if (bufferIndent > 0) {
            ensureSpace(doc, cursor, layout, 12);
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(10.5);
            doc.setTextColor(...layout.colors.ink);
            doc.text('•', layout.marginX + 2, cursor.y);
            drawRichText(doc, cursor, layout, joined, {
                x: layout.marginX + bufferIndent,
                maxWidth: layout.contentWidth - bufferIndent,
            });
        } else {
            drawRichText(doc, cursor, layout, joined);
        }
        cursor.y += 4;
    };

    let i = 0;
    while (i < lines.length) {
        const raw = lines[i];
        const trimmed = raw.trim();

        if (trimmed === '') {
            flushParagraph();
            cursor.y += 6;
            i++;
            continue;
        }

        // GFM table: a row line immediately followed by a separator line.
        if (TABLE_ROW_RE.test(trimmed) && i + 1 < lines.length && TABLE_SEPARATOR_RE.test(lines[i + 1].trim())) {
            flushParagraph();
            const header = parseTableRow(trimmed);
            const body: string[][] = [];
            i += 2; // skip header + separator
            while (i < lines.length && TABLE_ROW_RE.test(lines[i].trim())) {
                body.push(parseTableRow(lines[i].trim()));
                i++;
            }
            ensureSpace(doc, cursor, layout, 40);
            autoTable(doc, {
                startY: cursor.y,
                margin: { left: layout.marginX, right: layout.marginX, bottom: layout.marginX + 24 },
                head: [header],
                body,
                styles: {
                    font: 'helvetica',
                    fontSize: 8,
                    textColor: layout.colors.ink,
                    lineColor: layout.colors.border,
                    cellPadding: 4,
                    overflow: 'linebreak',
                },
                headStyles: { fillColor: layout.colors.ink, textColor: 255, fontStyle: 'bold' },
                alternateRowStyles: { fillColor: layout.colors.panel },
            });
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            cursor.y = (doc as any).lastAutoTable.finalY + 14;
            continue;
        }

        const heading = trimmed.match(HEADING_RE);
        if (heading) {
            flushParagraph();
            const level = heading[1].length;
            const text = sanitizeForPdf(heading[2].replace(/\*\*/g, ''));
            const size = level === 1 ? 13 : level === 2 ? 11.5 : level === 3 ? 10.5 : 9.5;
            ensureSpace(doc, cursor, layout, size * 1.6 + 6);
            cursor.y += 6;
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(size);
            doc.setTextColor(...(level <= 2 ? layout.colors.ink : layout.colors.amber));
            doc.text(text, layout.marginX, cursor.y);
            cursor.y += size * 0.9;
            i++;
            continue;
        }

        if (HR_RE.test(trimmed)) {
            flushParagraph();
            ensureSpace(doc, cursor, layout, 14);
            cursor.y += 4;
            doc.setDrawColor(...layout.colors.border);
            doc.setLineWidth(0.75);
            doc.line(layout.marginX, cursor.y, layout.marginX + layout.contentWidth, cursor.y);
            cursor.y += 12;
            i++;
            continue;
        }

        const bullet = trimmed.match(BULLET_RE) || trimmed.match(NUMBERED_RE);
        if (bullet) {
            flushParagraph();
            buffer = [bullet[1]];
            bufferIndent = 14;
            i++;
            continue;
        }

        // Plain text line: continuation of the current paragraph/bullet buffer.
        if (buffer.length === 0) bufferIndent = 0;
        buffer.push(trimmed);
        i++;
    }
    flushParagraph();
}