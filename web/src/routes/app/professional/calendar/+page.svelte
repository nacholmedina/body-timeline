<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime } from '$lib/utils';
	import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Plus, X, Clock, User } from 'lucide-svelte';

	type ViewMode = 'day' | 'week' | 'month';

	let view: ViewMode = 'month';
	let currentDate = new Date();
	let appointments: any[] = [];
	let patients: any[] = [];
	let loading = true;

	// Create appointment modal
	let showCreateModal = false;
	let selectedPatientId = '';
	let appointmentTitle = '';
	let appointmentDate = '';
	let appointmentTime = '';
	let appointmentDuration = 30;
	let appointmentNotes = '';
	let creating = false;
	let createError = '';

	// Calendar state
	let calendarDays: Date[] = [];
	let weekDays: Date[] = [];

	$: localeCode = $locale === 'es' ? 'es-ES' : 'en-US';
	$: monthName = currentDate.toLocaleString(localeCode, { month: 'long', year: 'numeric' });

	onMount(async () => {
		await loadData();
		buildCalendar();
	});

	$: {
		currentDate;
		view;
		buildCalendar();
	}

	async function loadData() {
		try {
			loading = true;
			const [appts, pats] = await Promise.all([
				api.get('/appointments', { limit: '1000' }),
				api.get('/professional/patients')
			]);
			appointments = appts.data || [];
			patients = pats.data || [];
		} catch (err) {
			console.error('Failed to load calendar data:', err);
		} finally {
			loading = false;
		}
	}

	function buildCalendar() {
		if (view === 'month') {
			const year = currentDate.getFullYear();
			const month = currentDate.getMonth();
			const firstDay = new Date(year, month, 1);
			const lastDay = new Date(year, month + 1, 0);

			// Start from the Sunday of the week containing the first day
			const startDate = new Date(firstDay);
			startDate.setDate(startDate.getDate() - startDate.getDay());

			// End on the Saturday of the week containing the last day
			const endDate = new Date(lastDay);
			endDate.setDate(endDate.getDate() + (6 - endDate.getDay()));

			calendarDays = [];
			const current = new Date(startDate);
			while (current <= endDate) {
				calendarDays.push(new Date(current));
				current.setDate(current.getDate() + 1);
			}
		} else if (view === 'week') {
			// Show today + next 6 days (rolling week)
			weekDays = [];
			for (let i = 0; i < 7; i++) {
				const day = new Date(currentDate);
				day.setDate(day.getDate() + i);
				weekDays.push(day);
			}
		}
	}

	function prevPeriod() {
		const newDate = new Date(currentDate);
		if (view === 'month') {
			newDate.setMonth(newDate.getMonth() - 1);
		} else if (view === 'week') {
			newDate.setDate(newDate.getDate() - 7);
		} else {
			newDate.setDate(newDate.getDate() - 1);
		}
		currentDate = newDate;
	}

	function nextPeriod() {
		const newDate = new Date(currentDate);
		if (view === 'month') {
			newDate.setMonth(newDate.getMonth() + 1);
		} else if (view === 'week') {
			newDate.setDate(newDate.getDate() + 7);
		} else {
			newDate.setDate(newDate.getDate() + 1);
		}
		currentDate = newDate;
	}

	function today() {
		currentDate = new Date();
	}

	function getAppointmentsForDay(date: Date): any[] {
		const dateStr = date.toISOString().split('T')[0];
		return appointments.filter((appt) => {
			const apptDate = new Date(appt.scheduled_at).toISOString().split('T')[0];
			return apptDate === dateStr && appt.status !== 'cancelled';
		});
	}

	function isToday(date: Date): boolean {
		const today = new Date();
		return (
			date.getDate() === today.getDate() &&
			date.getMonth() === today.getMonth() &&
			date.getFullYear() === today.getFullYear()
		);
	}

	function isCurrentMonth(date: Date): boolean {
		return date.getMonth() === currentDate.getMonth();
	}

	async function createAppointment(forceCreate = false) {
		if (!selectedPatientId || !appointmentTitle || !appointmentDate || !appointmentTime) {
			createError = $t('professional.fillRequiredFields');
			return;
		}

		try {
			creating = true;
			createError = '';

			const scheduled_at = `${appointmentDate}T${appointmentTime}:00`;
			const scheduledDate = new Date(scheduled_at);
			const now = new Date();

			// Check if date is in the past
			if (scheduledDate < now && !forceCreate) {
				createError = $t('professional.cannotSchedulePast');
				creating = false;
				return;
			}

			// Check for conflicts (appointments that overlap)
			const conflicts = appointments.filter((appt) => {
				if (appt.patient_id !== selectedPatientId || appt.status === 'cancelled') return false;

				const apptStart = new Date(appt.scheduled_at);
				const apptEnd = new Date(apptStart.getTime() + appt.duration_minutes * 60000);
				const newEnd = new Date(scheduledDate.getTime() + appointmentDuration * 60000);

				// Check if appointments overlap
				return (scheduledDate < apptEnd && newEnd > apptStart);
			});

			if (conflicts.length > 0 && !forceCreate) {
				const conflictTimes = conflicts.map(c =>
					new Date(c.scheduled_at).toLocaleTimeString(localeCode, { hour: '2-digit', minute: '2-digit' })
				).join(', ');
				createError = `Warning: This overlaps with existing appointment(s) at ${conflictTimes}. Click again to proceed anyway.`;
				creating = false;
				return;
			}

			await api.post('/appointments', {
				patient_id: selectedPatientId,
				title: appointmentTitle,
				scheduled_at,
				duration_minutes: appointmentDuration,
				notes: appointmentNotes || undefined
			});

			showCreateModal = false;
			resetForm();
			await loadData();
		} catch (err: any) {
			createError = err.message || 'Failed to create appointment';
		} finally {
			creating = false;
		}
	}

	function resetForm() {
		selectedPatientId = '';
		appointmentTitle = '';
		appointmentDate = '';
		appointmentTime = '';
		appointmentDuration = 30;
		appointmentNotes = '';
		createError = '';
	}

	function openCreateModal() {
		resetForm();
		// Set default date to today
		const today = new Date();
		appointmentDate = today.toISOString().split('T')[0];
		appointmentTime = '09:00';
		showCreateModal = true;
	}
