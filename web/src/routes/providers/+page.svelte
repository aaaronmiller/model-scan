<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { api } from '$lib/api';

	let providers = $state<any[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try { providers = await api('/api/v1/providers'); }
		catch {} finally { loading = false; }
	});
</script>

<div class="space-y-4">
	<h2 class="text-xl font-semibold" in:fade>Providers</h2>

	{#if loading}
		<div class="h-32 bg-muted rounded-xl animate-pulse"></div>
	{:else if providers.length === 0}
		<p class="text-muted-fg">No provider data available</p>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" in:fly={{ y: 10, duration: 300, delay: 50 }}>
			{#each providers as p}
				<div class="rounded-xl border bg-card p-4 hover:shadow-md transition-all duration-200">
					<div class="flex items-center justify-between mb-3">
						<h3 class="font-semibold">{p.provider}</h3>
						<span class="w-3 h-3 rounded-full"
							class:bg-green-500={Number(p.accessible) > 0}
							class:bg-yellow-500={Number(p.accessible) === 0}
							class:bg-red-500={!p.accessible}>
						</span>
					</div>
					<div class="text-sm space-y-1 text-muted-fg">
						<div>Models: <span class="text-fg font-medium">{p.model_count}</span></div>
						<div>Accessible: <span class="text-fg font-medium">{p.accessible || 0}</span></div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
