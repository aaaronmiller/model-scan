<script lang="ts">
	import { page } from '$app/stores';
	import gsap from 'gsap';
	import sidebarAccent from '$lib/assets/sidebar-accent.png';

	let { sidebarOpen }: { sidebarOpen: boolean } = $props();

	const navItems = [
		{ href: '/', label: 'Dashboard', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>' },
		{ href: '/models', label: 'Models', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><circle cx="12" cy="12" r="3"/></svg>' },
		{ href: '/slots', label: 'Slots', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/></svg>' },
		{ href: '/compare', label: 'Compare', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>' },
		{ href: '/scan/latest', label: 'Scan', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' },
		{ href: '/scan/history', label: 'History', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' },
		{ href: '/config', label: 'Config', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' },
		{ href: '/providers', label: 'Providers', svg: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' },
	];

	let currentPath = $derived($page.url.pathname);
	let navEl = $state<HTMLElement | null>(null);
</script>

<aside class="border-r border-border bg-card transition-all duration-300 flex flex-col z-10 relative overflow-hidden"
	class:!w-[220px]={sidebarOpen} class:!w-[60px]={!sidebarOpen}>
	<div class="absolute left-0 top-0 w-[3px] h-full opacity-30" style="background-image: url({sidebarAccent}); background-repeat: repeat-y; background-size: 3px 200px;"></div>
	<div class="h-14 flex items-center gap-2.5 px-4 border-b border-border relative z-10">
		<div class="w-7 h-7 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
			<span class="text-primary-fg text-xs font-bold">mS</span>
		</div>
		<span class="font-display font-semibold text-base tracking-tight" class:hidden={!sidebarOpen}>model-scan</span>
	</div>

	<nav bind:this={navEl} class="flex-1 py-3 space-y-0.5 px-2">
		{#each navItems as item}
			<a href={item.href}
				class={"flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 " + (currentPath === item.href ? "bg-primary/10 text-primary" : "hover:bg-accent")}>
				<span class="flex-shrink-0">{@html item.svg}</span>
				<span class="truncate" class:hidden={!sidebarOpen}>{item.label}</span>
			</a>
		{/each}
	</nav>

	<div class="p-3 border-t border-border" class:hidden={!sidebarOpen}>
		<div class="text-xs text-muted-fg font-display">v5.0.0</div>
	</div>
</aside>
