<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { authStore } from '$stores/auth';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime } from '$lib/utils';
	import { Calendar, Clock, User, Plus } from 'lucide-svelte';
	import DateTimePicker from '$components/DateTimePicker.svelte';

	let appointments: any[] = [];
	let loading = true;
	let error = '';
	let filter: 'upcoming' | 'all' = 'upcoming';

	const canCreate = $authStore.user?.role === 'professional' || $authStore.user?.role === 'devadmin';

	let showForm = false;
	let patientId = '';
	let scheduledAt = '';
	let apptTitle = '';
	let durationMinutes = '30';
	let notes = '';
	let formLoading = false;
	let formError = '';

	async function loadAppointments() {
		loading = true;
		try {
			const params: Record<string, string> = {};
			if (filter === 'upcoming') params.upcoming = 'true';
			const res = await api.get('/appointments', params);
			appointments = res.data;
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	async function createAppointment() {
		formError = '';
		formLoading = true;
		try {
			const res = await api.post('/appointments', {
				patient_id: patientId,
				scheduled_at: new Date(scheduledAt).toISOString(),
				title: apptTitle,
				duration_minutes: parseInt(durationMinutes),
				notes: notes || undefined
			});
			appointments = [...appointments, res.data].sort(
				(a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
			);
			showForm = false;
			patientId = '';
			scheduledAt = '';
			apptTitle = '';
			notes = '';
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			formLoading = false;
		}
	}

	function statusColor(status: string): string {
		switch (status) {
			case 'scheduled': return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
			case 'completed': return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
			case 'cancelled': return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300';
			default: return 'bg-gray-100 text-gray-700';
		}
	}

	onMount(loadAppointments);
</script>

<svelte:head>
	<title>{$t('appointments.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold text-[var(--text-primary)]">{$t('appointments.title')}</h1>
		{#if canCreate}
			<button on:click={() => (showForm = !showForm)} class="btn-primary flex items-center gap-2">
				<Plus size={18} />
				{$t('appointments.new')}
			</button>
		{/if}
	</div>

	<div class="flex gap-2">
		<button
			on:click={() => { filter = 'upcoming'; loadAppointments(); }}
			class="rounded-full px-4 py-1.5 text-sm font-medium {filter === 'upcoming' ? 'bg-brand-600 text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'}"
		>
			{$t('appointments.upcoming')}
		</button>
		<button
			on:click={() => { filter = 'all'; loadAppointments(); }}
			class="rounded-full px-4 py-1.5 text-sm font-medium {filter === 'all' ? 'bg-brand-600 text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'}"
		>
			{$t('common.all')}
		</button>
	</div>

	{#if showForm && canCreate}
		<form on:submit|preventDefault={createAppointment} class="card space-y-4">
			{#if formError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{formError}</div>
			{/if}
			<div>
				<label for="patientId" class="label">{$t('appointments.patientId')}</label>
				<input id="patientId" type="text" bind:value={patientId} class="input" required placeholder="Patient UUID" />
			</div>
			<div>
				<label for="apptTitle" class="label">{$t('appointments.appointmentTitle')}</label>
				<input id="apptTitle" type="text" bind:value={apptTitle} class="input" required />
			</div>
			<div>
				<label class="label">{$t('appointments.dateTime')}</label>
				<DateTimePicker bind:value={scheduledAt} id="scheduledAt" required />
			</div>
			<div>
				<label for="duration" class="label">{$t('appointments.duration')}</label>
				<input id="duration" type="number" bind:value={durationMinutes} class="input" />
			</div>
			<div class="flex gap-3">
				<button type="submit" class="btn-primary" disabled={formLoading}>
					{formLoading ? $t('common.loading') : $t('common.save')}
				</button>
				<button type="button" on:click={() => (showForm = false)} class="btn-secondary">{$t('common.cancel')}</button>
			</div>
		</form>
	{/if}

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if appointments.length === 0}
		<div class="py-12 text-center">
			<Calendar size={48} class="mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
			<p class="text-[var(--text-secondary)]">{$t('appointments.noAppointments')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each appointments as appt (appt.id)}
				<div class="card">
					<div class="flex items-start justify-between">
						<div>
							<h3 class="font-medium text-[var(--text-primary)]">{appt.title}</h3>
							<div class="mt-2 flex flex-wrap items-center gap-3 text-sm text-[var(--text-secondary)]">
								<span class="flex items-center gap-1">
									<Calendar size={14} />
									{formatDateTime(appt.scheduled_at)}
								</span>
								<span class="flex items-center gap-1">
									<Clock size={14} />
									{appt.duration_minutes} min
								</span>
								{#if appt.professional_name}
									<span class="flex items-center gap-1">
										<User size={14} />
										{appt.professional_name}
									</span>
								{/if}
							</div>
							{#if appt.notes}
								<p class="mt-2 text-sm text-[var(--text-secondary)]">{appt.notes}</p>
							{/if}
						</div>
						<span class="rounded-full px-2.5 py-0.5 text-xs font-medium {statusColor(appt.status)}">
							{$t(`appointments.${appt.status}`)}
						</span>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
