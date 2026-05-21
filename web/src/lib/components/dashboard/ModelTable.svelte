<script lang="ts">
	let { models, all = false }: { models: any[]; all?: boolean } = $props();

	let cols = $derived(all
		? ['Tier', 'Model', 'Provider', 'TPS', 'Latency', 'Tools', 'Vision', 'Price']
		: ['Model', 'Provider', 'TPS', 'Latency', 'Tier']);

	const tierColors: Record<string, string> = {
		S: 'text-orange-500 font-bold',
		A: 'text-green-500 font-semibold',
		B: 'text-cyan-500',
		C: 'text-gray-400',
		'—': 'text-gray-600',
	};
</script>

<div class="overflow-x-auto">
	<table class="w-full text-sm">
		<thead>
			<tr class="border-b">
				{#each cols as col}
					<th class="text-left py-2 px-2 text-muted-fg font-medium">{col}</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each models as model, i}
				<tr class="border-b last:border-0 hover:bg-accent/30 transition-colors"
					style="animation: fadeIn 0.2s ease-out {i * 0.03}s both;">
					{#if all}
						<td class="py-2 px-2">
							<span class={tierColors[model.tier] || 'text-gray-400'}>{model.tier || '—'}</span>
						</td>
					{/if}
					<td class="py-2 px-2 font-medium truncate max-w-[200px]" title={model.model_id || model.model}>
						{model.model_id || model.model || '—'}
					</td>
					<td class="py-2 px-2 text-muted-fg">{model.provider || '—'}</td>
					<td class="py-2 px-2">{model.tps ? `${model.tps.toFixed(0)} t/s` : '—'}</td>
					<td class="py-2 px-2">{model.latency_s ? `${model.latency_s.toFixed(2)}s` : '—'}</td>
					{#if all}
						<td class="py-2 px-2">{model.has_tools ? '✓' : '·'}</td>
						<td class="py-2 px-2">{model.has_vision_capability ? '✓' : '·'}</td>
						<td class="py-2 px-2">{model.price_blended != null ? `$${model.price_blended.toFixed(2)}` : '—'}</td>
					{/if}
					{#if !all}
						<td class="py-2 px-2">
							<span class={tierColors[model.tier] || ''}>{model.tier || '—'}</span>
						</td>
					{/if}
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(4px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
