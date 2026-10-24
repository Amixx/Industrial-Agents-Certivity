<script lang="ts">
import type { RegulationDecision } from '#lib/api/types.ts';

let { regulations }: { regulations: RegulationDecision[] } = $props();

const applied = $derived(regulations.filter((r) => r.included));
const excluded = $derived(regulations.filter((r) => !r.included));
</script>

<section>
	<h2>Regulations applied</h2>
	<table class="reg">
		<thead>
			<tr>
				<th>Regulation</th>
				<th>Title</th>
				<th>Version</th>
				<th class="num">Requirements</th>
			</tr>
		</thead>
		<tbody>
			{#each applied as r (r.regulation)}
				<tr>
					<td class="strong">{r.regulation}</td>
					<td>{r.title}</td>
					<td>{r.version}</td>
					<td class="num">{r.requirementCount}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

{#if excluded.length}
	<section>
		<h2>Regulations considered and excluded</h2>
		<table class="reg">
			<thead>
				<tr>
					<th>Regulation</th>
					<th>Title</th>
					<th>Reason</th>
				</tr>
			</thead>
			<tbody>
				{#each excluded as r (r.regulation)}
					<tr>
						<td class="strong">{r.regulation}</td>
						<td>{r.title}</td>
						<td>{r.reason}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
{/if}

<style>
.reg {
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
	vertical-align: top;
}
tr {
	break-inside: avoid;
}
td {
	border-bottom: 0.5pt solid rgb(0 0 0 / 0.2);
}
.strong {
	font-weight: 700;
	white-space: nowrap;
}
.num {
	text-align: right;
	padding-right: 0;
	font-variant-numeric: tabular-nums;
}
td.num {
	font-size: 16pt;
	font-weight: 300;
	line-height: 1;
	color: var(--color-cv-teal-700);
}
</style>
