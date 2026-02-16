<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { authStore } from '$stores/auth';
	import { BRANDING } from '$lib/config/branding';
	import { timeAgo } from '$lib/utils';
	import { locale } from '$i18n/index';
	import { Bell, CheckCircle, Send, Plus, Mail, Check, X } from 'lucide-svelte';
	import { unreadCount } from '$lib/stores/notifications';

	function detectType(title: string): string | null {
		if (title === 'meal_comment') return 'meal_comment';
		if (title === 'meal_reply') return 'meal_reply';
		if (title === 'professional_invitation') return 'professional_invitation';
		if (title === 'assignment_removed') return 'assignment_removed';
		if (title === 'goal_created') return 'goal_created';
		if (title === 'appointment_scheduled') return 'appointment_scheduled';
		if (title === 'appointment_cancelled') return 'appointment_cancelled';
		if (title === 'appointment_deleted') return 'appointment_deleted';
		if (title === 'exercise_request_created') return 'exercise_request_created';
		if (title === 'exercise_request_approved') return 'exercise_request_approved';
		if (title === 'exercise_request_rejected') return 'exercise_request_rejected';
		if (title.includes('commented on your meal')) return 'meal_comment';
		if (title.includes('Professional Invitation from')) return 'professional_invitation';
		if (title === 'Patient Assignment Removed') return 'assignment_removed';
		return null;
	}

	let notifications: any[] = [];

	// Reactive translated notifications — $t in a reactive block ensures Svelte tracks locale changes
	$: displayNotifications = notifications.map(notif => {
		const type = detectType(notif.title);
		const name = notif.author_name || '';
		let displayTitle = notif.title;
		let displayBody = notif.body;

		if (type === 'meal_comment') {
			displayTitle = $t('notifications.mealCommentTitle').replace('{name}', name);
			const preview = notif.body?.replace(/^Your professional has commented on your meal:\s*/, '') || '';
			displayBody = $t('notifications.mealCommentBody').replace('{name}', name).replace('{preview}', preview);
		} else if (type === 'meal_reply') {
			displayTitle = $t('notifications.mealReplyTitle').replace('{name}', name);
			displayBody = $t('notifications.mealReplyBody').replace('{name}', name).replace('{preview}', notif.body || '');
		} else if (type === 'professional_invitation') {
			displayTitle = $t('notifications.professionalInvitationTitle').replace('{name}', name);
			displayBody = $t('notifications.professionalInvitationBody').replace('{name}', name);
		} else if (type === 'assignment_removed') {
			displayTitle = $t('notifications.assignmentRemovedTitle');
			displayBody = $t('notifications.assignmentRemovedBody').replace('{name}', name);
		} else if (type === 'goal_created') {
			displayTitle = $t('notifications.goalCreatedTitle').replace('{name}', name);
			displayBody = $t('notifications.goalCreatedBody').replace('{name}', name).replace('{goal}', notif.body || '');
		} else if (type === 'appointment_scheduled') {
			displayTitle = $t('notifications.appointmentScheduledTitle').replace('{name}', name);
			displayBody = $t('notifications.appointmentScheduledBody').replace('{name}', name).replace('{details}', notif.body || '');
		} else if (type === 'appointment_cancelled') {
			displayTitle = $t('notifications.appointmentCancelledTitle');
			displayBody = $t('notifications.appointmentCancelledBody').replace('{name}', name).replace('{details}', notif.body || '');
		} else if (type === 'appointment_deleted') {
			displayTitle = $t('notifications.appointmentDeletedTitle');
			displayBody = $t('notifications.appointmentDeletedBody').replace('{name}', name).replace('{details}', notif.body || '');
		} else if (type === 'exercise_request_created') {
			displayTitle = $t('notifications.exerciseRequestCreatedTitle').replace('{name}', name);
			displayBody = $t('notifications.exerciseRequestCreatedBody').replace('{details}', notif.body || '');
		} else if (type === 'exercise_request_approved') {
			displayTitle = $t('notifications.exerciseRequestApprovedTitle');
			displayBody = $t('notifications.exerciseRequestApprovedBody').replace('{details}', notif.body || '');
		} else if (type === 'exercise_request_rejected') {
			displayTitle = $t('notifications.exerciseRequestRejectedTitle');
			displayBody = $t('notifications.exerciseRequestRejectedBody').replace('{details}', notif.body || '');
		}

		return { ...notif, displayTitle, displayBody };
	});
	let invitations: any[] = [];
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
			const promises = [api.get('/notifications')];
			if (isPatient) {
				promises.push(api.get('/invitations/pending'));
			}
			const results = await Promise.all(promises);
			notifications = results[0].data;
			if (isPatient && results[1]) {
				invitations = results[1].data || [];
			}
		} catch (err) {
			error = err instanceof ApiError ? err.message : $t('common.failedToLoad');
		} finally {
			loading = false;
		}
	}

	async function acceptInvitation(id: string) {
		try {
			await api.post(`/invitations/${id}/accept`);
			invitations = invitations.filter((inv) => inv.id !== id);
		} catch (err) {
			error = err instanceof ApiError ? err.message : $t('invitations.failedToAccept');
		}
	}

	async function rejectInvitation(id: string) {
		try {
			await api.post(`/invitations/${id}/reject`);
			invitations = invitations.filter((inv) => inv.id !== id);
		} catch (err) {
			error = err instanceof ApiError ? err.message : $t('invitations.failedToReject');
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
			formError = err instanceof ApiError ? err.message : $t('common.failed');
		} finally {
			formLoading = false;
		}
	}

	onMount(async () => {
		await loadNotifications();
		// Mark all as read on the backend and reset badge
		try {
			await api.post('/notifications/mark-all-read');
			notifications = notifications.map(n => ({ ...n, is_read: true }));
		} catch {}
		unreadCount.set(0);
	});
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

	<!-- Pending Invitations for Patients -->
	{#if isPatient && invitations.length > 0}
		<div class="card border-brand-300 dark:border-brand-700 bg-brand-50 dark:bg-brand-950">
			<div class="mb-4 flex items-center gap-2">
				<Mail size={18} class="text-brand-600" />
				<h3 class="font-semibold text-[var(--text-primary)]">{$t('invitations.pending')}</h3>
			</div>
			<div class="space-y-3">
				{#each invitations as invitation}
					<div class="rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 p-4">
						<div class="mb-3">
							<p class="font-medium text-[var(--text-primary)]">
								{$t('invitations.fromProfessional')}: {invitation.professional_name}
							</p>
							{#if invitation.professional_email}
								<p class="text-sm text-[var(--text-secondary)]">{invitation.professional_email}</p>
							{/if}
							{#if invitation.message}
								<p class="mt-2 text-sm text-[var(--text-secondary)]">{invitation.message}</p>
							{/if}
						</div>
						{#if $authStore.user?.professional_id}
							<p class="mb-3 text-xs text-amber-600 dark:text-amber-400">
								{$t('invitations.warningReassignment')}
							</p>
						{/if}
						<div class="flex gap-2">
							<button
								on:click={() => acceptInvitation(invitation.id)}
								class="flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors"
							>
								<Check size={16} />
								{$t('invitations.acceptInvitation')}
							</button>
							<button
								on:click={() => rejectInvitation(invitation.id)}
								class="flex flex-1 items-center justify-center gap-2 rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
							>
								<X size={16} />
								{$t('invitations.rejectInvitation')}
							</button>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if notifications.length === 0 && invitations.length === 0}
		<div class="py-12 text-center">
			<Bell size={48} class="mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
			<p class="text-[var(--text-secondary)]">{$t('notifications.noNotifications')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each displayNotifications as notif (notif.id)}
				<div class="card {!notif.is_read ? 'border-brand-300 dark:border-brand-700 bg-brand-50/50 dark:bg-brand-950/50' : ''}">
					<div class="flex items-start justify-between">
						<div class="flex-1">
							<div class="flex items-center gap-2">
								<h3 class="font-medium text-[var(--text-primary)]">{notif.displayTitle}</h3>
								{#if notif.is_read}
									<CheckCircle size={14} class="text-accent-500" />
								{/if}
							</div>
							<p class="mt-1 text-sm text-[var(--text-secondary)]">{notif.displayBody}</p>
							<div class="mt-2 flex items-center gap-3 text-xs text-[var(--text-secondary)]">
								{#if notif.author_name}
									<span class="font-medium text-brand-600 dark:text-brand-400">{notif.author_name}</span>
								{/if}
								<span>{timeAgo(notif.created_at, $locale)}</span>
							</div>
						</div>
						{#if !notif.is_read}
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
