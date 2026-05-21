<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { api, tierColor, fmtTps, fmtLat, fmtPrice } from '$lib/api';

	let data = $state<any>(null);
	let loading = $state(true);

	onMount(async () => {
		try { data = await api('/api/v1/scan/latest'); }
		catch {} finally { loading = false; }
	});
</script>

<div class="space-y-4">
	<h2 class="text-xl font-semibold" in:fade>Latest Scan</h2>

	{#if loading}
		<div class="h-48 bg-muted rounded-xl animate-pulse"></div>
	{:else if !data || !data.scan}
		<p class="text-muted-fg">No scan data yet</p>
	{:else}
		<div class="rounded-xl border bg-card p-4" in:fly={{ y: 10, duration: 300 }}>
			<div class="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
				<div><span class="text-muted-fg">Scanned at:</span> <span class="font-medium">{new Date(data.scan.scanned_at).toLocaleString()}</span></div>
				<div><span class="text-muted-fg">Models:</span> <span class="font-medium">{data.scan.model_count || data.models?.length || 0}</span></div>
				<div><span class="text-muted-fg">AA:</span> <span class="font-medium">{data.scan.aa_provenance || '—'}</span></div>
				{#if data.scan.duration_s}<div><span class="text-muted-fg">Duration:</span> <span class="font-medium">{data.scan.duration_s.toFixed(1)}s</span></div>{/if}
			</div>
		</div>

		{#if data.models?.length}
			<div class="rounded-xl border bg-card overflow-hidden" in:fly={{ y: 10, duration: 300, delay: 50 }}>
				<table class="w-full text-sm">
					<thead><tr class="border-b bg-muted/50">
						<th class="text-left py-2 px-3 text-muted-fg">Tier</th>
						<th class="text-left py-2 px-3 text-muted-fg">Model</th>
						<th class="text-left py-2 px-3 text-muted-fg">Provider</th>
						<th class="text-left py-2 px-3 text-muted-fg">TPS</th>
						<th class="text-left py-2 px-3 text-muted-fg">Lat</th>
						<th class="text-left py-2 px-3 text-muted-fg">Price</th>
					</tr></thead>
					<tbody>
						{#each data.models.slice(0, 50) as m, i}
							<tr class="border-b last:border-0 hover:bg-accent/30 transition-colors"
								style="animation: fadeIn 0.2s ease-out {i * 0.01}s both;">
								<td class="py-2 px-3"><span class={tierColor(m.tier)}>{m.tier || '—'}</span></td>
								<td class="py-2 px-3 font-medium truncate max-w-[200px]">{m.model_id || m.model || '—'}</td>
								<td class="py-2 px-3 text-muted-fg">{m.provider || '—'}</td>
								<td class="py-2 px-3">{fmtTps(m.tps)}</td>
								<td class="py-2 px-3">{fmtLat(m.latency_s)}</td>
								<td class="py-2 px-3">{fmtPrice(m.price_blended)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	{/if}
</div>

<style>
	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(4px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
