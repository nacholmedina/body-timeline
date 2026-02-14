<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { authStore } from '$stores/auth';
	import { BRANDING } from '$lib/config/branding';
	import { timeAgo } from '$lib/utils';
	import { locale } from '$i18n/index';
	import { Bell, CheckCircle, Send, Plus } from 'lucide-svelte';

	let notifications: any[] = [];
	let loading = true;
	let error = '';

	// Create notification form (for professionals)
	let showForm = false;
	let title = '';
	let body = '';
	let patientIds = '';
	let formLoading = false;
	let formError = '';

	const isProfessional = $authStore.user?.role === 'professional' || $authStore.user?.role === 'devadmin';
	const isPatient = $authStore.user?.role === 'patient';

	async function loadNotifications() {
		loading = true;
		try {
			const res = await api.get('/notifications');
			notifications = res.data;
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	async function markAsRead(id: string) {
		try {
			await api.post(`/notifications/${id}/read`);
			notifications = notifications.map((n) =>
				n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n
			);
		} catch {}
	}

	async function createNotification() {
		formError = '';
		formLoading = true;
		try {
			const ids = patientIds.split(',').map((s) => s.trim()).filter(Boolean);
			const res = await api.post('/notifications', { title, body, patient_ids: ids });
			notifications = [res.data, ...notifications];
			showForm = false;
			title = '';
			body = '';
			patientIds = '';
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			formLoading = false;
		}
	}

	onMount(loadNotifications);
</script>

<svelte:head>
	<title>{$t('notifications.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between gap-3">
		<h1 class="text-2xl font-bold text-[var(--text-primary)] min-w-0 truncate">{$t('notifications.title')}</h1>
		{#if isProfessional}
			<button on:click={() => (showForm = !showForm)} class="btn-primary flex items-center gap-2 shrink-0">
				<Plus size={18} />
				<span class="hidden sm:inline">{$t('notifications.createNote')}</span>
			</button>
		{/if}
	</div>

	{#if showForm && isProfessional}
		<form on:submit|preventDefault={createNotification} class="card space-y-4">
			{#if formError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{formError}</div>
			{/if}
			<div>
				<label for="nTitle" class="label">{$t('notifications.noteTitle')}</label>
				<input id="nTitle" type="text" bind:value={title} class="input" required />
			</div>
			<div>
				<label for="nBody" class="label">{$t('notifications.noteMessage')}</label>
				<textarea id="nBody" bind:value={body} class="input" rows="3" required></textarea>
			</div>
			<div>
				<label for="patientIds" class="label">{$t('notifications.patientIds')}</label>
				<input id="patientIds" type="text" bind:value={patientIds} class="input" required placeholder="uuid1, uuid2" />
			</div>
			<div class="flex gap-3">
				<button type="submit" class="btn-primary flex items-center gap-2" disabled={formLoading}>
					<Send size={16} />
					{formLoading ? $t('common.loading') : $t('notifications.send')}
				</button>
				<button type="button" on:click={() => (showForm = false)} class="btn-secondary">{$t('common.cancel')}</button>
			</div>
		</form>
	{/if}

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if notifications.length === 0}
		<div class="py-12 text-center">
			<Bell size={48} class="mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
			<p class="text-[var(--text-secondary)]">{$t('notifications.noNotifications')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each notifications as notif (notif.id)}
				<div class="card {!notif.is_read && isPatient ? 'border-brand-300 dark:border-brand-700 bg-brand-50/50 dark:bg-brand-950/50' : ''}">
					<div class="flex items-start justify-between">
						<div class="flex-1">
							<div class="flex items-center gap-2">
								<h3 class="font-medium text-[var(--text-primary)]">{notif.title}</h3>
								{#if notif.is_read}
									<CheckCircle size={14} class="text-accent-500" />
								{/if}
							</div>
							<p class="mt-1 text-sm text-[var(--text-secondary)]">{notif.body}</p>
							<div class="mt-2 flex items-center gap-3 text-xs text-[var(--text-secondary)]">
								{#if notif.author_name}
									<span class="font-medium text-brand-600 dark:text-brand-400">{notif.author_name}</span>
								{/if}
								<span>{timeAgo(notif.created_at, $locale)}</span>
							</div>
						</div>
						{#if isPatient && !notif.is_read}
							<button
								on:click={() => markAsRead(notif.id)}
								class="btn-secondary text-xs"
							>
								{$t('notifications.markRead')}
							</button>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
