<script lang="ts">
	let { models }: { models: any[] } = $props();

	const stats = $derived([
		{ label: 'Models Scanned', value: models.length, icon: '⊞', color: 'text-blue-500' },
		{ label: 'Healthy', value: models.filter(m => (m.reliability ?? 1) >= 0.99).length, icon: '✓', color: 'text-green-500' },
		{ label: 'Degraded', value: models.filter(m => 0.5 <= (m.reliability ?? 1) && (m.reliability ?? 1) < 0.99).length, icon: '⚠', color: 'text-yellow-500' },
		{ label: 'Providers', value: [...new Set(models.map(m => m.provider))].length, icon: '◉', color: 'text-purple-500' },
	]);
</script>

<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
	{#each stats as stat}
		<div class="rounded-xl border bg-card p-4 flex items-center gap-4 hover:shadow-md transition-all duration-200 hover:-translate-y-0.5">
			<div class="text-2xl {stat.color}">{stat.icon}</div>
			<div>
				<div class="text-2xl font-bold">{stat.value}</div>
				<div class="text-xs text-muted-fg">{stat.label}</div>
			</div>
		</div>
	{/each}
</div>
