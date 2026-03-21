<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { authStore } from '$stores/auth';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime } from '$lib/utils';
	import { Calendar, Clock, User, Plus, XCircle, RefreshCw, Trash2 } from 'lucide-svelte';
	import DateTimePicker from '$components/DateTimePicker.svelte';
	import ConfirmModal from '$components/ConfirmModal.svelte';
	import BookAppointment from '$components/BookAppointment.svelte';

	let appointments: any[] = [];
	let patients: any[] = [];
	let loading = true;
	let error = '';
	let filter: 'upcoming' | 'all' = 'upcoming';

	const canCreate = $authStore.user?.role === 'professional' || $authStore.user?.role === 'devadmin';
	const isPatient = $authStore.user?.role === 'patient';

	// Patient's assigned professional
	let assignedProfessional: { id: string; first_name: string; last_name: string } | null = null;

	let showForm = false;
	let patientId = '';
	let scheduledAt = '';
	let apptTitle = '';
	let durationMinutes = '30';
	let notes = '';
	let formLoading = false;
	let formError = '';
	let overrideWarning = false;

	// Reschedule modal
	let showRescheduleModal = false;
	let rescheduleAppt: any = null;
	let rescheduleDateTime = '';
	let rescheduling = false;
	let rescheduleError = '';

	// Delete confirmation
	let showDeleteConfirm = false;
	let appointmentToDelete: string | null = null;
	let deleting = false;

	// Auto-fill title when patient changes
	$: if (patientId && patients.length > 0) {
		const patient = patients.find((p: any) => p.id === patientId);
		if (patient && !apptTitle) {
			apptTitle = `${patient.first_name} ${patient.last_name}`;
		}
	}

	// Reset override when scheduled time changes
	$: if (scheduledAt) {
		overrideWarning = false;
	}

	async function loadAppointments() {
		loading = true;
		try {
			const params: Record<string, string> = {};
			if (filter === 'upcoming') params.upcoming = 'true';
			const res = await api.get('/appointments', params);
			// Próximos: nearest first (ascending). Todo: latest first (descending)
			appointments = res.data.sort((a: any, b: any) => {
				const timeA = new Date(a.scheduled_at).getTime();
				const timeB = new Date(b.scheduled_at).getTime();
				return filter === 'upcoming' ? timeA - timeB : timeB - timeA;
			});
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	async function loadPatients() {
		if (!canCreate) return;
		try {
			const res = await api.get('/professional/patients');
			patients = res.data || [];
		} catch (err) {
			console.error('Failed to load patients:', err);
		}
	}

	async function createAppointment() {
		formError = '';
		formLoading = true;
		try {
			// Validate required fields
			if (!patientId || !scheduledAt || !apptTitle) {
				formError = 'Todos los campos son requeridos';
				formLoading = false;
				return;
			}

			// Check for past dates
			const scheduledDate = new Date(scheduledAt);
			const now = new Date();
			if (isNaN(scheduledDate.getTime())) {
				formError = 'Fecha y hora inválida';
				formLoading = false;
				return;
			}
			if (scheduledDate < now) {
				formError = $t('appointments.cannotSchedulePast');
				formLoading = false;
				return;
			}

			// Check for overlapping appointments (skip for "other" patients)
			if (patientId !== 'other' && !overrideWarning) {
				try {
					// Fetch scheduled appointments to check for overlaps (excludes completed/cancelled)
					const allApptsRes = await api.get('/appointments', { status: 'scheduled', limit: '100' });
					const allAppointments = allApptsRes.data || [];

					const durationMs = parseInt(durationMinutes) * 60000;
					const newStart = scheduledDate.getTime();
					const newEnd = newStart + durationMs;
					const nowTime = now.getTime();

					// Find conflicts: same patient, not cancelled, not completely ended, time overlaps
					const conflicts = allAppointments.filter((appt: any) => {
						// Same patient only (convert both to string for comparison)
						if (String(appt.patient_id) !== String(patientId)) return false;
						// Not cancelled
						if (appt.status === 'cancelled') return false;
						// Time range
						const existStart = new Date(appt.scheduled_at).getTime();
						const existEnd = existStart + (appt.duration_minutes * 60000);
						// Skip if appointment has completely ended
						if (existEnd <= nowTime) return false;
						// Check overlap: new starts before existing ends AND new ends after existing starts
						return (newStart < existEnd) && (newEnd > existStart);
					});

					if (conflicts.length > 0) {
						const patient = patients.find((p: any) => p.id === patientId);
						const patientName = patient ? `${patient.first_name} ${patient.last_name}` : apptTitle;
						const conflictTimes = conflicts.map((c: any) =>
							new Date(c.scheduled_at).toLocaleTimeString($locale === 'es' ? 'es-AR' : 'en-US', { hour: '2-digit', minute: '2-digit' })
						).join(', ');
						formError = `${patientName}: ${$t('appointments.overlapWarning')} ${conflictTimes}. ${$t('professional.proceedAnyway')}`;
						overrideWarning = true;
						formLoading = false;
						return;
					}
				} catch (err) {
					console.error('Overlap check failed:', err);
					// Continue with appointment creation if overlap check fails
				}
			}

			const res = await api.post('/appointments', {
				patient_id: patientId === 'other' ? null : patientId,
				scheduled_at: new Date(scheduledAt).toISOString(),
				title: apptTitle,
				duration_minutes: parseInt(durationMinutes),
				notes: notes || undefined
			});
			appointments = [...appointments, res.data].sort((a, b) => {
				const timeA = new Date(a.scheduled_at).getTime();
				const timeB = new Date(b.scheduled_at).getTime();
				return filter === 'upcoming' ? timeA - timeB : timeB - timeA;
			});
			showForm = false;
			patientId = '';
			scheduledAt = '';
			apptTitle = '';
			notes = '';
			overrideWarning = false;
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			formLoading = false;
		}
	}

	async function cancelAppointment(appt: any) {
		if (!confirm($t('appointments.confirmCancel'))) return;
		try {
			await api.patch(`/appointments/${appt.id}`, { status: 'cancelled' });
			appointments = appointments.map(a => a.id === appt.id ? { ...a, status: 'cancelled' } : a);
		} catch (err) {
			console.error('Failed to cancel:', err);
		}
	}

	function deleteAppointment(id: string) {
		appointmentToDelete = id;
		showDeleteConfirm = true;
	}

	async function confirmDelete() {
		if (!appointmentToDelete) return;
		deleting = true;
		try {
			await api.delete(`/appointments/${appointmentToDelete}`);
			appointments = appointments.filter(a => a.id !== appointmentToDelete);
			showDeleteConfirm = false;
			appointmentToDelete = null;
		} catch (err) {
			error = 'Failed to delete appointment';
		} finally {
			deleting = false;
		}
	}

	function openReschedule(appt: any) {
		rescheduleAppt = appt;
		const d = new Date(appt.scheduled_at);
		const pad = (n: number) => String(n).padStart(2, '0');
		rescheduleDateTime = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
		rescheduleError = '';
		showRescheduleModal = true;
	}

	async function rescheduleAppointment() {
		if (!rescheduleDateTime) return;
		rescheduling = true;
		rescheduleError = '';
		try {
			const res = await api.patch(`/appointments/${rescheduleAppt.id}`, {
				scheduled_at: new Date(rescheduleDateTime).toISOString()
			});
			appointments = appointments.map(a => a.id === rescheduleAppt.id ? res.data : a)
				.sort((a, b) => {
					const timeA = new Date(a.scheduled_at).getTime();
					const timeB = new Date(b.scheduled_at).getTime();
					return filter === 'upcoming' ? timeA - timeB : timeB - timeA;
				});
			showRescheduleModal = false;
			rescheduleAppt = null;
		} catch (err) {
			rescheduleError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			rescheduling = false;
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

	function handlePatientChange() {
		apptTitle = '';
		overrideWarning = false;
		formError = '';
	}

	async function loadAssignedProfessional() {
		if (!isPatient) return;
		try {
			const res = await api.get('/professional/assigned');
			assignedProfessional = res.data;
		} catch (err) {
			console.error('Failed to load assigned professional:', err);
		}
	}

	async function patientCancelAppointment(appt: any) {
		if (!confirm($t('availability.confirmCancelBooking'))) return;
		try {
			await api.patch(`/appointments/${appt.id}`, { status: 'cancelled' });
			appointments = appointments.map(a => a.id === appt.id ? { ...a, status: 'cancelled' } : a);
		} catch (err) {
			console.error('Failed to cancel:', err);
		}
	}

	onMount(() => {
		loadAppointments();
		loadPatients();
		loadAssignedProfessional();
	});
</script>

<svelte:head>
	<title>{$t('appointments.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between gap-3">
		<h1 class="text-2xl font-bold text-[var(--text-primary)] min-w-0 truncate">{$t('appointments.title')}</h1>
		<div class="flex items-center gap-2">
			{#if isPatient && assignedProfessional}
				<BookAppointment
					professionalId={assignedProfessional.id}
					professionalName="{assignedProfessional.first_name} {assignedProfessional.last_name}"
					onBooked={loadAppointments}
				/>
			{/if}
			{#if canCreate}
				<button on:click={() => (showForm = !showForm)} class="btn-primary flex items-center gap-2 shrink-0">
					<Plus size={18} />
					<span class="hidden sm:inline">{$t('appointments.new')}</span>
				</button>
			{/if}
		</div>
	</div>

	{#if isPatient && !assignedProfessional && !loading}
		<div class="card text-sm text-[var(--text-secondary)] text-center py-4">
			{$t('availability.noProfessionalAssigned')}
		</div>
	{/if}

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
				<label for="patientId" class="label">{$t('appointments.selectPatient')}</label>
				<select id="patientId" bind:value={patientId} on:change={handlePatientChange} class="input" required>
					<option value="">{$t('professional.selectPatient')}</option>
					{#each patients as p}
						<option value={p.id}>{p.first_name} {p.last_name}</option>
					{/each}
					<option value="other">{$t('appointments.otherPatient')}</option>
				</select>
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
						<div class="flex-1 min-w-0">
							<h3 class="font-medium text-[var(--text-primary)]">{appt.title}</h3>
							<div class="mt-2 flex flex-wrap items-center gap-3 text-sm text-[var(--text-secondary)]">
								<span class="flex items-center gap-1">
									<Calendar size={14} />
									{formatDateTime(appt.scheduled_at, $locale)}
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
						<div class="flex items-center gap-2 shrink-0 ml-3">
							<span class="rounded-full px-2.5 py-0.5 text-xs font-medium {statusColor(appt.status)}">
								{$t(`appointments.${appt.status}`)}
							</span>
							{#if canCreate && appt.status === 'scheduled'}
								<button
									on:click={() => openReschedule(appt)}
									class="rounded-lg p-1.5 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
									title={$t('appointments.reschedule')}
								>
									<RefreshCw size={16} />
								</button>
								<button
									on:click={() => cancelAppointment(appt)}
									class="rounded-lg p-1.5 text-orange-500 hover:bg-orange-50 dark:hover:bg-orange-950 transition-colors"
									title={$t('appointments.cancel')}
								>
									<XCircle size={16} />
								</button>
							{/if}
							{#if canCreate}
								<button
									on:click={() => deleteAppointment(appt.id)}
									class="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
									title={$t('appointments.delete')}
								>
									<Trash2 size={16} />
								</button>
							{/if}
							{#if isPatient && appt.status === 'scheduled' && String(appt.patient_id) === String($authStore.user?.id)}
								<button
									on:click={() => patientCancelAppointment(appt)}
									class="rounded-lg p-1.5 text-orange-500 hover:bg-orange-50 dark:hover:bg-orange-950 transition-colors"
									title={$t('availability.cancelAppointment')}
								>
									<XCircle size={16} />
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Reschedule Modal -->
{#if showRescheduleModal && rescheduleAppt}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl">
			<h2 class="text-lg font-bold text-[var(--text-primary)] mb-4">{$t('appointments.reschedule')}</h2>
			<p class="text-sm text-[var(--text-secondary)] mb-4">{rescheduleAppt.title}</p>

			{#if rescheduleError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400 mb-4">{rescheduleError}</div>
			{/if}

			<div class="mb-4">
				<label class="label">{$t('appointments.dateTime')}</label>
				<DateTimePicker bind:value={rescheduleDateTime} id="reschedule" required />
			</div>

			<div class="flex gap-3">
				<button
					on:click={rescheduleAppointment}
					class="btn-primary flex-1"
					disabled={rescheduling}
				>
					{rescheduling ? $t('common.loading') : $t('common.save')}
				</button>
				<button
					on:click={() => { showRescheduleModal = false; rescheduleAppt = null; }}
					class="btn-secondary flex-1"
				>
					{$t('common.cancel')}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Delete Confirmation Modal -->
<ConfirmModal
	bind:show={showDeleteConfirm}
	title={$t('common.delete')}
	message={$t('appointments.confirmDelete')}
	onConfirm={confirmDelete}
	loading={deleting}
/>
