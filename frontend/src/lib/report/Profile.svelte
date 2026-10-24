<script lang="ts">
import type { Profile } from '#lib/api/types.ts';

let { profile }: { profile: Profile } = $props();

const rows = $derived([
	['Parts', profile.parts],
	['Functions', profile.functions],
	['Materials', profile.materials],
] as const);
</script>

<section>
	<h2>Product profile</h2>
	<table>
		<tbody>
			{#each rows as [label, items] (label)}
				<tr>
					<th scope="row">{label}</th>
					<td>{items.length ? items.join(', ') : '—'}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<style>
th {
	width: 7rem;
	text-align: left;
	vertical-align: top;
	font-weight: 600;
	color: var(--color-cv-ink-800);
}
th,
td {
	padding: 0.3rem 0.5rem 0.3rem 0;
	border-bottom: 0.5pt solid var(--color-cv-ink-800);
}
</style>
