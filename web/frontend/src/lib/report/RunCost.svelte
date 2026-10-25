<script lang="ts">
import type { RunCost } from '#lib/api/types.ts';
import { modelName, usd } from './cost.ts';

let { cost }: { cost: RunCost } = $props();

const n = (value: number) => value.toLocaleString('en-GB');
const sum = (key: 'calls' | 'input' | 'output' | 'cacheRead') =>
	cost.models.reduce((total, m) => total + m[key], 0);
</script>

<section>
	<h2>Run cost</h2>
	{#if cost.models.length}
		<table class="cost">
			<thead>
				<tr>
					<th>Model</th>
					<th class="num">Calls</th>
					<th class="num">Input tokens</th>
					<th class="num">Output tokens</th>
					<th class="num">Cached input</th>
					<th class="num">Cost</th>
				</tr>
			</thead>
			<tbody>
				{#each cost.models as m (m.model)}
					<tr>
						<td class="strong">{modelName(m.model)}</td>
						<td class="num">{n(m.calls)}</td>
						<td class="num">{n(m.input + m.cacheWrite)}</td>
						<td class="num">{n(m.output)}</td>
						<td class="num">{n(m.cacheRead)}</td>
						<td class="num">{usd(m.costUsd)}</td>
					</tr>
				{/each}
				<tr class="total">
					<td class="strong">Total</td>
					<td class="num">{n(sum('calls'))}</td>
					<td class="num">{n(cost.models.reduce((t, m) => t + m.input + m.cacheWrite, 0))}</td>
					<td class="num">{n(sum('output'))}</td>
					<td class="num">{n(sum('cacheRead'))}</td>
					<td class="num strong">{usd(cost.totalUsd)}</td>
				</tr>
			</tbody>
		</table>
		<p class="note">
			Anthropic API list prices. The brief and spoken answers are billed separately.
		</p>
	{:else}
		<p class="note">This run used no model, so it cost nothing.</p>
	{/if}
</section>

<style>
.cost {
	width: 100%;
	border-collapse: collapse;
	font-size: 10pt;
}
th {
	text-align: left;
	font-size: 8pt;
	font-weight: 700;
	border-bottom: 1.5pt solid black;
}
th,
td {
	padding: 1.2mm 3mm 1.2mm 0;
}
td {
	border-bottom: 0.5pt solid rgb(0 0 0 / 0.2);
	font-variant-numeric: tabular-nums;
}
.num {
	text-align: right;
}
.strong {
	font-weight: 700;
}
.total td {
	border-top: 1pt solid black;
	border-bottom: none;
}
.note {
	margin-top: 2mm;
	font-size: 8.5pt;
}
</style>
