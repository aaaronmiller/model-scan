<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { api, fmtTps, fmtLat, fmtPrice } from '$lib/api';
	import { Radar } from 'svelte-chartjs';

	let searchTerm = $state('');
	let allModels = $state<any[]>([]);
	let selected = $state<any[]>([]);
	let suggestions = $state<any[]>([]);
	let loading = $state(true);

	const metrics = [
		{ label: 'TPS', fn: (m: any) => fmtTps(m.tps) },
		{ label: 'Latency', fn: (m: any) => fmtLat(m.latency_s) },
		{ label: 'Price', fn: (m: any) => fmtPrice(m.price_blended) },
		{ label: 'Tools', fn: (m: any) => m.has_tools ? '✓' : '·' },
		{ label: 'Vision', fn: (m: any) => m.has_vision_capability ? '✓' : '·' },
		{ label: 'Tier', fn: (m: any) => m.tier || '—' },
	];

	const colors = [
		'rgba(59, 130, 246, 0.7)',   // blue
		'rgba(16, 185, 129, 0.7)',   // green
		'rgba(245, 158, 11, 0.7)',   // amber
		'rgba(139, 92, 246, 0.7)',   // purple
		'rgba(236, 72, 153, 0.7)',   // pink
	];

	onMount(async () => {
		try { allModels = await api('/api/v1/models?limit=200'); }
		catch {} finally { loading = false; }
	});

	function onSearchInput() {
		if (!searchTerm || searchTerm.length < 2) { suggestions = []; return; }
		const q = searchTerm.toLowerCase();
		suggestions = allModels.filter(m => (m.model_id || m.model || '').toLowerCase().includes(q) && !selected.find(s => s.model_id === m.model_id));
	}

	function addModel(m: any) {
		if (selected.length >= 5 || selected.find(s => s.model_id === m.model_id)) return;
		selected = [...selected, m];
		searchTerm = '';
		suggestions = [];
	}

	function removeModel(idx: number) {
		selected = selected.filter((_, i) => i !== idx);
	}

	const chartData = $derived({
		labels: ['Intelligence', 'Speed', 'Agentic', 'Coding', 'Cost'],
		datasets: selected.map((m, i) => ({
			label: m.model_id || m.model || `Model ${i + 1}`,
			data: [
				m.ai_index ?? 50,
				Math.min(100, (m.tps ?? 30) * 1.5),
				m.has_tools ? 75 : 30,
				m.ai_coding ?? 50,
				m.price_blended ? Math.max(10, 100 - m.price_blended * 20) : 50,
			],
			backgroundColor: colors[i % colors.length].replace('0.7', '0.12'),
			borderColor: colors[i % colors.length],
			borderWidth: 2,
			pointRadius: 3,
		})),
	});
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between" in:fade>
		<h2 class="text-xl font-semibold">Compare Models</h2>
		{#if selected.length >= 2}
			<button onclick={() => { const canvas = document.querySelector('canvas'); if(canvas){const a=document.createElement('a');a.href=canvas.toDataURL();a.download='model-compare.png';a.click()}}}
				class="px-3 py-1.5 rounded-lg border bg-card text-sm hover:bg-accent active:scale-95">Export PNG</button>
		{/if}
	</div>

	<div class="relative" in:fly={{ y: 8, duration: 250 }}>
		<input type="text" bind:value={searchTerm} oninput={onSearchInput} placeholder="Search models to add (up to 5)..."
			class="w-full px-3 py-2 rounded-lg border bg-card text-sm outline-none focus:ring-2 focus:ring-primary/20" />
		{#if suggestions.length > 0}
			<div class="absolute z-10 w-full mt-1 rounded-lg border bg-card shadow-lg max-h-48 overflow-y-auto">
				{#each suggestions as m}
					<button onclick={() => addModel(m)}
						class="w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors">{m.model_id || m.model}</button>
				{/each}
			</div>
		{/if}
	</div>

	{#if selected.length > 0}
		<div class="flex gap-2 flex-wrap" in:fade>
			{#each selected as m, i}
				<span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border"
					style="border-color: {colors[i % colors.length]}">
					<span style="color: {colors[i % colors.length]}">●</span>
					{m.model_id || m.model}
					<button onclick={() => removeModel(i)} class="ml-1 hover:text-red-500">&times;</button>
				</span>
			{/each}
		</div>
	{/if}

	{#if selected.length >= 2}
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<div class="rounded-xl border bg-card p-4" in:fly={{ y: 10, duration: 300, delay: 50 }}>
				<h3 class="font-semibold mb-3">Radar Comparison</h3>
				<div class="h-72"><Radar data={chartData} options={{ responsive: true, maintainAspectRatio: false, scales: { r: { beginAtZero: true, max: 100 } }, plugins: { legend: { position: 'bottom' } } }} /></div>
			</div>
			<div class="rounded-xl border bg-card overflow-hidden" in:fly={{ y: 10, duration: 300, delay: 100 }}>
				<table class="w-full text-sm">
					<thead><tr class="border-b bg-muted/50">
						<th class="text-left py-2 px-3 text-muted-fg">Metric</th>
						{#each selected as m}<th class="text-left py-2 px-3 text-muted-fg">{m.model_id || m.model}</th>{/each}
					</tr></thead>
					<tbody>
						{#each metrics as metric}
							<tr class="border-b last:border-0">
								<td class="py-2 px-3 font-medium">{metric.label}</td>
								{#each selected as m}<td class="py-2 px-3">{metric.fn(m)}</td>{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{:else if !loading}
		<div class="flex flex-col items-center py-20 text-muted-fg" in:fade>
			<span class="text-4xl mb-2">◎</span>
			<p>Search and add at least 2 models to compare</p>
		</div>
	{/if}
</div>
