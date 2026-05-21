<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { fade, fly } from 'svelte/transition';
	import { api, tierColor, fmtTps, fmtLat } from '$lib/api';

	let slot = $state<any>(null);
	let loading = $state(true);
	let slotId = $derived($page.params.id);

	onMount(async () => {
		if (!slotId) return;
		try { slot = await api(`/api/v1/slots/${encodeURIComponent(slotId)}`); }
		catch {} finally { loading = false; }
	});
</script>

<div class="space-y-4">
	<a href="/slots" class="text-sm text-muted-fg hover:text-fg">&larr; Back to slots</a>

	{#if loading}
		<div class="h-64 bg-muted rounded-xl animate-pulse" />
	{:else if !slot}
		<p class="text-muted-fg">Slot not found</p>
	{:else}
		<div in:fly={{ y: 10, duration: 300 }}>
			<div class="flex items-center gap-3 mb-4">
				<h2 class="text-xl font-semibold">{slot.slot_id}</h2>
				{#if slot.incumbent}<span class="text-xs bg-green-500/10 text-green-500 px-2 py-0.5 rounded">✓ incumbent active</span>{/if}
			</div>

			{#if slot.incumbent}
				<div class="rounded-xl border bg-card p-4 mb-6" in:fade>
					<h3 class="font-semibold mb-2">Incumbent</h3>
					<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
						<div><span class="text-muted-fg">Model:</span> {slot.incumbent.model_id}</div>
						<div><span class="text-muted-fg">Provider:</span> {slot.incumbent.provider}</div>
						<div><span class="text-muted-fg">TPS:</span> {fmtTps(slot.incumbent.tps)}</div>
						<div><span class="text-muted-fg">Latency:</span> {fmtLat(slot.incumbent.latency_s)}</div>
					</div>
				</div>
			{/if}

			<div class="rounded-xl border bg-card" in:fly={{ y: 10, duration: 300, delay: 100 }}>
				<h3 class="font-semibold p-4 border-b">Candidates</h3>
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/50">
							<th class="text-left py-2 px-3 text-muted-fg">Rank</th>
							<th class="text-left py-2 px-3 text-muted-fg">Model</th>
							<th class="text-left py-2 px-3 text-muted-fg">Fitness</th>
							<th class="text-left py-2 px-3 text-muted-fg">TPS</th>
							<th class="text-left py-2 px-3 text-muted-fg">Latency</th>
							<th class="text-left py-2 px-3 text-muted-fg">Tier</th>
						</tr>
					</thead>
					<tbody>
						{#each (slot.candidates || []) as m, i}
							<tr class="border-b last:border-0 hover:bg-accent/30 transition-colors"
								style={slot.incumbent && m.model_id === slot.incumbent.model_id ? 'background: rgba(34,197,94,0.08)' : ''}>
								<td class="py-2 px-3 font-mono">#{i + 1}</td>
								<td class="py-2 px-3 font-medium">{m.model_id || m.model}
									{#if slot.incumbent && m.model_id === slot.incumbent.model_id}
										<span class="text-green-500 text-xs ml-1">(current)</span>
									{/if}
								</td>
								<td class="py-2 px-3"><span class="font-mono">{m.fitness?.toFixed(1)}</span></td>
								<td class="py-2 px-3">{fmtTps(m.tps)}</td>
								<td class="py-2 px-3">{fmtLat(m.latency_s)}</td>
								<td class="py-2 px-3"><span class={tierColor(m.tier)}>{m.tier || '—'}</span></td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
