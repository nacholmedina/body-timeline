<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { t } from '$i18n/index';
	import { api } from '$lib/api/client';
	import { Calendar, Check, Loader2, X, ExternalLink } from 'lucide-svelte';

	interface Status {
		connected: boolean;
		configured: boolean;
		google_email?: string;
		calendar_id?: string;
		connected_at?: string;
	}

	let status: Status | null = null;
	let loading = true;
	let acting = false;
	let banner: { kind: 'success' | 'error'; text: string } | null = null;

	async function loadStatus() {
		try {
			status = await api.get('/auth/google/calendar/status');
		} catch {
			status = { connected: false, configured: false };
		} finally {
			loading = false;
		}
	}

	async function connect() {
		acting = true;
		try {
			const res = await api.get('/auth/google/calendar/connect');
			if (browser && res.authorization_url) {
				window.location.href = res.authorization_url;
				return;
			}
		} catch (err: any) {
			banner = { kind: 'error', text: err.message || $t('googleCalendar.connectFailed') };
		} finally {
			acting = false;
		}
	}

	async function disconnect() {
		if (!confirm($t('googleCalendar.disconnectConfirm'))) return;
		acting = true;
		try {
			await api.post('/auth/google/calendar/disconnect');
			banner = { kind: 'success', text: $t('googleCalendar.disconnected') };
			await loadStatus();
		} catch (err: any) {
			banner = { kind: 'error', text: err.message || $t('googleCalendar.disconnectFailed') };
		} finally {
			acting = false;
			setTimeout(() => (banner = null), 3500);
		}
	}

	function consumeCallbackParam() {
		if (!browser) return;
		const param = $page.url.searchParams.get('google_calendar');
		if (!param) return;
		if (param === 'connected') {
			banner = { kind: 'success', text: $t('googleCalendar.connectedToast') };
		} else if (param === 'denied') {
			banner = { kind: 'error', text: $t('googleCalendar.consentDenied') };
		} else {
			banner = { kind: 'error', text: $t('googleCalendar.connectFailed') };
		}
		// Strip the param without reloading
		const url = new URL(window.location.href);
		url.searchParams.delete('google_calendar');
		goto(url.pathname + url.search + url.hash, { replaceState: true, noScroll: true });
		setTimeout(() => (banner = null), 4000);
	}

	onMount(async () => {
		consumeCallbackParam();
		await loadStatus();
	});
</script>

<div class="card">
	<div class="flex items-center gap-3 mb-3">
		<div class="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900/40">
			<Calendar size={18} class="text-brand-600 dark:text-brand-400" />
		</div>
		<div>
			<h3 class="text-lg font-semibold text-[var(--text-primary)]">{$t('googleCalendar.title')}</h3>
			<p class="text-xs text-[var(--text-secondary)]">{$t('googleCalendar.subtitle')}</p>
		</div>
	</div>

	{#if banner}
		<div class="mb-3 rounded-lg border p-3 text-sm flex items-start gap-2
			{banner.kind === 'success'
				? 'border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-950/40 dark:text-green-300'
				: 'border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-300'}">
			{#if banner.kind === 'success'}
				<Check size={16} class="shrink-0 mt-0.5" />
			{:else}
				<X size={16} class="shrink-0 mt-0.5" />
			{/if}
			<span>{banner.text}</span>
		</div>
	{/if}

	{#if loading}
		<div class="flex items-center gap-2 text-sm text-[var(--text-secondary)] py-2">
			<Loader2 size={14} class="animate-spin" />
			{$t('common.loading')}
		</div>
	{:else if status && !status.configured}
		<p class="text-sm text-[var(--text-secondary)]">{$t('googleCalendar.notConfigured')}</p>
	{:else if status && status.connected}
		<div class="space-y-3">
			<div class="flex items-center gap-2 text-sm text-[var(--text-primary)]">
				<Check size={14} class="text-green-600 dark:text-green-400" />
				<span>
					{$t('googleCalendar.connectedAs')}
					<span class="font-medium">{status.google_email || $t('googleCalendar.yourGoogleAccount')}</span>
				</span>
			</div>
			<p class="text-xs text-[var(--text-secondary)]">{$t('googleCalendar.connectedHint')}</p>
			<button
				on:click={disconnect}
				disabled={acting}
				class="rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors disabled:opacity-50"
			>
				{acting ? $t('common.loading') : $t('googleCalendar.disconnect')}
			</button>
		</div>
	{:else}
		<div class="space-y-3">
			<p class="text-sm text-[var(--text-secondary)]">{$t('googleCalendar.notConnectedHint')}</p>
			<button
				on:click={connect}
				disabled={acting}
				class="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
			>
				<ExternalLink size={14} />
				{acting ? $t('common.loading') : $t('googleCalendar.connect')}
			</button>
		</div>
	{/if}
</div>
