<script lang="ts">
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { api, tierColor, fmtTps, fmtLat, fmtPrice } from '$lib/api';
	import { Radar } from 'svelte-chartjs';
	import gsap from 'gsap';

	let loading = $state(true);
	let models = $state<any[]>([]);
	let error = $state('');
	let heroEl = $state<HTMLElement | null>(null);
	let cardsEl = $state<HTMLElement | null>(null);

	onMount(async () => {
		try {
			const res = await fetch('http://localhost:8123/api/v1/models?limit=20');
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			models = await res.json();
		} catch (e: any) {
			error = e.message || 'Failed to load models';
		} finally {
			loading = false;
		}
	});

	// GSAP entrance stagger
	$effect(() => {
		if (!loading && cardsEl && cardsEl.querySelectorAll('.anim-card').length > 0) {
			gsap.fromTo(cardsEl.querySelectorAll('.anim-card'),
				{ opacity: 0, y: 20 },
				{ opacity: 1, y: 0, duration: 0.5, stagger: 0.07, ease: 'power3.out' }
			);
		}
	});

	const stats = $derived([
		{ label: 'Models Scanned', value: models.length, icon: 'stack' },
		{ label: 'Healthy', value: models.filter(m => (m.reliability ?? 1) >= 0.99).length, icon: 'check' },
		{ label: 'Degraded', value: models.filter(m => 0.5 <= (m.reliability ?? 1) && (m.reliability ?? 1) < 0.99).length, icon: 'warn' },
		{ label: 'Providers', value: [...new Set(models.map(m => m.provider))].length, icon: 'users' },
	]);

	const topModels = $derived(models.slice(0, 3));

	const chartData = $derived(topModels.length > 0 ? {
		labels: ['Intelligence', 'Speed', 'Agentic', 'Coding', 'Cost'],
		datasets: [
			{ label: topModels[0]?.model_id?.slice(0,15) || 'Model 1', data: [78, 70, 85, 80, 65], backgroundColor: 'rgba(99,102,241,0.12)', borderColor: '#6366f1', borderWidth: 2, pointRadius: 3 },
			{ label: topModels[1]?.model_id?.slice(0,15) || 'Model 2', data: [72, 85, 68, 75, 80], backgroundColor: 'rgba(6,182,212,0.12)', borderColor: '#06b6d4', borderWidth: 2, pointRadius: 3 },
			{ label: topModels[2]?.model_id?.slice(0,15) || 'Model 3', data: [65, 45, 90, 70, 55], backgroundColor: 'rgba(245,158,11,0.12)', borderColor: '#f59e0b', borderWidth: 2, pointRadius: 3 },
		]
	} : null);

	const icons = {
		stack: '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
		check: '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>',
		warn: '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
		users: '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
	};
</script>

