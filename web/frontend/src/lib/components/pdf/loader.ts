import type { PDFDocumentProxy } from 'pdfjs-dist';

type PdfJs = typeof import('pdfjs-dist');

let pdfjsPromise: Promise<PdfJs> | null = null;
const documents = new Map<string, Promise<PDFDocumentProxy>>();

export function loadPdfJs(): Promise<PdfJs> {
	pdfjsPromise ??= Promise.all([
		import('pdfjs-dist'),
		import('pdfjs-dist/build/pdf.worker.min.mjs?url'),
	]).then(([pdfjs, worker]) => {
		pdfjs.GlobalWorkerOptions.workerSrc = worker.default;
		return pdfjs;
	});
	return pdfjsPromise;
}

export function loadDocument(url: string): Promise<PDFDocumentProxy> {
	let doc = documents.get(url);
	if (!doc) {
		doc = loadPdfJs().then((pdfjs) => pdfjs.getDocument({ url }).promise);
		doc.catch(() => documents.delete(url));
		documents.set(url, doc);
	}
	return doc;
}
