<script lang="ts">
	import { locale } from '$i18n/index';
	import { Globe } from 'lucide-svelte';
</script>

<button
	on:click={() => locale.set($locale === 'en' ? 'es' : 'en')}
	class="flex items-center gap-1.5 rounded-lg px-2 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
	aria-label="Toggle language"
>
	<Globe size={18} />
	<span class="uppercase">{$locale}</span>
</button>
