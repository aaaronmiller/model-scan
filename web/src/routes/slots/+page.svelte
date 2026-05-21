<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { api } from '$lib/api';

	let slots = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try { slots = await api('/api/v1/slots'); }
		catch {} finally { loading = false; }
	});
</script>

<div class="space-y-4">
	<h2 class="text-xl font-semibold" in:fade>Slots</h2>
	<p class="text-sm text-muted-fg">Each slot is a role in ~/.hermes/config.yaml with specific requirements</p>

	{#if loading}
		<div class="h-48 bg-muted rounded-xl animate-pulse"></div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" in:fly={{ y: 10, duration: 300, delay: 50 }}>
			{#each slots as slot}
				<a href="/slots/{slot.slot_id}"
					class="rounded-xl border bg-card p-4 hover:shadow-md transition-all duration-200 hover:-translate-y-0.5">
					<div class="flex items-center justify-between mb-3">
						<h3 class="font-semibold">{slot.slot_id}</h3>
						{#if slot.incumbent}
							<span class="text-xs text-green-500">✓ active</span>
						{/if}
					</div>
					{#if slot.incumbent}
						<div class="text-sm">
							<div class="text-muted-fg">Current: <span class="text-fg font-medium">{slot.incumbent.model_id}</span></div>
							<div class="text-muted-fg text-xs mt-1">{slot.incumbent.provider}</div>
						</div>
					{:else}
						<p class="text-sm text-muted-fg">No incumbent assigned</p>
					{/if}
				</a>
			{/each}
		</div>
	{/if}
</div>