</script>

<svelte:head>
	<title>{$t('professional.calendar')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
		<div>
			<h1 class="text-2xl font-bold text-[var(--text-primary)]">{$t('professional.calendar')}</h1>
			<p class="text-sm text-[var(--text-secondary)]">{appointments.filter(a => a.status !== 'cancelled').length} appointments</p>
		</div>
		<button
			on:click={openCreateModal}
			class="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors"
		>
			<Plus size={18} />
			{$t('professional.createAppointment')}
		</button>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else}
		<!-- Calendar Controls -->
		<div class="card">
			<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
				<!-- View Switcher -->
				<div class="flex rounded-lg border border-[var(--border-color)] overflow-hidden">
					<button
						on:click={() => (view = 'day')}
						class="px-3 py-2 text-sm font-medium transition-colors {view === 'day'
							? 'bg-brand-600 text-white'
							: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
					>
						{$t('professional.dayView')}
					</button>
					<button
						on:click={() => (view = 'week')}
						class="px-3 py-2 text-sm font-medium transition-colors {view === 'week'
							? 'bg-brand-600 text-white'
							: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
					>
						{$t('professional.weekView')}
					</button>
					<button
						on:click={() => (view = 'month')}
						class="px-3 py-2 text-sm font-medium transition-colors {view === 'month'
							? 'bg-brand-600 text-white'
							: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
					>
						{$t('professional.monthView')}
					</button>
				</div>

				<!-- Navigation -->
				<div class="flex items-center gap-3">
					<button
						on:click={prevPeriod}
						class="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] transition-colors"
					>
						<ChevronLeft size={20} />
					</button>
					<button
						on:click={today}
						class="px-3 py-1.5 rounded-lg text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
					>
						{$t('professional.today')}
					</button>
					<button
						on:click={nextPeriod}
						class="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] transition-colors"
					>
						<ChevronRight size={20} />
					</button>
					<span class="text-sm font-medium text-[var(--text-primary)]">{monthName}</span>
				</div>
			</div>
		</div>

		<!-- Calendar View -->
		{#if view === 'month'}
			<div class="card overflow-x-auto">
				<!-- Weekday Headers -->
				<div class="grid grid-cols-7 gap-px bg-[var(--border-color)] border border-[var(--border-color)] rounded-t-lg overflow-hidden">
					{#each [$t('professional.sun'), $t('professional.mon'), $t('professional.tue'), $t('professional.wed'), $t('professional.thu'), $t('professional.fri'), $t('professional.sat')] as day}
						<div class="bg-[var(--bg-secondary)] p-2 text-center text-xs font-medium text-[var(--text-secondary)]">
							{day}
						</div>
					{/each}
				</div>

				<!-- Calendar Days -->
				<div class="grid grid-cols-7 gap-px bg-[var(--border-color)] border-x border-b border-[var(--border-color)] rounded-b-lg overflow-hidden">
					{#each calendarDays as day}
						{@const dayAppointments = getAppointmentsForDay(day)}
						<div
							class="bg-white dark:bg-gray-900 min-h-24 p-2 {isCurrentMonth(day) ? '' : 'opacity-40'}"
						>
							<div class="flex items-center justify-between mb-1">
								<span
									class="text-sm font-medium {isToday(day)
										? 'flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-white'
										: 'text-[var(--text-primary)]'}"
								>
									{day.getDate()}
								</span>
							</div>
							<div class="space-y-1">
								{#each dayAppointments.slice(0, 2) as appt}
									<div class="rounded bg-brand-100 dark:bg-brand-900 px-2 py-1 text-xs">
										<p class="font-medium text-brand-700 dark:text-brand-300 truncate">
											{new Date(appt.scheduled_at).toLocaleTimeString(localeCode, {
												hour: '2-digit',
												minute: '2-digit'
											})}
										</p>
										<p class="text-[var(--text-secondary)] truncate">{appt.title}</p>
									</div>
								{/each}
								{#if dayAppointments.length > 2}
									<p class="text-xs text-[var(--text-secondary)]">+{dayAppointments.length - 2} more</p>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{:else if view === 'week'}
			<div class="card space-y-4">
				{#each weekDays as day}
					{@const dayAppointments = getAppointmentsForDay(day)}
					<div>
						<h3 class="mb-2 text-sm font-semibold {isToday(day) ? 'text-brand-600' : 'text-[var(--text-primary)]'}">
							{day.toLocaleDateString(localeCode, { weekday: 'long', month: 'short', day: 'numeric' })}
						</h3>
						{#if dayAppointments.length > 0}
							<div class="space-y-2">
								{#each dayAppointments as appt}
									<div class="rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] p-3">
										<div class="flex items-start justify-between">
											<div class="flex-1">
												<p class="font-medium text-[var(--text-primary)]">{appt.title}</p>
												<div class="mt-1 flex items-center gap-3 text-xs text-[var(--text-secondary)]">
													<span class="flex items-center gap-1">
														<Clock size={12} />
														{new Date(appt.scheduled_at).toLocaleTimeString(localeCode, {
															hour: '2-digit',
															minute: '2-digit'
														})}
													</span>
													<span class="flex items-center gap-1">
														<User size={12} />
														{appt.patient_name || 'Unknown'}
													</span>
												</div>
											</div>
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<p class="text-sm text-[var(--text-secondary)]">{$t('professional.noAppointmentsThisDay')}</p>
						{/if}
					</div>
				{/each}
			</div>
		{:else if view === 'day'}
			{@const dayAppointments = getAppointmentsForDay(currentDate)}
			<div class="card">
				<h3 class="mb-4 text-lg font-semibold text-[var(--text-primary)]">
					{currentDate.toLocaleDateString(localeCode, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
				</h3>
				{#if dayAppointments.length > 0}
					<div class="space-y-3">
						{#each dayAppointments as appt}
							<div class="rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] p-4">
								<div class="flex items-start justify-between mb-2">
									<div class="flex-1">
										<p class="font-semibold text-[var(--text-primary)]">{appt.title}</p>
										<div class="mt-1 flex items-center gap-3 text-sm text-[var(--text-secondary)]">
											<span class="flex items-center gap-1">
												<Clock size={14} />
												{new Date(appt.scheduled_at).toLocaleTimeString(localeCode, {
													hour: '2-digit',
													minute: '2-digit'
												})} ({appt.duration_minutes} min)
											</span>
											<span class="flex items-center gap-1">
												<User size={14} />
												{appt.patient_name || 'Unknown'}
											</span>
										</div>
									</div>
								</div>
								{#if appt.notes}
									<p class="mt-2 text-sm text-[var(--text-secondary)]">{appt.notes}</p>
								{/if}
							</div>
						{/each}
					</div>
				{:else}
					<p class="text-center py-8 text-[var(--text-secondary)]">{$t('professional.noAppointmentsThisDay')}</p>
				{/if}
			</div>
		{/if}
	{/if}
</div>

<!-- Create Appointment Modal -->
{#if showCreateModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-xl font-bold text-[var(--text-primary)]">{$t('professional.createAppointment')}</h2>
				<button
					on:click={() => (showCreateModal = false)}
					class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
				>
					<X size={20} />
				</button>
			</div>

			<div class="space-y-4">
				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
						{$t('professional.patient')} *
					</label>
					<select bind:value={selectedPatientId} class="input w-full">
						<option value="">{$t('professional.selectPatient')}</option>
						{#each patients as patient}
							<option value={patient.id}>
								{patient.first_name} {patient.last_name}
							</option>
						{/each}
					</select>
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
						{$t('professional.appointmentTitle')} *
					</label>
					<input
						type="text"
						bind:value={appointmentTitle}
						class="input w-full"
					/>
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
							{$t('professional.date')} *
						</label>
						<input
							type="date"
							bind:value={appointmentDate}
							class="input w-full"
						/>
					</div>
					<div>
						<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
							{$t('professional.time')} *
						</label>
						<input
							type="time"
							bind:value={appointmentTime}
							class="input w-full"
						/>
					</div>
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
						{$t('professional.duration')}
					</label>
					<input
						type="number"
						bind:value={appointmentDuration}
						class="input w-full"
						min="15"
						step="15"
					/>
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
						{$t('professional.notes')} ({$t('common.optional')})
					</label>
					<textarea
						bind:value={appointmentNotes}
						class="input w-full"
						rows="3"
					></textarea>
				</div>

				{#if createError}
					<p class="text-sm {createError.includes('Warning') ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}">
						{createError}
					</p>
				{/if}

				<div class="flex gap-3">
					<button
						on:click={() => (showCreateModal = false)}
						class="flex-1 rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
						disabled={creating}
					>
						{$t('common.cancel')}
					</button>
					<button
						on:click={() => createAppointment(createError.includes('Warning') || createError.includes('overlaps'))}
						class="flex-1 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
						disabled={creating}
					>
						{creating ? 'Creating...' : createError.includes('Warning') || createError.includes('overlaps') ? $t('professional.proceedAnyway') : $t('common.create')}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.input {
		@apply rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500;
	}
</style>
