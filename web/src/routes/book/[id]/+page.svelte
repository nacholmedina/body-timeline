<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { BRANDING } from '$lib/config/branding';
	import { Calendar, Clock, User, ChevronLeft, ChevronRight, Check, Wifi } from 'lucide-svelte';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import LanguageToggle from '$components/LanguageToggle.svelte';

	import { PUBLIC_API_URL } from '$env/static/public';
	const BASE = PUBLIC_API_URL || 'http://localhost:5001/api/v1';

	let professionalId = '';
	let professional: any = null;
	let loading = true;
	let error = '';

	// Booking form state
	interface Slot {
		time: string;
		is_online_only: boolean;
	}
	let step: 'date' | 'time' | 'details' | 'done' = 'date';
	let selectedDate = '';
	let selectedSlot = '';
	let selectedSlotOnlineOnly = false;
	let slots: Slot[] = [];
	let slotDuration = 30;
	let loadingSlots = false;
	let guestName = '';
	let guestEmail = '';
	let guestPhone = '';
	let notes = '';
	let booking = false;
	let bookingError = '';

	// Calendar
	let currentMonth = new Date();
	$: localeCode = $locale === 'es' ? 'es-ES' : 'en-US';
	$: monthLabel = currentMonth.toLocaleString(localeCode, { month: 'long', year: 'numeric' });

	$: professionalId = $page.params.id;

	onMount(async () => {
		await loadProfessional();
	});

	async function loadProfessional() {
		try {
			const res = await fetch(`${BASE}/availability/${professionalId}/public`);
			if (!res.ok) throw new Error('not found');
			professional = await res.json();
		} catch {
			error = 'not_found';
		} finally {
			loading = false;
		}
	}

	function getCalendarDays(): (Date | null)[] {
		const year = currentMonth.getFullYear();
		const month = currentMonth.getMonth();
		const firstDay = new Date(year, month, 1);
		const lastDay = new Date(year, month + 1, 0);
		const startDow = firstDay.getDay();

		const days: (Date | null)[] = [];
		for (let i = 0; i < startDow; i++) days.push(null);
		for (let d = 1; d <= lastDay.getDate(); d++) {
			days.push(new Date(year, month, d));
		}
		return days;
	}

	$: calendarDays = getCalendarDays();

	function prevMonth() {
		const d = new Date(currentMonth);
		d.setMonth(d.getMonth() - 1);
		currentMonth = d;
	}

	function nextMonth() {
		const d = new Date(currentMonth);
		d.setMonth(d.getMonth() + 1);
		currentMonth = d;
	}

	function isToday(date: Date): boolean {
		const t = new Date();
		return date.getDate() === t.getDate() && date.getMonth() === t.getMonth() && date.getFullYear() === t.getFullYear();
	}

	// Compare against the server's "today" so the calendar doesn't disable
	// real future dates when the user's clock is wrong or in an aggressive
	// timezone. Reactive so the grid re-renders once the profile loads.
	$: todayStr = professional?.today || (() => {
		const d = new Date();
		d.setHours(0, 0, 0, 0);
		return toDateStr(d);
	})();
	$: isPast = (date: Date) => toDateStr(date) < todayStr;

	function isSelected(date: Date): boolean {
		return selectedDate === toDateStr(date);
	}

	function toDateStr(date: Date): string {
		const y = date.getFullYear();
		const m = String(date.getMonth() + 1).padStart(2, '0');
		const d = String(date.getDate()).padStart(2, '0');
		return `${y}-${m}-${d}`;
	}

	async function selectDate(date: Date) {
		if (isPast(date)) return;
		selectedDate = toDateStr(date);
		selectedSlot = '';
		selectedSlotOnlineOnly = false;
		loadingSlots = true;

		try {
			const res = await fetch(`${BASE}/availability/${professionalId}/public/slots?date=${selectedDate}`);
			if (!res.ok) throw new Error('failed');
			const data = await res.json();
			slots = (data.slots || []).map((s: any) =>
				typeof s === 'string'
					? { time: s, is_online_only: false }
					: { time: s.time, is_online_only: !!s.is_online_only }
			);
			slotDuration = data.slot_duration_minutes || 30;
		} catch {
			slots = [];
		} finally {
			loadingSlots = false;
		}

		step = 'time';
	}

	function selectSlot(slot: Slot) {
		selectedSlot = slot.time;
		selectedSlotOnlineOnly = slot.is_online_only;
		step = 'details';
	}

	function backToDate() {
		step = 'date';
		selectedSlot = '';
	}

	function backToTime() {
		step = 'time';
		bookingError = '';
	}

	async function submitBooking() {
		if (!guestName.trim() || !guestEmail.trim()) {
			bookingError = $t('publicBooking.nameEmailRequired');
			return;
		}

		booking = true;
		bookingError = '';

		try {
			const res = await fetch(`${BASE}/availability/${professionalId}/public/book`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					name: guestName.trim(),
					email: guestEmail.trim(),
					phone: guestPhone.trim() || undefined,
					date: selectedDate,
					slot_time: selectedSlot,
					notes: notes.trim() || undefined,
				}),
			});

			if (!res.ok) {
				const data = await res.json().catch(() => null);
				throw new Error(data?.message || data?.error || 'Booking failed');
			}

			step = 'done';
		} catch (err: any) {
			bookingError = err.message || $t('publicBooking.bookingFailed');
		} finally {
			booking = false;
		}
	}

	function formatSelectedDate(): string {
		if (!selectedDate) return '';
		const [y, m, d] = selectedDate.split('-').map(Number);
		const date = new Date(y, m - 1, d);
		return date.toLocaleDateString(localeCode, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
	}
</script>

<svelte:head>
	<title>{professional ? `${$t('publicBooking.bookWith')} ${professional.first_name} ${professional.last_name}` : $t('publicBooking.booking')} - {BRANDING.appName}</title>
</svelte:head>

<div class="min-h-screen bg-[var(--bg-primary)]">
	<!-- Top bar -->
	<div class="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
		<div class="mx-auto max-w-lg flex items-center justify-between px-4 py-3">
			<span class="text-lg font-bold text-[var(--text-primary)]">{BRANDING.appName}</span>
			<div class="flex items-center gap-2">
				<LanguageToggle />
				<ThemeToggle />
			</div>
		</div>
	</div>

	<div class="mx-auto max-w-lg px-4 py-8">
		{#if loading}
			<div class="flex items-center justify-center py-20">
				<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
			</div>
		{:else if error === 'not_found'}
			<div class="text-center py-20">
				<p class="text-lg font-medium text-[var(--text-primary)]">{$t('publicBooking.notFound')}</p>
				<p class="mt-2 text-sm text-[var(--text-secondary)]">{$t('publicBooking.notFoundDesc')}</p>
			</div>
		{:else if professional}
			<!-- Professional header -->
			<div class="text-center mb-8">
				{#if professional.avatar_url}
					<img src={professional.avatar_url} alt="" class="mx-auto h-20 w-20 rounded-full object-cover mb-3" />
				{:else}
					<div class="mx-auto h-20 w-20 rounded-full bg-brand-100 dark:bg-brand-900 flex items-center justify-center mb-3">
						<User size={32} class="text-brand-600 dark:text-brand-400" />
					</div>
				{/if}
				<h1 class="text-xl font-bold text-[var(--text-primary)]">
					{professional.first_name} {professional.last_name}
				</h1>
				{#if professional.bio}
					<p class="mt-1 text-sm text-[var(--text-secondary)]">{professional.bio}</p>
				{/if}
				<p class="mt-2 text-sm text-brand-600 dark:text-brand-400">{$t('publicBooking.selectTimeSlot')}</p>
			</div>

			<!-- Steps indicator -->
			{#if step !== 'done'}
				<div class="flex items-center justify-center gap-2 mb-6">
					{#each ['date', 'time', 'details'] as s, i}
						<div class="flex items-center gap-2">
							<div class="h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium
								{step === s ? 'bg-brand-600 text-white' :
								 ['date', 'time', 'details'].indexOf(step) > i ? 'bg-brand-100 dark:bg-brand-900 text-brand-600 dark:text-brand-400' :
								 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'}">
								{i + 1}
							</div>
							{#if i < 2}
								<div class="w-8 h-0.5 bg-[var(--border-color)]"></div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}

			<!-- Step: Select Date -->
			{#if step === 'date'}
				<div class="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-4">
					<div class="flex items-center justify-between mb-4">
						<button on:click={prevMonth} class="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] transition-colors">
							<ChevronLeft size={20} />
						</button>
						<span class="text-sm font-semibold text-[var(--text-primary)] capitalize">{monthLabel}</span>
						<button on:click={nextMonth} class="p-2 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] transition-colors">
							<ChevronRight size={20} />
						</button>
					</div>

					<div class="grid grid-cols-7 gap-1 mb-2">
						{#each [$t('professional.sun'), $t('professional.mon'), $t('professional.tue'), $t('professional.wed'), $t('professional.thu'), $t('professional.fri'), $t('professional.sat')] as day}
							<div class="text-center text-xs font-medium text-[var(--text-secondary)] py-1">{day}</div>
						{/each}
					</div>

					<div class="grid grid-cols-7 gap-1">
						{#each calendarDays as day}
							{#if day === null}
								<div></div>
							{:else}
								<button
									on:click={() => selectDate(day)}
									disabled={isPast(day)}
									class="aspect-square rounded-lg text-sm font-medium transition-colors
										{isPast(day) ? 'text-[var(--text-secondary)] opacity-30 cursor-not-allowed' :
										 isSelected(day) ? 'bg-brand-600 text-white' :
										 isToday(day) ? 'bg-brand-100 dark:bg-brand-900 text-brand-600 dark:text-brand-400 hover:bg-brand-200 dark:hover:bg-brand-800' :
										 'text-[var(--text-primary)] hover:bg-[var(--bg-primary)]'}"
								>
									{day.getDate()}
								</button>
							{/if}
						{/each}
					</div>
				</div>

			<!-- Step: Select Time -->
			{:else if step === 'time'}
				<div class="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-4">
					<button on:click={backToDate} class="flex items-center gap-1 text-sm text-brand-600 dark:text-brand-400 hover:underline mb-4">
						<ChevronLeft size={16} />
						{$t('publicBooking.changeDate')}
					</button>

					<div class="flex items-center gap-2 mb-4">
						<Calendar size={16} class="text-[var(--text-secondary)]" />
						<span class="text-sm font-medium text-[var(--text-primary)] capitalize">{formatSelectedDate()}</span>
					</div>

					{#if loadingSlots}
						<div class="flex items-center justify-center py-8">
							<div class="h-6 w-6 animate-spin rounded-full border-3 border-brand-200 border-t-brand-600"></div>
						</div>
					{:else if slots.length === 0}
						<p class="text-center py-8 text-sm text-[var(--text-secondary)]">{$t('publicBooking.noSlots')}</p>
					{:else}
						<div class="grid grid-cols-3 gap-2">
							{#each slots as slot}
								<button
									on:click={() => selectSlot(slot)}
									class="rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors flex flex-col items-center gap-0.5
										{selectedSlot === slot.time
											? 'border-brand-500 bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400'
											: 'border-[var(--border-color)] text-[var(--text-primary)] hover:border-brand-300 hover:bg-brand-50/50 dark:hover:bg-brand-950/50'}"
								>
									<span>{slot.time}</span>
									{#if slot.is_online_only}
										<span class="flex items-center gap-1 text-[10px] font-medium text-brand-600 dark:text-brand-400">
											<Wifi size={10} />
											{$t('availability.onlineOnly')}
										</span>
									{/if}
								</button>
							{/each}
						</div>
						<p class="mt-3 text-xs text-[var(--text-secondary)] text-center">
							<Clock size={12} class="inline" /> {slotDuration} min
						</p>
					{/if}
				</div>

			<!-- Step: Guest Details -->
			{:else if step === 'details'}
				<div class="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-4">
					<button on:click={backToTime} class="flex items-center gap-1 text-sm text-brand-600 dark:text-brand-400 hover:underline mb-4">
						<ChevronLeft size={16} />
						{$t('publicBooking.changeTime')}
					</button>

					<div class="mb-6 p-3 rounded-lg bg-[var(--bg-primary)]">
						<div class="flex items-center gap-4">
							<div class="flex items-center gap-2 text-sm text-[var(--text-primary)]">
								<Calendar size={14} class="text-[var(--text-secondary)]" />
								<span class="capitalize">{formatSelectedDate()}</span>
							</div>
							<div class="flex items-center gap-2 text-sm text-[var(--text-primary)]">
								<Clock size={14} class="text-[var(--text-secondary)]" />
								<span>{selectedSlot} ({slotDuration} min)</span>
							</div>
						</div>
						{#if selectedSlotOnlineOnly}
							<div class="mt-2 flex items-center gap-1.5 text-xs font-medium text-brand-600 dark:text-brand-400">
								<Wifi size={12} />
								{$t('availability.onlineOnlyHint')}
							</div>
						{/if}
					</div>

					<div class="space-y-4">
						<div>
							<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('publicBooking.yourName')} *</label>
							<input type="text" bind:value={guestName} class="w-full rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2.5 text-[var(--text-primary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" placeholder={$t('publicBooking.namePlaceholder')} />
						</div>

						<div>
							<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('publicBooking.yourEmail')} *</label>
							<input type="email" bind:value={guestEmail} class="w-full rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2.5 text-[var(--text-primary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" placeholder={$t('publicBooking.emailPlaceholder')} />
						</div>

						<div>
							<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('publicBooking.yourPhone')}</label>
							<input type="tel" bind:value={guestPhone} class="w-full rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2.5 text-[var(--text-primary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" placeholder={$t('publicBooking.phonePlaceholder')} />
						</div>

						<div>
							<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('publicBooking.notesOptional')}</label>
							<textarea bind:value={notes} rows="2" class="w-full rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2.5 text-[var(--text-primary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" placeholder={$t('publicBooking.notesPlaceholder')}></textarea>
						</div>

						{#if bookingError}
							<p class="text-sm text-red-600 dark:text-red-400">{bookingError}</p>
						{/if}

						<button
							on:click={submitBooking}
							disabled={booking}
							class="w-full rounded-lg bg-brand-600 px-4 py-3 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
						>
							{booking ? $t('common.loading') : $t('publicBooking.confirmBooking')}
						</button>
					</div>
				</div>

			<!-- Step: Done -->
			{:else if step === 'done'}
				<div class="rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-8 text-center">
					<div class="mx-auto h-16 w-16 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mb-4">
						<Check size={32} class="text-green-600 dark:text-green-400" />
					</div>
					<h2 class="text-xl font-bold text-[var(--text-primary)] mb-2">{$t('publicBooking.confirmed')}</h2>
					<p class="text-sm text-[var(--text-secondary)] mb-4">{$t('publicBooking.confirmedDesc')}</p>

					<div class="inline-flex flex-col items-center gap-2 rounded-lg bg-[var(--bg-primary)] px-4 py-3 text-sm text-[var(--text-primary)]">
						<div class="flex items-center gap-4">
							<span class="flex items-center gap-1">
								<Calendar size={14} class="text-[var(--text-secondary)]" />
								<span class="capitalize">{formatSelectedDate()}</span>
							</span>
							<span class="flex items-center gap-1">
								<Clock size={14} class="text-[var(--text-secondary)]" />
								{selectedSlot}
							</span>
						</div>
						{#if selectedSlotOnlineOnly}
							<div class="flex items-center gap-1.5 text-xs font-medium text-brand-600 dark:text-brand-400">
								<Wifi size={12} />
								{$t('availability.onlineOnlyHint')}
							</div>
						{/if}
					</div>

					<p class="mt-6 text-xs text-[var(--text-secondary)]">
						{$t('publicBooking.with')} {professional.first_name} {professional.last_name}
					</p>
				</div>
			{/if}
		{/if}
	</div>
</div>
