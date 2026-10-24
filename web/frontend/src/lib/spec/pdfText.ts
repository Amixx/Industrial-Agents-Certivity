import type { TextItem } from 'pdfjs-dist/types/src/display/api';
import { loadPdfJs } from '#lib/components/pdf/loader.ts';

export type PdfSpec = { text: string; pages: number };

export class ScannedPdfError extends Error {
	constructor() {
		super('This PDF has no text layer (looks scanned). Scanned PDFs are not supported yet.');
	}
}

type Line = { x: number; y: number; size: number; text: string; cells: string[] };

function pageLines(items: TextItem[]): Line[] {
	const lines: { y: number; size: number; parts: { x: number; w: number; str: string }[] }[] = [];
	for (const item of items) {
		if (!item.str.trim() && !item.hasEOL) continue;
		const y = item.transform[5];
		const size = Math.hypot(item.transform[2], item.transform[3]);
		const line = lines.find((l) => Math.abs(l.y - y) < size * 0.4);
		if (line) {
			line.parts.push({ x: item.transform[4], w: item.width, str: item.str });
			line.size = Math.max(line.size, size);
		} else {
			lines.push({ y, size, parts: [{ x: item.transform[4], w: item.width, str: item.str }] });
		}
	}
	return lines
		.sort((a, b) => b.y - a.y)
		.map((l) => {
			const parts = l.parts.sort((a, b) => a.x - b.x);
			const cells: string[] = [];
			let end = Number.NEGATIVE_INFINITY;
			for (const p of parts) {
				if (cells.length && p.x - end <= l.size * 0.3) cells[cells.length - 1] += p.str;
				else cells.push(p.str);
				end = p.x + p.w;
			}
			const clean = cells.map((c) => c.replace(/\s+/g, ' ').trim()).filter(Boolean);
			return { x: parts[0].x, y: l.y, size: l.size, text: clean.join(' '), cells: clean };
		})
		.filter((l) => l.text);
}

export async function extractPdfText(file: File): Promise<PdfSpec> {
	const pdfjs = await loadPdfJs();
	const task = pdfjs.getDocument({ data: await file.arrayBuffer() });
	const doc = await task.promise;
	try {
		const pages: Line[][] = [];
		for (let n = 1; n <= doc.numPages; n++) {
			const content = await (await doc.getPage(n)).getTextContent();
			pages.push(pageLines(content.items.filter((i): i is TextItem => 'str' in i)));
		}

		const all = pages.flat();
		if (!all.length) throw new ScannedPdfError();

		const sizes = new Map<number, number>();
		for (const l of all) {
			const key = Math.round(l.size * 2) / 2;
			sizes.set(key, (sizes.get(key) ?? 0) + l.text.length);
		}
		const body = [...sizes.entries()].sort((a, b) => b[1] - a[1])[0][0];
		const heading = (l: Line) => l.size > body * 1.15 && l.text.length < 90;
		const biggest = Math.max(...all.map((l) => l.size));

		const margin = Math.min(...all.map((l) => l.x));
		const toMarkdown = (l: Line) => {
			if (heading(l)) return `\n${l.size >= biggest ? '#' : '##'} ${l.text}\n`;
			const text = l.text.replace(/^[•◦▪‣·-]\s*/, '');
			return text !== l.text || l.x > margin + body ? `- ${text}` : text;
		};
		const pageMarkdown = (lines: Line[]) => {
			const out: string[] = [];
			let tableCols = 0;
			for (const l of lines) {
				const row = !heading(l) && l.cells.length >= 2;
				if (row && (!tableCols || tableCols === l.cells.length)) {
					if (!tableCols) {
						tableCols = l.cells.length;
						out.push('', `| ${l.cells.join(' | ')} |`, `|${' --- |'.repeat(tableCols)}`);
					} else out.push(`| ${l.cells.join(' | ')} |`);
					continue;
				}
				if (tableCols) out.push('');
				tableCols = 0;
				out.push(toMarkdown(l));
			}
			return out.join('\n');
		};
		const text = pages
			.map(pageMarkdown)
			.join('\n\n')
			.replace(/\n{3,}/g, '\n\n')
			.trim();
		return { text, pages: doc.numPages };
	} finally {
		await task.destroy();
	}
}
