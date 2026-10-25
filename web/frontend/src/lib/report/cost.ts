import type { RunCost } from '#lib/api/types.ts';

const NAMES: Record<string, string> = {
	'claude-sonnet-5-5': 'Sonnet 5.5',
	'claude-haiku-5-5': 'Haiku 5.5',
};

export function modelName(model: string): string {
	return NAMES[model] ?? model;
}

export function usd(value: number): string {
	return `$${value.toFixed(value > 0 && value < 0.1 ? 4 : 2)}`;
}

/** One line, e.g. "$2.71: Sonnet 5.5 $2.40, Haiku 5.5 $0.31". */
export function costSummary(cost: RunCost): string {
	if (!cost.models.length) return '$0.00, no model calls';
	const parts = cost.models.map((m) => `${modelName(m.model)} ${usd(m.costUsd)}`);
	return `${usd(cost.totalUsd)}: ${parts.join(', ')}`;
}
