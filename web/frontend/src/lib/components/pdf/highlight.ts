import type { TextContent, TextItem } from 'pdfjs-dist/types/src/display/api';

export type Highlight = { paragraph?: string; text?: string };

/** Rectangle in PDF user space (origin bottom-left, y up). */
export type PdfRect = { left: number; right: number; top: number; bottom: number };

export type HighlightMatch = { rect: PdfRect; via: 'paragraph' | 'text' };

type Line = { text: string; x0: number; x1: number; y: number; h: number };

const HEADER_RE = /\|\s*page \d+ of \d+/i;
const LABEL_RE = /^(\d+(\.\d+)+\.?\s|\d+\.\s|Annex\s+\d)/;
const MARGIN_SLACK = 2;
const PARAGRAPH_GAP = 1.15;
const MIN_TEXT_SCORE = 0.4;

function buildLines(content: TextContent): Line[] {
	const items = content.items.filter((it): it is TextItem => 'str' in it && it.str.trim() !== '');
	const rows: { y: number; items: TextItem[] }[] = [];
	for (const it of items) {
		const y = it.transform[5];
		const row = rows.find((r) => Math.abs(r.y - y) < 2);
		if (row) row.items.push(it);
		else rows.push({ y, items: [it] });
	}
	return rows
		.map(({ y, items }) => {
			items.sort((a, b) => a.transform[4] - b.transform[4]);
			return {
				text: items
					.map((it) => it.str)
					.join(' ')
					.replace(/\s+/g, ' ')
					.trim(),
				x0: Math.min(...items.map((it) => it.transform[4])),
				x1: Math.max(...items.map((it) => it.transform[4] + it.width)),
				y,
				h: Math.max(
					...items.map((it) => it.height || Math.hypot(it.transform[2], it.transform[3])),
				),
			};
		})
		.filter((l) => !HEADER_RE.test(l.text))
		.sort((a, b) => b.y - a.y);
}

/** Indices of lines that open a new paragraph: a label at the left margin after a paragraph gap. */
function paragraphStarts(lines: Line[]): Set<number> {
	const margin = Math.min(...lines.map((l) => l.x0));
	const gaps = lines.slice(1).map((l, i) => lines[i].y - l.y);
	const minGap = Math.min(...gaps.filter((g) => g > 4));
	const starts = new Set<number>([0]);
	lines.forEach((l, i) => {
		if (i === 0 || l.x0 > margin + MARGIN_SLACK || !LABEL_RE.test(l.text)) return;
		if (gaps[i - 1] >= minGap * PARAGRAPH_GAP) starts.add(i);
	});
	return starts;
}

function escapeRe(s: string) {
	return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function labelRe(label: string) {
	return new RegExp(`^${escapeRe(label).replace(/\s+/g, '\\s+')}\\.?(\\s|$)`, 'i');
}

function findParagraph(lines: Line[], paragraph: string): number {
	const label = paragraph.trim().replace(/[.\s]+$/, '');
	if (!label) return -1;
	const margin = Math.min(...lines.map((l) => l.x0));
	const atMargin = (i: number) => lines[i].x0 <= margin + MARGIN_SLACK;
	const matching = (re: RegExp, from = 0) =>
		lines.findIndex((l, i) => i >= from && atMargin(i) && re.test(l.text));

	const direct = matching(labelRe(label));
	if (direct >= 0) return direct;

	const annex = label.match(/^Annex\s+(\w+)(?:\s+Part\s+(\w+))?\s*(.*)$/i);
	if (!annex) return -1;
	const [, num, part, sub] = annex;
	let from = 0;
	const annexHeading = matching(labelRe(`Annex ${num}`));
	if (annexHeading >= 0) from = annexHeading;
	if (part) {
		const partHeading = matching(labelRe(`Part ${part}`), from);
		if (partHeading >= 0) from = partHeading;
	}
	return sub ? matching(labelRe(sub), from) : annexHeading;
}

function words(s: string): Set<string> {
	return new Set(s.toLowerCase().match(/[a-z0-9]{3,}/g) ?? []);
}

function findByText(lines: Line[], starts: number[], text: string): number {
	const query = words(text);
	if (query.size === 0) return -1;
	let best = -1;
	let bestScore = MIN_TEXT_SCORE;
	starts.forEach((start, k) => {
		const block = words(
			lines
				.slice(start, starts[k + 1] ?? lines.length)
				.map((l) => l.text)
				.join(' '),
		);
		let hits = 0;
		for (const w of query) if (block.has(w)) hits++;
		const score = hits / query.size;
		if (score > bestScore) {
			bestScore = score;
			best = start;
		}
	});
	return best;
}

export function findHighlight(content: TextContent, highlight: Highlight): HighlightMatch | null {
	const lines = buildLines(content);
	if (lines.length === 0) return null;
	const startSet = paragraphStarts(lines);
	const starts = [...startSet].sort((a, b) => a - b);

	let via: HighlightMatch['via'] = 'paragraph';
	let start = highlight.paragraph ? findParagraph(lines, highlight.paragraph) : -1;
	if (start < 0 && highlight.text) {
		via = 'text';
		start = findByText(lines, starts, highlight.text);
	}
	if (start < 0) return null;

	const end = starts.find((s) => s > start) ?? lines.length;
	const block = lines.slice(start, end);
	const first = block[0];
	const last = block[block.length - 1];
	return {
		via,
		rect: {
			left: Math.min(...block.map((l) => l.x0)),
			right: Math.max(...block.map((l) => l.x1)),
			top: first.y + first.h,
			bottom: last.y - last.h * 0.3,
		},
	};
}
