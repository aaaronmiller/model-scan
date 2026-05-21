<script lang="ts">
	import '../app.css';
	import Header from '$lib/components/dashboard/Header.svelte';
	import Sidebar from '$lib/components/dashboard/Sidebar.svelte';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import gsap from 'gsap';
	import heroBanner from '$lib/assets/hero-banner.png';
	import footerBg from '$lib/assets/footer-bg.png';
	import sidebarAccent from '$lib/assets/sidebar-accent.png';
	import patternDots from '$lib/assets/pattern-dots.png';

	let sidebarOpen = $state(true);
	let darkMode = $state(false);
	let { children } = $props();
	let mainEl = $state<HTMLElement | null>(null);
	let footerEl = $state<HTMLElement | null>(null);

	onMount(() => {
		const saved = localStorage.getItem('theme');
		if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
			darkMode = true;
			document.documentElement.classList.add('dark');
		}
	});

	$effect(() => {
		document.documentElement.classList.toggle('dark', darkMode);
		localStorage.setItem('theme', darkMode ? 'dark' : 'light');
	});

	$effect(() => {
		if ($page.url.pathname && mainEl) {
			gsap.fromTo(mainEl,
				{ opacity: 0, y: 20 },
				{ opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }
			);
		}
	});

	$effect(() => {
		if (footerEl) {
			gsap.fromTo(footerEl,
				{ opacity: 0 },
				{ opacity: 1, duration: 0.6, delay: 0.3, ease: 'power2.out' }
			);
		}
	});
</script>

<div class="flex h-screen bg-bg text-fg" style="font-family:'DM Sans',sans-serif;
	background-image: url({patternDots}); background-repeat: repeat; background-size: 400px;">
	
	<Sidebar {sidebarOpen} />

	<div class="flex-1 flex flex-col min-w-0">
		<Header {darkMode} onToggleDark={() => darkMode = !darkMode}
			onToggleSidebar={() => sidebarOpen = !sidebarOpen} />

		<main bind:this={mainEl} class="flex-1 overflow-y-auto p-6 lg:p-8">
			{@render children()}
		</main>

		<footer bind:this={footerEl}
			class="border-t border-border px-6 lg:px-8 py-4 text-xs text-muted-fg flex justify-between items-center relative overflow-hidden"
			style="font-family:'Lexend',sans-serif; background-image: url({footerBg}); background-size: cover; background-position: center;">
			<div class="absolute inset-0 bg-black/40"></div>
			<span class="relative z-10">model-scan v5</span>
			<span class="relative z-10">scanned at <time>{new Date().toLocaleString()}</time></span>
		</footer>
	</div>
</div>
