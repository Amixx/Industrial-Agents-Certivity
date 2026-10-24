import type { ApiClient, Assessment, PipelineEvent, RegulationUpdate } from './types.ts';

async function json<T>(res: Response): Promise<T> {
	if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
	return res.json();
}

/** Expects `POST /api/assessments` to stream newline-delimited PipelineEvents. */
export const http: ApiClient = {
	async runAssessment(spec, image, onEvent, caseName) {
		const body = new FormData();
		body.set('spec', spec);
		if (image) body.set('image', image);
		if (caseName) body.set('case_name', caseName);
		const res = await fetch('/api/assessments', { method: 'POST', body });
		if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`);

		const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
		let buffer = '';
		let id: string | undefined;
		for (;;) {
			const { value, done } = await reader.read();
			if (done) break;
			buffer += value;
			const lines = buffer.split('\n');
			buffer = lines.pop() ?? '';
			for (const line of lines.filter(Boolean)) {
				const event: PipelineEvent = JSON.parse(line);
				id = event.assessmentId ?? id;
				onEvent(event);
			}
		}
		if (!id) throw new Error('Pipeline ended without an assessment id');
		return json<Assessment>(await fetch(`/api/assessments/${id}`));
	},
	async listAssessments() {
		return json<Assessment[]>(await fetch('/api/assessments'));
	},
	async getAssessment(id) {
		const res = await fetch(`/api/assessments/${id}`);
		return res.status === 404 ? null : json<Assessment>(res);
	},
	async checkUpdates(id) {
		return json<RegulationUpdate[]>(await fetch(`/api/assessments/${id}/updates`));
	},
	async applyUpdate(id, regulation) {
		const res = await fetch(`/api/assessments/${id}/updates/${encodeURIComponent(regulation)}`, {
			method: 'POST',
		});
		return json<Assessment>(res);
	},
};
