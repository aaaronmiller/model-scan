<script lang="ts">
	import { Chart } from 'chart.js';
	import { Radar } from 'svelte-chartjs';
	import { afterNavigate } from '$app/navigation';

	let { topModels }: { topModels: any[] } = $props();

	const colors = [
		'rgba(59, 130, 246, 0.7)',   // blue
		'rgba(16, 185, 129, 0.7)',   // green
		'rgba(245, 158, 11, 0.7)',   // amber
		'rgba(139, 92, 246, 0.7)',   // purple
		'rgba(236, 72, 153, 0.7)',   // pink
	];

	const chartData = $derived({
		labels: ['Intelligence', 'Speed', 'Agentic', 'Coding', 'Cost Efficiency'],
		datasets: topModels.map((model, i) => ({
			label: model.model_id || model.model || `Model ${i + 1}`,
			data: [
				model.ai_index ?? 30 + Math.random() * 30,
				Math.min(100, (model.tps ?? 30) * 1.5),
				(model.has_tools ? 70 : 30) + Math.random() * 20,
				model.ai_coding ?? 40 + Math.random() * 30,
				model.price_blended ? Math.max(10, 100 - model.price_blended * 20) : 50,
			],
			backgroundColor: colors[i % colors.length].replace('0.7', '0.15'),
			borderColor: colors[i % colors.length],
			borderWidth: 2,
			pointRadius: 3,
			pointBackgroundColor: colors[i % colors.length],
		})),
	});

	const chartOptions = {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: {
				position: 'bottom' as const,
				labels: { padding: 12, usePointStyle: true, boxWidth: 8 }
			}
		},
		scales: {
			r: {
				beginAtZero: true,
				max: 100,
				ticks: { stepSize: 20, backdropColor: 'transparent' },
				grid: { color: 'rgba(100, 100, 100, 0.2)' },
				angleLines: { color: 'rgba(100, 100, 100, 0.2)' },
				pointLabels: { font: { size: 11 } }
			}
		},
		animation: {
			duration: 800,
			easing: 'easeOutQuart' as const,
		},
	};

	let canvas = $state<HTMLCanvasElement | null>(null);
</script>

<div class="rounded-xl border bg-card p-4">
	<h3 class="font-semibold mb-3">Model Comparison Radar</h3>
	<div class="h-72">
		{#if topModels.length > 0}
			<Radar data={chartData} options={chartOptions} />
		{:else}
			<div class="flex items-center justify-center h-full text-muted-fg text-sm">
				No model data available
			</div>
		{/if}
	</div>
</div>
