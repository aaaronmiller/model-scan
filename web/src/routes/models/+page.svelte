<script lang="ts">
	import { onMount } from 'svelte';
	import { api, tierColor, fmtTps, fmtLat, fmtPrice } from '$lib/api';
	import gsap from 'gsap';

	let models = $state<any[]>([]);
	let loading = $state(true);
	let search = $state('');
	let sortCol = $state('composite');
	let sortDir = $state<'asc'|'desc'>('desc');
	let filterProvider = $state('');
	let filterTier = $state('');
	let activePreset = $state('all');
	let tableEl = $state<HTMLElement | null>(null);
	let presetsEl = $state<HTMLElement | null>(null);

	const presets = [
		{ id: 'all', label: 'All Models', icon: '📊' },
		{ id: 'free', label: 'Free Only', icon: '🆓' },
		{ id: 'best_value', label: 'Best Value', icon: '💎' },
		{ id: 'agent_ready', label: 'Agent Ready', icon: '🤖' },
		{ id: 's_tier', label: 'S-Tier', icon: '👑' },
		{ id: 'deepseek', label: 'DeepSeek Fleet', icon: '🧊' },
	];

	onMount(async () => {
		try { models = await api('/api/v1/models?limit=200'); }
		catch {} finally { loading = false; }
	});

	$effect(() => {
		if (!loading && presetsEl && presetsEl.querySelectorAll('.preset-btn').length > 0) {
			gsap.fromTo(presetsEl.querySelectorAll('.preset-btn'),
				{ opacity: 0, y: -8 },
				{ opacity: 1, y: 0, duration: 0.3, stagger: 0.05, ease: 'power2.out' }
			);
		}
	});

	function setPreset(id: string) {
		activePreset = id;
		filterProvider = '';
		filterTier = '';
		if (id === 's_tier') filterTier = 'S';
		else if (id === 'free') { /* free-filter handled in filtered derived */ }
		else if (id === 'best_value') { sortCol = 'composite'; sortDir = 'desc'; }
		else if (id === 'agent_ready') { sortCol = 'composite'; sortDir = 'desc'; }
		else if (id === 'deepseek') { search = 'deepseek'; }
		else { search = ''; sortCol = 'composite'; sortDir = 'desc'; }
	}

	let providers = $derived([...new Set(models.map(m => m.provider).filter(Boolean))]);
	let tiers = $derived([...new Set(models.map(m => m.tier).filter(Boolean))]);

	let filtered = $derived(() => {
		let list = [...models];
		// Search
		if (search) { const q = search.toLowerCase(); list = list.filter(m => (m.model_id || m.model || '').toLowerCase().includes(q) || (m.provider || '').toLowerCase().includes(q)); }
		// Provider filter
		if (filterProvider) list = list.filter(m => m.provider === filterProvider);
		// Tier filter
		if (filterTier) list = list.filter(m => m.tier === filterTier);
		// Free-mode preset
		if (activePreset === 'free') {
			list = list.filter(m => {
				const mid = (m.model_id || m.model || '').toLowerCase();
				return mid.includes(':free') || mid.includes('-free') || ['groq','cerebras'].includes((m.provider||'').toLowerCase());
			});
		}
		// Agent-ready: has tools + reasoning capability
		if (activePreset === 'agent_ready') {
			list = list.filter(m => m.has_tools && m.tier && ['S','A'].includes(m.tier));
		}
		// Sort
		list.sort((a, b) => {
			if (activePreset === 'best_value') {
				const aCAI = (a.ai_index ?? 0) / Math.max((a.price_blended ?? 0.01), 0.01);
				const bCAI = (b.ai_index ?? 0) / Math.max((b.price_blended ?? 0.01), 0.01);
				return bCAI - aCAI;
			}
			const aV = a[sortCol] ?? 0, bV = b[sortCol] ?? 0;
			return sortDir === 'desc' ? (bV > aV ? 1 : -1) : (aV > bV ? 1 : -1);
		});
		return list;
	}) as any;

	function toggleSort(col: string) {
		if (sortCol === col) sortDir = sortDir === 'desc' ? 'asc' : 'desc';
		else { sortCol = col; sortDir = 'desc'; }
	}

	function sortArrow(col: string) {
		return sortCol === col ? (sortDir === 'desc' ? ' ↓' : ' ↑') : '';
	}

	function provTag(provider: string) {
		const tags: Record<string,string> = { 'openrouter':'🔄','opencode-go':'🔵','opencode-zen':'🟢','kilo':'⚡','nvidia':'💚','groq':'⚪','cerebras':'🔶','ollama-cloud':'☁️','venice':'🎭' };
		return tags[provider?.toLowerCase()] || '';
	}

	function provenanceIcon(m: any): string {
		const hasBench = m.benchmark_swe_verified && m.benchmark_swe_verified > 0;
		const hasProbe = m.tps && m.tps > 0;
		const hasAA = m.ai_index && m.ai_index > 0;
		const parts: string[] = [];
		if (hasProbe) parts.push('🔬');
		if (hasAA) parts.push('📊');
		if (hasBench) parts.push('📈');
		return parts.join(' ') || '—';
	}

	$effect(() => {
		if (!loading && tableEl && tableEl.querySelectorAll('tbody tr').length > 0) {
			gsap.fromTo(tableEl.querySelectorAll('tbody tr'),
				{ opacity: 0, y: 8 },
				{ opacity: 1, y: 0, duration: 0.3, stagger: 0.015, ease: 'power2.out' }
			);
		}
	});
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-display font-bold tracking-tight">Models</h1>
			<p class="text-sm text-muted-fg mt-0.5">{models.length} total models</p>
		</div>
	</div>

	<!-- Preset Filters -->
	<div bind:this={presetsEl} class="flex gap-2 flex-wrap">
		{#each presets as p}
			<button onclick={() => setPreset(p.id)}
				class={"preset-btn px-3 py-1.5 rounded-lg text-sm font-medium font-display transition-all duration-150 " + (activePreset === p.id ? "bg-primary/10 text-primary" : "bg-muted hover:bg-accent")}>
				{p.icon} {p.label}
			</button>
		{/each}
	</div>

	<div class="flex gap-3 flex-wrap">
		<input type="search" bind:value={search} placeholder="Search models..." class="input max-w-xs" />
		<select bind:value={filterProvider} class="input max-w-[160px]"><option value="">All providers</option>{#each providers as p}<option>{p}</option>{/each}</select>
		<select bind:value={filterTier} class="input max-w-[120px]"><option value="">All tiers</option>{#each tiers as t}<option>{t}</option>{/each}</select>
	</div>

	{#if loading}
		<div class="h-64 skeleton"></div>
	{:else}
		<div bind:this={tableEl} class="card overflow-hidden">
			<table class="w-full">
				<thead>
					<tr>
						<th class="cursor-pointer hover:text-fg" onclick={() => toggleSort('tier')}>Tier{sortArrow('tier')}</th>
						<th class="cursor-pointer hover:text-fg" onclick={() => toggleSort('model_id')}>Model{sortArrow('model_id')}</th>
						<th class="cursor-pointer hover:text-fg" onclick={() => toggleSort('provider')}>Provider{sortArrow('provider')}</th>
						<th class="cursor-pointer hover:text-fg" onclick={() => toggleSort('tps')}>TPS{sortArrow('tps')}</th>
						<th class="cursor-pointer hover:text-fg" onclick={() => toggleSort('latency_s')}>Latency{sortArrow('latency_s')}</th>
						<th>Tools</th><th>Vision</th>
						<th class="cursor-pointer hover:text-fg" onclick={() => toggleSort('price_blended')}>Price{sortArrow('price_blended')}</th>
						<th class="cursor-pointer hover:text-fg" onclick={() => toggleSort('ai_index')}>AA{sortArrow('ai_index')}</th>
						<th>Data</th>
					</tr>
				</thead>
				<tbody>
					{#each filtered as m}
						<tr class="cursor-pointer" onclick={() => location.href = `/models/${encodeURIComponent(m.model_id || m.model)}`}>
							<td><span class="badge badge-{(m.tier || 'default').toLowerCase()}">{m.tier || '—'}</span></td>
							<td class="font-medium">{m.model_id || m.model}</td>
							<td class="text-muted-fg">{provTag(m.provider)} {m.provider || '—'}</td>
							<td class="font-mono text-xs">{fmtTps(m.tps)}</td>
							<td class="font-mono text-xs">{fmtLat(m.latency_s)}</td>
							<td class="text-center">{m.has_tools ? '✓' : '·'}</td>
							<td class="text-center">{m.has_vision_capability ? '✓' : '·'}</td>
							<td class="font-mono text-xs">{fmtPrice(m.price_blended)}</td>
							<td class="font-mono text-xs">{m.ai_index ?? '~'}</td>
							<td class="text-xs text-muted-fg" title="🔬=live probe 📊=AA benchmark 📈=verified bench">{provenanceIcon(m)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
