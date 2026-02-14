<script lang="ts">
	import { themeStore } from '$stores/theme';
	import { Sun, Moon } from 'lucide-svelte';
</script>

<button
	on:click={() => themeStore.toggle()}
	class="rounded-lg p-2 text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
	aria-label="Toggle theme"
>
	{#if $themeStore === 'dark'}
		<Sun size={20} />
	{:else}
		<Moon size={20} />
	{/if}
</button>
