<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime } from '$lib/utils';
	import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, Plus, X, Clock, User, Trash2, XCircle, RefreshCw, Settings, Share2, Copy, Check as CheckIcon } from 'lucide-svelte';
	import ConfirmModal from '$components/ConfirmModal.svelte';
	import AvailabilitySettings from '$components/AvailabilitySettings.svelte';
	import GoogleCalendarConnect from '$components/GoogleCalendarConnect.svelte';
	import { authStore } from '$lib/stores/auth';

	type ViewMode = 'day' | 'week' | 'month' | 'availability';

	let view: ViewMode = 'month';
	let currentDate = new Date();
	let appointments: any[] = [];
	let patients: any[] = [];
	let loading = true;

	// Delete confirmation
	let showDeleteConfirm = false;
	let appointmentToDelete: string | null = null;
	let deleting = false;

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

	// Reschedule modal
	let showRescheduleModal = false;
	let rescheduleAppt: any = null;
	let rescheduleDate = '';
	let rescheduleTime = '';
	let rescheduling = false;
	let rescheduleError = '';

	// Share
	let showShareMenu = false;
	let linkCopied = false;

	$: bookingUrl = typeof window !== 'undefined' && $authStore.user?.id
		? `${window.location.origin}/book/${$authStore.user.id}`
		: '';

	function toggleShareMenu() {
		showShareMenu = !showShareMenu;
		linkCopied = false;
	}

	function closeShareMenu() {
		showShareMenu = false;
	}

	async function copyLink() {
		await navigator.clipboard.writeText(bookingUrl);
		linkCopied = true;
		setTimeout(() => { linkCopied = false; }, 2000);
	}

	async function shareInstagram() {
		if (navigator.share) {
			try {
				await navigator.share({
					title: $t('share.bookTitle'),
					text: $t('share.bookMessage'),
					url: bookingUrl,
				});
			} catch {}
		} else {
			await navigator.clipboard.writeText(bookingUrl);
			linkCopied = true;
			setTimeout(() => { linkCopied = false; }, 2000);
		}
		showShareMenu = false;
	}

	function shareWhatsApp() {
		const text = `${$t('share.bookMessage')}\n${bookingUrl}`;
		window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
		showShareMenu = false;
	}

	function shareFacebook() {
		window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(bookingUrl)}`, '_blank', 'width=600,height=400');
		showShareMenu = false;
	}

	// Calendar state
	let calendarDays: Date[] = [];
	let weekDays: Date[] = [];

	$: localeCode = $locale === 'es' ? 'es-ES' : 'en-US';
	$: monthName = currentDate.toLocaleString(localeCode, { month: 'long', year: 'numeric' });

	// Auto-fill title when patient changes
	$: if (selectedPatientId && patients.length > 0) {
		const patient = patients.find((p: any) => p.id === selectedPatientId);
		if (patient && !appointmentTitle) {
			appointmentTitle = `${patient.first_name} ${patient.last_name}`;
		}
	}

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

			const startDate = new Date(firstDay);
			startDate.setDate(startDate.getDate() - startDate.getDay());

			const endDate = new Date(lastDay);
			endDate.setDate(endDate.getDate() + (6 - endDate.getDay()));

			calendarDays = [];
			const current = new Date(startDate);
			while (current <= endDate) {
				calendarDays.push(new Date(current));
				current.setDate(current.getDate() + 1);
			}
		} else if (view === 'week') {
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
		if (view === 'month') newDate.setMonth(newDate.getMonth() - 1);
		else if (view === 'week') newDate.setDate(newDate.getDate() - 7);
		else newDate.setDate(newDate.getDate() - 1);
		currentDate = newDate;
	}

	function nextPeriod() {
		const newDate = new Date(currentDate);
		if (view === 'month') newDate.setMonth(newDate.getMonth() + 1);
		else if (view === 'week') newDate.setDate(newDate.getDate() + 7);
		else newDate.setDate(newDate.getDate() + 1);
		currentDate = newDate;
	}

	function today() {
		currentDate = new Date();
	}

	function getAppointmentsForDay(date: Date): any[] {
		const dateStr = date.toISOString().split('T')[0];
		return appointments.filter((appt) => {
			const apptDate = new Date(appt.scheduled_at).toISOString().split('T')[0];
			return apptDate === dateStr;
		});
	}

	function selectDay(date: Date) {
		currentDate = new Date(date);
		view = 'day';
	}

	function isToday(date: Date): boolean {
		const t = new Date();
		return date.getDate() === t.getDate() && date.getMonth() === t.getMonth() && date.getFullYear() === t.getFullYear();
	}

	function isCurrentMonth(date: Date): boolean {
		return date.getMonth() === currentDate.getMonth();
	}

	// --- Appointment actions ---
	async function cancelAppointment(appt: any) {
		if (!confirm($t('appointments.confirmCancel'))) return;
		try {
			await api.patch(`/appointments/${appt.id}`, { status: 'cancelled' });
			appointments = appointments.map(a => a.id === appt.id ? { ...a, status: 'cancelled' } : a);
		} catch (err: any) {
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
		} catch (err: any) {
			console.error('Failed to delete appointment:', err);
		} finally {
			deleting = false;
		}
	}

	function openReschedule(appt: any) {
		rescheduleAppt = appt;
		const d = new Date(appt.scheduled_at);
		rescheduleDate = d.toISOString().split('T')[0];
		rescheduleTime = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
		rescheduleError = '';
		showRescheduleModal = true;
	}

	async function rescheduleAppointment() {
		if (!rescheduleDate || !rescheduleTime) {
			rescheduleError = $t('professional.fillRequiredFields');
			return;
		}
		rescheduling = true;
		rescheduleError = '';
		try {
			const scheduled_at = `${rescheduleDate}T${rescheduleTime}:00`;
			const res = await api.patch(`/appointments/${rescheduleAppt.id}`, { scheduled_at });
			appointments = appointments.map(a => a.id === rescheduleAppt.id ? res.data : a);
			showRescheduleModal = false;
			rescheduleAppt = null;
		} catch (err: any) {
			rescheduleError = err.message || 'Failed';
		} finally {
			rescheduling = false;
		}
	}

	// --- Create appointment ---
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

			if (scheduledDate < now && !forceCreate) {
				createError = $t('professional.cannotSchedulePast');
				creating = false;
				return;
			}

			// Skip conflict detection for non-registered patients
			const conflicts = selectedPatientId !== 'other' ? appointments.filter((appt) => {
				if (String(appt.patient_id) !== String(selectedPatientId) || appt.status === 'cancelled') return false;
				const apptStart = new Date(appt.scheduled_at);
				const apptEnd = new Date(apptStart.getTime() + appt.duration_minutes * 60000);
				const newEnd = new Date(scheduledDate.getTime() + appointmentDuration * 60000);
				return (scheduledDate < apptEnd && newEnd > apptStart);
			}) : [];

			if (conflicts.length > 0 && !forceCreate) {
				const conflictTimes = conflicts.map(c =>
					new Date(c.scheduled_at).toLocaleTimeString(localeCode, { hour: '2-digit', minute: '2-digit' })
				).join(', ');
				createError = `${$t('appointments.overlapWarning')} ${conflictTimes}. ${$t('professional.proceedAnyway')}`;
				creating = false;
				return;
			}

			await api.post('/appointments', {
				patient_id: selectedPatientId === 'other' ? null : selectedPatientId,
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
		const d = new Date();
		appointmentDate = d.toISOString().split('T')[0];
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
			<p class="text-sm text-[var(--text-secondary)]">{appointments.filter(a => a.status !== 'cancelled').length} {$t('nav.appointments').toLowerCase()}</p>
		</div>
		<div class="flex items-center gap-2">
			<button
				on:click|stopPropagation={toggleShareMenu}
				class="flex items-center gap-2 rounded-lg border border-[var(--border-color)] px-3 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
			>
				<Share2 size={18} />
				<span class="hidden sm:inline">{$t('share.shareLink')}</span>
			</button>

			<button
				on:click={openCreateModal}
				class="flex items-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors"
			>
				<Plus size={18} />
				<span class="hidden sm:inline">{$t('professional.createAppointment')}</span>
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else}
		<!-- Calendar Controls -->
		<div class="card">
			<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
				<div class="flex rounded-lg border border-[var(--border-color)] overflow-hidden">
					{#each ['day', 'week', 'month'] as v}
						<button
							on:click={() => (view = v)}
							class="px-3 py-2 text-sm font-medium transition-colors {view === v
								? 'bg-brand-600 text-white'
								: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
						>
							{$t(`professional.${v}View`)}
						</button>
					{/each}
					<button
						on:click={() => (view = 'availability')}
						class="flex items-center gap-1 px-3 py-2 text-sm font-medium transition-colors {view === 'availability'
							? 'bg-brand-600 text-white'
							: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
					>
						<Settings size={14} />
						{$t('availability.availabilityView')}
					</button>
				</div>

				<div class="flex items-center gap-3">
					<button on:click={prevPeriod} class="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors">
						<ChevronLeft size={20} />
					</button>
					<button on:click={today} class="px-3 py-1.5 rounded-lg text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors">
						{$t('professional.today')}
					</button>
					<button on:click={nextPeriod} class="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors">
						<ChevronRight size={20} />
					</button>
					<span class="text-sm font-medium text-[var(--text-primary)]">{monthName}</span>
				</div>
			</div>
		</div>

		<!-- Calendar View -->
		{#if view === 'month'}
			<div class="card overflow-x-auto">
				<div class="grid grid-cols-7 gap-px bg-[var(--border-color)] border border-[var(--border-color)] rounded-t-lg overflow-hidden">
					{#each [$t('professional.sun'), $t('professional.mon'), $t('professional.tue'), $t('professional.wed'), $t('professional.thu'), $t('professional.fri'), $t('professional.sat')] as day}
						<div class="bg-[var(--bg-secondary)] p-1.5 sm:p-2 text-center text-xs font-medium text-[var(--text-secondary)]">{day}</div>
					{/each}
				</div>
				<div class="grid grid-cols-7 gap-px bg-[var(--border-color)] border-x border-b border-[var(--border-color)] rounded-b-lg overflow-hidden">
					{#each calendarDays as day}
						{@const dayAppointments = getAppointmentsForDay(day)}
						<button
							on:click={() => selectDay(day)}
							class="bg-white dark:bg-gray-900 min-h-12 sm:min-h-24 p-1 sm:p-2 text-left hover:bg-[var(--bg-secondary)] transition-colors cursor-pointer {isCurrentMonth(day) ? '' : 'opacity-40'}"
						>
							<span class="text-xs sm:text-sm font-medium {isToday(day) ? 'flex h-5 w-5 sm:h-6 sm:w-6 items-center justify-center rounded-full bg-brand-600 text-white' : 'text-[var(--text-primary)]'}">
								{day.getDate()}
							</span>
							<!-- Mobile: dot indicators only -->
							{#if dayAppointments.length > 0}
								<div class="mt-1 flex gap-0.5 sm:hidden justify-center">
									{#each dayAppointments.slice(0, 3) as appt}
										<span class="h-1.5 w-1.5 rounded-full {appt.status === 'cancelled' ? 'bg-red-400' : 'bg-brand-500'}"></span>
									{/each}
								</div>
							{/if}
							<!-- Desktop: appointment pills -->
							<div class="mt-1 space-y-1 hidden sm:block">
								{#each dayAppointments.slice(0, 2) as appt}
									<div class="rounded px-2 py-1 text-xs {appt.status === 'cancelled'
										? 'bg-red-100 dark:bg-red-900/40'
										: 'bg-brand-100 dark:bg-brand-900'}">
										<p class="font-medium truncate {appt.status === 'cancelled'
											? 'text-red-600 dark:text-red-400 line-through'
											: 'text-brand-700 dark:text-brand-300'}">
											{new Date(appt.scheduled_at).toLocaleTimeString(localeCode, { hour: '2-digit', minute: '2-digit' })}
										</p>
										<p class="truncate {appt.status === 'cancelled' ? 'text-red-500/70 dark:text-red-400/60 line-through' : 'text-[var(--text-secondary)]'}">{appt.title}</p>
									</div>
								{/each}
								{#if dayAppointments.length > 2}
									<p class="text-xs text-[var(--text-secondary)]">+{dayAppointments.length - 2} {$t('common.more')}</p>
								{/if}
							</div>
						</button>
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
									<div class="rounded-lg border p-3 {appt.status === 'cancelled'
										? 'border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950/40'
										: 'border-[var(--border-color)] bg-[var(--bg-secondary)]'}">
										<div class="flex items-start justify-between">
											<div class="flex-1">
												<div class="flex items-center gap-2">
													<p class="font-medium {appt.status === 'cancelled' ? 'text-red-600 dark:text-red-400 line-through' : 'text-[var(--text-primary)]'}">{appt.title}</p>
													{#if appt.status === 'cancelled'}
														<span class="rounded-full bg-red-100 dark:bg-red-900 px-2 py-0.5 text-[0.65rem] font-medium text-red-600 dark:text-red-400">{$t('appointments.cancelled')}</span>
													{/if}
												</div>
												<div class="mt-1 flex items-center gap-3 text-xs text-[var(--text-secondary)]">
													<span class="flex items-center gap-1">
														<Clock size={12} />
														{new Date(appt.scheduled_at).toLocaleTimeString(localeCode, { hour: '2-digit', minute: '2-digit' })}
													</span>
													{#if appt.patient_name}
														<span class="flex items-center gap-1">
															<User size={12} />
															{appt.patient_name}
														</span>
													{/if}
												</div>
											</div>
											{#if appt.status !== 'cancelled'}
												<div class="flex gap-1 ml-2">
													<button on:click={() => openReschedule(appt)} class="p-1.5 rounded text-[var(--text-secondary)] hover:bg-brand-50 dark:hover:bg-brand-950 hover:text-brand-600" title={$t('appointments.reschedule')}>
														<RefreshCw size={14} />
													</button>
													<button on:click={() => cancelAppointment(appt)} class="p-1.5 rounded text-[var(--text-secondary)] hover:bg-amber-50 dark:hover:bg-amber-950 hover:text-amber-600" title={$t('appointments.cancel')}>
														<XCircle size={14} />
													</button>
													<button on:click={() => deleteAppointment(appt.id)} class="p-1.5 rounded text-[var(--text-secondary)] hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600" title={$t('appointments.delete')}>
														<Trash2 size={14} />
													</button>
												</div>
											{/if}
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
							<div class="rounded-lg border p-4 {appt.status === 'cancelled'
								? 'border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950/40'
								: 'border-[var(--border-color)] bg-[var(--bg-secondary)]'}">
								<div class="flex items-start justify-between mb-2">
									<div class="flex-1">
										<div class="flex items-center gap-2">
											<p class="font-semibold {appt.status === 'cancelled' ? 'text-red-600 dark:text-red-400 line-through' : 'text-[var(--text-primary)]'}">{appt.title}</p>
											{#if appt.status === 'cancelled'}
												<span class="rounded-full bg-red-100 dark:bg-red-900 px-2 py-0.5 text-[0.65rem] font-medium text-red-600 dark:text-red-400">{$t('appointments.cancelled')}</span>
											{/if}
										</div>
										<div class="mt-1 flex items-center gap-3 text-sm text-[var(--text-secondary)]">
											<span class="flex items-center gap-1">
												<Clock size={14} />
												{new Date(appt.scheduled_at).toLocaleTimeString(localeCode, { hour: '2-digit', minute: '2-digit' })} ({appt.duration_minutes} min)
											</span>
											{#if appt.patient_name}
												<span class="flex items-center gap-1">
													<User size={14} />
													{appt.patient_name}
												</span>
											{/if}
										</div>
									</div>
									{#if appt.status !== 'cancelled'}
										<div class="flex gap-1 ml-2">
											<button on:click={() => openReschedule(appt)} class="p-1.5 rounded text-[var(--text-secondary)] hover:bg-brand-50 dark:hover:bg-brand-950 hover:text-brand-600" title={$t('appointments.reschedule')}>
												<RefreshCw size={14} />
											</button>
											<button on:click={() => cancelAppointment(appt)} class="p-1.5 rounded text-[var(--text-secondary)] hover:bg-amber-50 dark:hover:bg-amber-950 hover:text-amber-600" title={$t('appointments.cancel')}>
												<XCircle size={14} />
											</button>
											<button on:click={() => deleteAppointment(appt.id)} class="p-1.5 rounded text-[var(--text-secondary)] hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600" title={$t('appointments.delete')}>
												<Trash2 size={14} />
											</button>
										</div>
									{/if}
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
		{:else if view === 'availability'}
			{#if $authStore.user?.id}
				<div class="space-y-6">
					<AvailabilitySettings professionalId={$authStore.user.id} />
					<GoogleCalendarConnect />
				</div>
			{/if}
		{/if}
	{/if}
</div>

<!-- Share Bottom Sheet -->
{#if showShareMenu}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50" on:click={closeShareMenu}>
		<div on:click|stopPropagation class="w-full sm:max-w-sm rounded-t-2xl sm:rounded-2xl bg-white dark:bg-gray-800 shadow-xl overflow-hidden">
			<!-- Handle bar (mobile) -->
			<div class="flex justify-center pt-3 pb-1 sm:hidden">
				<div class="h-1 w-10 rounded-full bg-gray-300 dark:bg-gray-600"></div>
			</div>

			<div class="p-4">
				<h3 class="text-lg font-semibold text-[var(--text-primary)] mb-4">{$t('share.shareLink')}</h3>

				<!-- Link copy -->
				<div class="flex items-center gap-2 mb-4">
					<input
						type="text"
						value={bookingUrl}
						readonly
						class="flex-1 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-primary)] truncate"
					/>
					<button
						on:click={copyLink}
						class="rounded-lg px-3 py-2 text-sm font-medium transition-colors {linkCopied ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}"
					>
						{#if linkCopied}
							<CheckIcon size={18} />
						{:else}
							<Copy size={18} />
						{/if}
					</button>
				</div>

				<!-- Share buttons -->
				<div class="grid grid-cols-3 gap-3 mb-4">
					<button on:click={shareInstagram} class="flex flex-col items-center gap-2 rounded-xl p-3 hover:bg-[var(--bg-secondary)] transition-colors">
						<div class="h-12 w-12 rounded-full bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 flex items-center justify-center">
							<svg class="h-6 w-6 text-white" viewBox="0 0 24 24" fill="currentColor">
								<path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
							</svg>
						</div>
						<span class="text-xs font-medium text-[var(--text-primary)]">Instagram</span>
					</button>

					<button on:click={shareWhatsApp} class="flex flex-col items-center gap-2 rounded-xl p-3 hover:bg-[var(--bg-secondary)] transition-colors">
						<div class="h-12 w-12 rounded-full bg-green-500 flex items-center justify-center">
							<svg class="h-6 w-6 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
						</div>
						<span class="text-xs font-medium text-[var(--text-primary)]">WhatsApp</span>
					</button>

					<button on:click={shareFacebook} class="flex flex-col items-center gap-2 rounded-xl p-3 hover:bg-[var(--bg-secondary)] transition-colors">
						<div class="h-12 w-12 rounded-full bg-blue-600 flex items-center justify-center">
							<svg class="h-6 w-6 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
						</div>
						<span class="text-xs font-medium text-[var(--text-primary)]">Facebook</span>
					</button>
				</div>

				<button on:click={closeShareMenu} class="w-full rounded-lg border border-[var(--border-color)] py-2.5 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors">
					{$t('common.cancel')}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Create Appointment Modal -->
{#if showCreateModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-xl font-bold text-[var(--text-primary)]">{$t('professional.createAppointment')}</h2>
				<button on:click={() => (showCreateModal = false)} class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
					<X size={20} />
				</button>
			</div>

			<div class="space-y-4">
				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.patient')} *</label>
					<select
						bind:value={selectedPatientId}
						on:change={() => {
							const patient = patients.find((p) => p.id === selectedPatientId);
							if (patient) appointmentTitle = `${patient.first_name} ${patient.last_name}`;
						}}
						class="input w-full"
					>
						<option value="">{$t('professional.selectPatient')}</option>
						{#each patients as patient}
							<option value={patient.id}>{patient.first_name} {patient.last_name}</option>
						{/each}
						<option value="other">{$t('appointments.otherPatient')}</option>
					</select>
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.appointmentTitle')} *</label>
					<input type="text" bind:value={appointmentTitle} class="input w-full" />
				</div>

				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.date')} *</label>
						<input type="date" bind:value={appointmentDate} class="input w-full date-input" />
					</div>
					<div>
						<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.time')} *</label>
						<input type="time" bind:value={appointmentTime} class="input w-full date-input" />
					</div>
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.duration')}</label>
					<input type="number" bind:value={appointmentDuration} class="input w-full" min="15" step="15" />
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.notes')} ({$t('common.optional')})</label>
					<textarea bind:value={appointmentNotes} class="input w-full" rows="3"></textarea>
				</div>

				{#if createError}
					<p class="text-sm {createError.includes('Warning') ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}">
						{createError}
					</p>
				{/if}

				<div class="flex gap-3">
					<button on:click={() => (showCreateModal = false)} class="flex-1 rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors" disabled={creating}>
						{$t('common.cancel')}
					</button>
					<button
						on:click={() => createAppointment(createError.includes('Warning') || createError.includes('overlaps'))}
						class="flex-1 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
						disabled={creating}
					>
						{creating ? $t('common.loading') : createError.includes('Warning') || createError.includes('overlaps') ? $t('professional.proceedAnyway') : $t('common.create')}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- Reschedule Modal -->
{#if showRescheduleModal && rescheduleAppt}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-sm rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-lg font-bold text-[var(--text-primary)]">{$t('appointments.reschedule')}</h2>
				<button on:click={() => (showRescheduleModal = false)} class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
					<X size={20} />
				</button>
			</div>
			<p class="mb-4 text-sm text-[var(--text-secondary)]">
				{rescheduleAppt.title}{#if rescheduleAppt.patient_name} — {rescheduleAppt.patient_name}{/if}
			</p>
			<div class="space-y-4">
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.date')} *</label>
						<input type="date" bind:value={rescheduleDate} class="input w-full date-input" />
					</div>
					<div>
						<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.time')} *</label>
						<input type="time" bind:value={rescheduleTime} class="input w-full date-input" />
					</div>
				</div>

				{#if rescheduleError}
					<p class="text-sm text-red-600 dark:text-red-400">{rescheduleError}</p>
				{/if}

				<div class="flex gap-3">
					<button on:click={() => (showRescheduleModal = false)} class="flex-1 rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors">
						{$t('common.cancel')}
					</button>
					<button on:click={rescheduleAppointment} class="flex-1 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50" disabled={rescheduling}>
						{rescheduling ? $t('common.loading') : $t('common.save')}
					</button>
				</div>
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

<style>
	.input {
		@apply rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500;
	}
	/* Fix dark calendar/clock icons in date/time inputs */
	.date-input::-webkit-calendar-picker-indicator {
		filter: invert(0.5);
	}
	:global(.dark) .date-input::-webkit-calendar-picker-indicator {
		filter: invert(0.7);
	}
</style>
