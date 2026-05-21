<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { api } from '$lib/api';

	let patch = $state('');
	let loading = $state(true);

	onMount(async () => {
		try {
			const res = await api('/api/v1/config/preview');
			patch = res.patch || '# No patch available';
		} catch (e: any) {
			patch = `# Error: ${e.message}`;
		} finally { loading = false; }
	});
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between" in:fade>
		<h2 class="text-xl font-semibold">Config Patch Preview</h2>
		<button onclick={() => navigator.clipboard.writeText(patch)}
			class="px-3 py-1.5 rounded-lg border bg-card text-sm hover:bg-accent transition-colors active:scale-95">
			Copy
		</button>
	</div>
	<p class="text-sm text-muted-fg">Recommended changes to ~/.hermes/config.yaml based on latest scan</p>

	{#if loading}
		<div class="h-64 bg-muted rounded-xl animate-pulse"></div>
	{:else}
		<pre class="rounded-xl border bg-card p-4 text-sm font-mono overflow-x-auto" in:fly={{ y: 10, duration: 300, delay: 50 }}>{patch}</pre>
	{/if}
</div>
