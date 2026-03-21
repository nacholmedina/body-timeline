<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api } from '$lib/api/client';
	import { Calendar, Clock, X, Check } from 'lucide-svelte';

	export let professionalId: string;
	export let professionalName: string = '';
	export let onBooked: () => void = () => {};

	let showModal = false;
	let selectedDate = '';
	let slots: string[] = [];
	let slotDuration = 30;
	let selectedSlot: string | null = null;
	let notes = '';
	let loadingSlots = false;
	let booking = false;
	let error = '';
	let successMessage = '';

	// Available days from the professional's schedule
	let availableDays: number[] = []; // day_of_week values
	let bookingWindowDays = 30;

	$: localeCode = $locale === 'es' ? 'es-ES' : 'en-US';

	onMount(async () => {
		try {
			const res = await api.get(`/availability/${professionalId}`);
			const schedule = res.schedule || [];
			availableDays = schedule.filter((s: any) => s.is_active).map((s: any) => s.day_of_week);
			if (schedule.length > 0) {
				bookingWindowDays = schedule[0].booking_window_days;
			}
		} catch (err) {
			console.error('Failed to load availability:', err);
		}
	});

	function openModal() {
		showModal = true;
		selectedDate = '';
		slots = [];
		selectedSlot = null;
		notes = '';
		error = '';
		successMessage = '';
	}

	async function loadSlots() {
		if (!selectedDate) return;
		loadingSlots = true;
		error = '';
		selectedSlot = null;
		try {
			const res = await api.get(`/availability/${professionalId}/slots`, { date: selectedDate });
			slots = res.slots || [];
			slotDuration = res.slot_duration_minutes || 30;
		} catch (err: any) {
			console.error('Failed to load slots:', err);
			slots = [];
		} finally {
			loadingSlots = false;
		}
	}

	async function bookSlot() {
		if (!selectedSlot || !selectedDate) return;
		booking = true;
		error = '';
		try {
			await api.post(`/availability/${professionalId}/book`, {
				date: selectedDate,
				slot_time: selectedSlot,
				notes: notes || undefined,
			});
			successMessage = $t('availability.bookingConfirmed');
			setTimeout(() => {
				showModal = false;
				onBooked();
			}, 1500);
		} catch (err: any) {
			error = err.data?.message || err.message || $t('availability.bookingFailed');
		} finally {
			booking = false;
		}
	}

	function getMinDate(): string {
		const d = new Date();
		d.setDate(d.getDate() + 1);
		return d.toISOString().split('T')[0];
	}

	function getMaxDate(): string {
		const d = new Date();
		d.setDate(d.getDate() + bookingWindowDays);
		return d.toISOString().split('T')[0];
	}
</script>

<!-- Book Button -->
{#if availableDays.length > 0}
	<button
		on:click={openModal}
		class="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors"
	>
		<Calendar size={18} />
		{$t('availability.bookAppointment')}
	</button>
{/if}

<!-- Booking Modal -->
{#if showModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl max-h-[90vh] overflow-y-auto">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-xl font-bold text-[var(--text-primary)]">{$t('availability.bookAppointment')}</h2>
				<button on:click={() => (showModal = false)} class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
					<X size={20} />
				</button>
			</div>

			{#if professionalName}
				<p class="text-sm text-[var(--text-secondary)] mb-4">{professionalName}</p>
			{/if}

			{#if successMessage}
				<div class="flex items-center gap-2 rounded-lg bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-800 p-4 text-green-700 dark:text-green-400">
					<Check size={20} />
					<span class="text-sm font-medium">{successMessage}</span>
				</div>
			{:else}
				<div class="space-y-4">
					<!-- Date Picker -->
					<div>
						<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('availability.selectDate')}</label>
						<input
							type="date"
							bind:value={selectedDate}
							on:change={loadSlots}
							min={getMinDate()}
							max={getMaxDate()}
							class="input w-full date-input"
						/>
					</div>

					<!-- Slots -->
					{#if loadingSlots}
						<div class="flex items-center justify-center py-6">
							<div class="h-6 w-6 animate-spin rounded-full border-3 border-brand-200 border-t-brand-600"></div>
							<span class="ml-2 text-sm text-[var(--text-secondary)]">{$t('availability.loadingSlots')}</span>
						</div>
					{:else if selectedDate && slots.length > 0}
						<div>
							<label class="mb-2 block text-sm font-medium text-[var(--text-primary)]">
								{$t('availability.availableSlots')} ({slotDuration} min)
							</label>
							<div class="grid grid-cols-3 gap-2">
								{#each slots as slot}
									<button
										on:click={() => (selectedSlot = slot)}
										class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors {selectedSlot === slot
											? 'border-brand-600 bg-brand-600 text-white'
											: 'border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]'}"
									>
										<span class="flex items-center justify-center gap-1">
											<Clock size={12} />
											{slot}
										</span>
									</button>
								{/each}
							</div>
						</div>
					{:else if selectedDate}
						<p class="text-sm text-[var(--text-secondary)] text-center py-4">{$t('availability.noSlotsAvailable')}</p>
					{/if}

					<!-- Notes -->
					{#if selectedSlot}
						<div>
							<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.notes')} ({$t('common.optional')})</label>
							<textarea bind:value={notes} class="input w-full" rows="2" />
						</div>
					{/if}

					{#if error}
						<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
					{/if}

					<!-- Actions -->
					<div class="flex gap-3">
						<button
							on:click={() => (showModal = false)}
							class="flex-1 rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
						>
							{$t('common.cancel')}
						</button>
						<button
							on:click={bookSlot}
							class="flex-1 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
							disabled={!selectedSlot || booking}
						>
							{booking ? $t('common.loading') : $t('availability.confirmBooking')}
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.input {
		@apply rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500;
	}
	.date-input::-webkit-calendar-picker-indicator {
		filter: invert(0.5);
	}
	:global(.dark) .date-input::-webkit-calendar-picker-indicator {
		filter: invert(0.7);
	}
</style>
