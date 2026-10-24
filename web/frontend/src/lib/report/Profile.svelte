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
					<td>{items.length ? items.join(', ') : 'None listed'}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</section>

<style>
th {
	width: 30mm;
	text-align: left;
	vertical-align: top;
	font-weight: 700;
}
th,
td {
	padding: 1.2mm 3mm 1.2mm 0;
	border-bottom: 0.5pt solid rgb(0 0 0 / 0.2);
}
</style>
