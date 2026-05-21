<script lang="ts">
	let { onToggleDark, onToggleSidebar, darkMode }: {
		onToggleDark: () => void;
		onToggleSidebar: () => void;
		darkMode: boolean;
	} = $props();
</script>

<header class="h-14 border-b border-border flex items-center justify-between px-4 lg:px-6 bg-card">
	<div class="flex items-center gap-3">
		<button onclick={onToggleSidebar}
			class="btn-ghost p-1.5 rounded-lg hover:bg-accent transition-colors active:scale-90"
			aria-label="Toggle sidebar">
			<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
		</button>
	</div>

	<div class="flex items-center gap-2">
		<button onclick={onToggleDark}
			class="btn-ghost p-1.5 rounded-lg hover:bg-accent transition-colors active:scale-90"
			aria-label="Toggle dark mode">
			{#if darkMode}
				<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
			{:else}
				<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
			{/if}
		</button>
	</div>
</header>
