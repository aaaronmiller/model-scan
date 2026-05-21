<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { api } from '$lib/api';

	let history = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try { history = await api('/api/v1/scan/history'); }
		catch {} finally { loading = false; }
	});
</script>

<div class="space-y-4">
	<h2 class="text-xl font-semibold" in:fade>Scan History</h2>

	{#if loading}
		<div class="h-48 bg-muted rounded-xl animate-pulse"></div>
	{:else if history.length === 0}
		<p class="text-muted-fg">No scans recorded yet</p>
	{:else}
		<div class="rounded-xl border bg-card overflow-hidden" in:fly={{ y: 10, duration: 300, delay: 50 }}>
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b bg-muted/50">
						<th class="text-left py-2.5 px-3 text-muted-fg">Date</th>
						<th class="text-left py-2.5 px-3 text-muted-fg">Models</th>
						<th class="text-left py-2.5 px-3 text-muted-fg">Healthy</th>
						<th class="text-left py-2.5 px-3 text-muted-fg">Degraded</th>
						<th class="text-left py-2.5 px-3 text-muted-fg">Failed</th>
					</tr>
				</thead>
				<tbody>
					{#each history as s}
						<tr class="border-b last:border-0 hover:bg-accent/30 transition-colors">
							<td class="py-2.5 px-3">{new Date(s.scanned_at).toLocaleString()}</td>
							<td class="py-2.5 px-3">{s.model_count || '—'}</td>
							<td class="py-2.5 px-3 text-green-500">{s.healthy ?? '—'}</td>
							<td class="py-2.5 px-3 text-yellow-500">{s.degraded ?? '—'}</td>
							<td class="py-2.5 px-3 text-red-500">{s.failed ?? '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
