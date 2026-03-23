<script lang="ts">
	import { onlineStore } from '$stores/online';
	import { syncStatus, syncPending, syncAll } from '$lib/offline/sync';
	import { t } from '$i18n/index';
	import { WifiOff, RefreshCw, Check } from 'lucide-svelte';

	$: showBanner = !$onlineStore || $syncStatus === 'syncing' || $syncStatus === 'complete' || ($syncPending > 0 && $onlineStore);
</script>

{#if showBanner}
	<!-- Spacer to push content below the fixed banner -->
	<div class="h-10"></div>
{/if}

{#if !$onlineStore}
	<div class="fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-2 bg-amber-500 px-4 py-2 text-sm font-medium text-white">
		<WifiOff size={16} />
		{$t('common.offline')}
	</div>
{:else if $syncStatus === 'syncing'}
	<div class="fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-2 bg-brand-500 px-4 py-2 text-sm font-medium text-white">
		<RefreshCw size={16} class="animate-spin" />
		{$t('common.syncing')} ({$syncPending})
	</div>
{:else if $syncStatus === 'complete'}
	<div class="fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-2 bg-accent-500 px-4 py-2 text-sm font-medium text-white">
		<Check size={16} />
		{$t('common.syncComplete')}
	</div>
{:else if $syncPending > 0 && $onlineStore}
	<button
		on:click={syncAll}
		class="fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-2 bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
	>
		<RefreshCw size={16} />
		{$syncPending} pending - Tap to sync
	</button>
{/if}