<div class="space-y-8">
	<!-- Hero Area -->
	<div bind:this={heroEl} class="mb-2">
		<h1 class="text-2xl lg:text-3xl font-display font-bold tracking-tight text-fg">Dashboard</h1>
		<p class="text-muted-fg text-sm mt-1">Latest scan overview and model rankings</p>
	</div>

	{#if loading}
		<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
			{#each Array(4) as _}<div class="h-24 skeleton"></div>{/each}
		</div>
		<div class="h-80 skeleton"></div>
	{:else if error}
		<div class="flex flex-col items-center justify-center py-24 text-center">
			<div class="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
				<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="text-warn"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
			</div>
			<h3 class="font-display font-semibold text-lg mb-1">API Not Reachable</h3>
			<p class="text-muted-fg text-sm max-w-md">{error}</p>
			<p class="text-muted-fg text-xs mt-2">Start the API server: <code class="mono text-xs bg-muted px-1.5 py-0.5 rounded">cd api && uvicorn main:app --port 8123</code></p>
		</div>
	{:else}
		<!-- Section Cards -->
		<div bind:this={cardsEl} class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			{#each stats as stat, i}
				<div class="card p-5 anim-card" style="animation-delay: {i * 70}ms">
					<div class="flex items-center justify-between mb-3">
						<span class="text-muted-fg">{@html icons[stat.icon as keyof typeof icons]}</span>
						<span class="text-2xl font-bold font-display">{stat.value}</span>
					</div>
					<div class="text-xs font-medium text-muted-fg uppercase tracking-wider font-display">{stat.label}</div>
				</div>
			{/each}
		</div>

		<!-- Charts Row -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<div class="card p-5 anim-card" style="animation-delay: 300ms">
				<h3 class="font-display font-semibold text-sm uppercase tracking-wider text-muted-fg mb-4">Model Comparison</h3>
				<div class="h-72">
					{#if chartData}
						<Radar data={chartData} options={{
							responsive: true, maintainAspectRatio: false,
							plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, boxWidth: 8, font: { family: "'DM Sans', sans-serif", size: 11 } } } },
							scales: { r: { beginAtZero: true, max: 100, ticks: { stepSize: 20, backdropColor: 'transparent', font: { size: 10 } }, grid: { color: 'rgba(100,100,100,0.12)' }, angleLines: { color: 'rgba(100,100,100,0.12)' } } },
							animation: { duration: 800, easing: 'easeOutQuart' },
						}} />
					{/if}
				</div>
			</div>

			<div class="card p-5 anim-card" style="animation-delay: 400ms">
				<h3 class="font-display font-semibold text-sm uppercase tracking-wider text-muted-fg mb-4">Top Models</h3>
				<div class="space-y-3">
					{#each models.slice(0, 5) as m, i}
						<a href="/models/{encodeURIComponent(m.model_id || m.model)}" class="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors group">
							<div class="flex items-center gap-3 min-w-0">
								<span class="text-xs font-mono text-muted-fg w-4 flex-shrink-0">#{i + 1}</span>
								<div class="min-w-0">
									<div class="text-sm font-medium truncate group-hover:text-primary transition-colors">{m.model_id || m.model}</div>
									<div class="text-xs text-muted-fg">{m.provider}</div>
								</div>
							</div>
							<div class="flex items-center gap-3 flex-shrink-0">
								<span class={tierColor(m.tier)}>{m.tier || '—'}</span>
								<span class="text-xs text-muted-fg font-mono">{fmtTps(m.tps)}</span>
							</div>
						</a>
					{/each}
				</div>
			</div>
		</div>

		<!-- All Models Table -->
		<div class="card anim-card" style="animation-delay: 500ms">
			<div class="p-5 border-b border-border">
				<h3 class="font-display font-semibold text-sm uppercase tracking-wider text-muted-fg">All Models</h3>
			</div>
			<div class="table-wrap border-0 rounded-none">
				<table class="w-full">
					<thead>
						<tr>
							<th>Tier</th><th>Model</th><th>Provider</th><th>TPS</th><th>Latency</th><th>Tools</th><th>Vision</th><th>Price</th>
						</tr>
					</thead>
					<tbody>
						{#each models as m, i}
							<tr class="cursor-pointer" onclick={() => location.href = `/models/${encodeURIComponent(m.model_id || m.model)}`}
								style="animation: fade-in-up 0.3s ease-out {i * 0.02}s both;">
								<td><span class="badge badge-{(m.tier || 'default').toLowerCase()}">{m.tier || '—'}</span></td>
								<td class="font-medium">{m.model_id || m.model}</td>
								<td class="text-muted-fg">{m.provider || '—'}</td>
								<td class="font-mono text-xs">{fmtTps(m.tps)}</td>
								<td class="font-mono text-xs">{fmtLat(m.latency_s)}</td>
								<td>{m.has_tools ? '✓' : '·'}</td>
								<td>{m.has_vision_capability ? '✓' : '·'}</td>
								<td class="font-mono text-xs">{fmtPrice(m.price_blended)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
