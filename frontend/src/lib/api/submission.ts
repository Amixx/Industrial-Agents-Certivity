import type { Assessment, Submission } from './types.ts';

export const TEAM_ID = 'team-00';

export function toSubmission(assessment: Assessment): Submission {
	return {
		team_id: TEAM_ID,
		case_id: assessment.caseName ?? assessment.id,
		requirements: assessment.requirements.map(({ id, text, source }) => ({ id, text, source }))
	};
}

export function downloadSubmission(assessment: Assessment) {
	const blob = new Blob([JSON.stringify(toSubmission(assessment), null, 2)], {
		type: 'application/json'
	});
	const a = document.createElement('a');
	a.href = URL.createObjectURL(blob);
	a.download = `${assessment.caseName ?? assessment.id}.json`;
	a.click();
	URL.revokeObjectURL(a.href);
}
