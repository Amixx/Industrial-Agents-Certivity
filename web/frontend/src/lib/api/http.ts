import type {
	ApiClient,
	AskAnswer,
	Assessment,
	Brief,
	CitedRegulation,
	PipelineEvent,
	ReadAloud,
	UpdateRun,
} from './types.ts';
import { UpdateRefusal } from './types.ts';

async function json<T>(res: Response): Promise<T> {
	if (!res.ok) {
		const body = await res.json().catch(() => null);
		throw new Error(body?.detail ?? `${res.status} ${res.statusText}`);
	}
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
				if (event.step === 'failed') throw new Error(event.message);
				id = event.assessmentId ?? id;
				onEvent(event);
			}
		}
		if (!id) throw new Error('The server closed the run before it finished');
		return json<Assessment>(await fetch(`/api/assessments/${id}`));
	},
	async listAssessments() {
		return json<Assessment[]>(await fetch('/api/assessments'));
	},
	async getAssessment(id) {
		const res = await fetch(`/api/assessments/${id}`);
		return res.status === 404 ? null : json<Assessment>(res);
	},
	async listUpdates(id) {
		return json<CitedRegulation[]>(await fetch(`/api/assessments/${id}/updates`));
	},
	async createUpdate(id, request, toVersion) {
		const body = new FormData();
		if ('file' in request) body.set('file', request.file);
		else body.set('regulation', request.regulation);
		if (toVersion) body.set('to_version', toVersion);
		const res = await fetch(`/api/assessments/${id}/updates`, { method: 'POST', body });
		if (res.status === 422) {
			const refusal = await res.json();
			throw new UpdateRefusal(refusal.detail, refusal.code, refusal.regulation, refusal.version);
		}
		return json<UpdateRun>(res);
	},
	async getUpdate(id, run) {
		const res = await fetch(`/api/assessments/${id}/updates/${encodeURIComponent(run)}`);
		return res.status === 404 ? null : json<UpdateRun>(res);
	},
	async applyUpdate(id, run) {
		const url = `/api/assessments/${id}/updates/${encodeURIComponent(run)}/apply`;
		return json<Assessment>(await fetch(url, { method: 'POST' }));
	},
	async undoUpdate(id, run) {
		const url = `/api/assessments/${id}/updates/${encodeURIComponent(run)}/undo`;
		return json<Assessment>(await fetch(url, { method: 'POST' }));
	},
	async getBrief(requirements, write) {
		const res = await fetch('/api/brief', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ requirements, write }),
		});
		if (!write && res.status === 404) return null;
		return json<Brief>(res);
	},
	async ask(question, selection, requirements) {
		const res = await fetch('/api/ask', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ question, selection, requirements }),
		});
		return json<AskAnswer>(res);
	},
	async read(assessmentId, text) {
		const res = await fetch('/api/read', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ assessmentId, text }),
		});
		return json<ReadAloud>(res);
	},
};
