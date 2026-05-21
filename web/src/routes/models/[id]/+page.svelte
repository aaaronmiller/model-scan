<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { fade, fly } from 'svelte/transition';
	import { api, tierColor, fmtTps, fmtLat, fmtPrice } from '$lib/api';
	import { Chart } from 'chart.js';
	import { Radar } from 'svelte-chartjs';

	let model = $state<any>(null);
	let loading = $state(true);
	let error = $state('');

	let modelId = $derived($page.params.id);

	onMount(async () => {
		if (!modelId) { error = 'No model ID'; loading = false; return; }
		try {
			model = await api(`/api/v1/models/${encodeURIComponent(modelId)}`);
		} catch (e: any) {
			error = e.message || 'Failed to load';
		} finally { loading = false; }
	});

	const radarData = $derived(model ? {
		labels: ['Intelligence', 'Speed', 'Agentic', 'Coding', 'Cost'],
		datasets: [{
			label: model.model_id || model.model,
			data: [
				model.ai_index ?? 50,
				Math.min(100, (model.tps ?? 30) * 1.5),
				model.has_tools ? 75 : 30,
				model.ai_coding ?? 50,
				model.price_blended ? Math.max(10, 100 - model.price_blended * 20) : 50,
			],
			backgroundColor: 'rgba(59, 130, 246, 0.15)',
			borderColor: 'rgba(59, 130, 246, 0.8)',
			borderWidth: 2,
		}]
	} : null);
</script>

<div class="space-y-6">
	{#if loading}
		<div class="h-80 bg-muted rounded-xl animate-pulse"></div>
	{:else if error}
		<div class="flex flex-col items-center py-20" in:fade>
			<span class="text-4xl mb-4">⚠</span>
			<p class="text-muted-fg">{error}</p>
		</div>
	{:else if model}
		<div in:fly={{ y: 10, duration: 300 }}>
			<a href="/models" class="text-sm text-muted-fg hover:text-fg">&larr; Back to models</a>
			<div class="flex items-center gap-4 mt-2">
				<h2 class="text-xl font-semibold">{model.model_id || model.model}</h2>
				<span class={tierColor(model.tier) + ' text-sm px-2 py-0.5 rounded bg-muted'}>{model.tier || '—'}</span>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<div class="lg:col-span-2 space-y-4" in:fly={{ y: 10, duration: 300, delay: 100 }}>
				<div class="rounded-xl border bg-card p-4">
					<h3 class="font-semibold mb-3">Radar</h3>
					<div class="h-64">
						{#if radarData}<Radar data={radarData} options={{ responsive: true, maintainAspectRatio: false, scales: { r: { beginAtZero: true, max: 100 } } }} />{/if}
					</div>
				</div>

				<div class="rounded-xl border bg-card p-4">
					<h3 class="font-semibold mb-3">Benchmarks</h3>
					<div class="space-y-2">
						{#if model.benchmark_swe_verified != null}
							<div class="flex justify-between items-center">
								<span class="text-sm text-muted-fg">SWE-Verified</span>
								<span class="font-mono text-sm">{model.benchmark_swe_verified.toFixed(1)}%</span>
							</div>
						{/if}
						{#if model.ai_index != null}
							<div class="flex justify-between items-center">
								<span class="text-sm text-muted-fg">AA Intelligence</span>
								<span class="font-mono text-sm">{model.ai_index}</span>
							</div>
						{/if}
						{#if model.ai_coding != null}
							<div class="flex justify-between items-center">
								<span class="text-sm text-muted-fg">AA Coding</span>
								<span class="font-mono text-sm">{model.ai_coding}</span>
							</div>
						{/if}
					</div>
				</div>
			</div>

			<div class="space-y-4" in:fly={{ y: 10, duration: 300, delay: 200 }}>
				<div class="rounded-xl border bg-card p-4">
					<h3 class="font-semibold mb-3">Details</h3>
					<dl class="space-y-2 text-sm">
						<div class="flex justify-between"><dt class="text-muted-fg">Provider</dt><dd>{model.provider || '—'}</dd></div>
						<div class="flex justify-between"><dt class="text-muted-fg">TPS</dt><dd>{fmtTps(model.tps)}</dd></div>
						<div class="flex justify-between"><dt class="text-muted-fg">Latency</dt><dd>{fmtLat(model.latency_s)}</dd></div>
						<div class="flex justify-between"><dt class="text-muted-fg">Price</dt><dd>{fmtPrice(model.price_blended)}</dd></div>
						<div class="flex justify-between"><dt class="text-muted-fg">Tools</dt><dd>{model.has_tools ? '✓ Yes' : '· No'}</dd></div>
						<div class="flex justify-between"><dt class="text-muted-fg">Vision</dt><dd>{model.has_vision_capability ? '✓ Yes' : '· No'}</dd></div>
						<div class="flex justify-between"><dt class="text-muted-fg">Arch</dt><dd>{model.arch || '—'}</dd></div>
						<div class="flex justify-between"><dt class="text-muted-fg">Reliability</dt><dd>{model.reliability != null ? `${(model.reliability * 100).toFixed(0)}%` : '—'}</dd></div>
					</dl>
				</div>
			</div>
		</div>
	{/if}
</div>
