<script lang="ts">
	import { t, locale } from '$i18n/index';
	import { themeStore } from '$stores/theme';
	import { BRANDING } from '$lib/config/branding';
	import { Sun, Moon, Globe } from 'lucide-svelte';
</script>

<svelte:head>
	<title>{$t('settings.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="mx-auto max-w-lg space-y-6">
	<h1 class="text-2xl font-bold text-[var(--text-primary)]">{$t('settings.title')}</h1>

	<!-- Theme -->
	<div class="card">
		<h3 class="mb-4 font-semibold text-[var(--text-primary)]">{$t('settings.theme')}</h3>
		<div class="flex gap-3">
			<button
				on:click={() => themeStore.set('light')}
				class="flex flex-1 items-center justify-center gap-2 rounded-lg border-2 px-4 py-3 text-sm font-medium transition-colors
				       {$themeStore === 'light'
					? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
					: 'border-[var(--border-color)] text-[var(--text-secondary)]'}"
			>
				<Sun size={18} />
				{$t('settings.light')}
			</button>
			<button
				on:click={() => themeStore.set('dark')}
				class="flex flex-1 items-center justify-center gap-2 rounded-lg border-2 px-4 py-3 text-sm font-medium transition-colors
				       {$themeStore === 'dark'
					? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
					: 'border-[var(--border-color)] text-[var(--text-secondary)]'}"
			>
				<Moon size={18} />
				{$t('settings.dark')}
			</button>
		</div>
	</div>

	<!-- Language -->
	<div class="card">
		<h3 class="mb-4 font-semibold text-[var(--text-primary)]">{$t('settings.language')}</h3>
		<div class="flex gap-3">
			<button
				on:click={() => locale.set('en')}
				class="flex flex-1 items-center justify-center gap-2 rounded-lg border-2 px-4 py-3 text-sm font-medium transition-colors
				       {$locale === 'en'
					? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
					: 'border-[var(--border-color)] text-[var(--text-secondary)]'}"
			>
				<Globe size={18} />
				English
			</button>
			<button
				on:click={() => locale.set('es')}
				class="flex flex-1 items-center justify-center gap-2 rounded-lg border-2 px-4 py-3 text-sm font-medium transition-colors
				       {$locale === 'es'
					? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
					: 'border-[var(--border-color)] text-[var(--text-secondary)]'}"
			>
				<Globe size={18} />
				Espa&ntilde;ol
			</button>
		</div>
	</div>

	<!-- About -->
	<div class="card">
		<h3 class="mb-2 font-semibold text-[var(--text-primary)]">{BRANDING.appName}</h3>
		<p class="text-sm text-[var(--text-secondary)]">{BRANDING.description}</p>
		<p class="mt-2 text-xs text-[var(--text-secondary)]">v{BRANDING.version}</p>
	</div>
</div>
