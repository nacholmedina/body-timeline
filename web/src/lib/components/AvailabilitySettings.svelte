<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { api } from '$lib/api/client';
	import { Save, Plus, Trash2, X, ShieldOff, Clock, Wifi } from 'lucide-svelte';

	export let professionalId: string;

	const DAY_KEYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const;

	interface TimeInterval {
		start_time: string;
		end_time: string;
		is_online_only: boolean;
	}

	interface DaySchedule {
		enabled: boolean;
		intervals: TimeInterval[];
	}

	interface Override {
		id: string;
		override_date: string;
		override_type: 'block' | 'extra';
		start_time: string | null;
		end_time: string | null;
	}

	let schedule: DaySchedule[] = Array.from({ length: 7 }, () => ({
		enabled: false,
		intervals: [{ start_time: '09:00', end_time: '17:00', is_online_only: false }],
	}));
	let slotDuration = 30;
	let bookingWindow = 30;
	let overrides: Override[] = [];

	let saving = false;
	let saveMessage = '';
	let saveError = false;
	let loading = true;

	// Override form
	let showOverrideForm = false;
	let overrideDate = '';
	let overrideType: 'block' | 'extra' = 'block';
	let overrideStartTime = '09:00';
	let overrideEndTime = '17:00';
	let addingOverride = false;

	onMount(async () => {
		try {
			const res = await api.get(`/availability/${professionalId}`);
			const rules = res.schedule || [];
			const existingOverrides = res.overrides || [];

			// Group rules by day_of_week (multiple intervals per day)
			const dayMap: Record<number, TimeInterval[]> = {};
			for (const rule of rules) {
				if (!dayMap[rule.day_of_week]) dayMap[rule.day_of_week] = [];
				dayMap[rule.day_of_week].push({
					start_time: rule.start_time,
					end_time: rule.end_time,
					is_online_only: !!rule.is_online_only,
				});
			}

			for (let i = 0; i < 7; i++) {
				if (dayMap[i] && dayMap[i].length > 0) {
					schedule[i] = { enabled: true, intervals: dayMap[i] };
				}
			}
			schedule = schedule;

			if (rules.length > 0) {
				slotDuration = rules[0].slot_duration_minutes;
				bookingWindow = rules[0].booking_window_days;
			}

			overrides = existingOverrides;
		} catch (err) {
			console.error('Failed to load availability:', err);
		} finally {
			loading = false;
		}
	});

	function addInterval(dayIndex: number) {
		schedule[dayIndex].intervals = [
			...schedule[dayIndex].intervals,
			{ start_time: '14:00', end_time: '18:00', is_online_only: false },
		];
	}

	function removeInterval(dayIndex: number, intervalIndex: number) {
		schedule[dayIndex].intervals = schedule[dayIndex].intervals.filter((_, idx) => idx !== intervalIndex);
		if (schedule[dayIndex].intervals.length === 0) {
			schedule[dayIndex].enabled = false;
			schedule[dayIndex].intervals = [{ start_time: '09:00', end_time: '17:00', is_online_only: false }];
		}
	}

	async function saveSchedule() {
		saving = true;
		saveMessage = '';
		saveError = false;
		try {
			const rules: { day_of_week: number; start_time: string; end_time: string; is_online_only: boolean }[] = [];
			for (let i = 0; i < 7; i++) {
				if (schedule[i].enabled) {
					for (const interval of schedule[i].intervals) {
						rules.push({
							day_of_week: i,
							start_time: interval.start_time,
							end_time: interval.end_time,
							is_online_only: interval.is_online_only,
						});
					}
				}
			}

			await api.put(`/availability/${professionalId}/schedule`, {
				rules,
				slot_duration_minutes: slotDuration,
				booking_window_days: bookingWindow,
			});
			saveMessage = $t('availability.scheduleUpdated');
			setTimeout(() => (saveMessage = ''), 3000);
		} catch (err: any) {
			saveError = true;
			saveMessage = err.message || $t('availability.scheduleFailed');
		} finally {
			saving = false;
		}
	}

	async function addOverride() {
		if (!overrideDate) return;
		addingOverride = true;
		try {
			const body: any = {
				override_date: overrideDate,
				override_type: overrideType,
			};
			if (overrideType === 'extra') {
				body.start_time = overrideStartTime;
				body.end_time = overrideEndTime;
			}
			const res = await api.post(`/availability/${professionalId}/overrides`, body);
			overrides = [...overrides, res.data];
			showOverrideForm = false;
			overrideDate = '';
		} catch (err: any) {
			console.error('Failed to add override:', err);
		} finally {
			addingOverride = false;
		}
	}

	async function removeOverride(id: string) {
		try {
			await api.delete(`/availability/${professionalId}/overrides/${id}`);
			overrides = overrides.filter((o) => o.id !== id);
		} catch (err: any) {
			console.error('Failed to delete override:', err);
		}
	}
</script>

{#if loading}
	<div class="flex items-center justify-center py-12">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
	</div>
{:else}
	<div class="space-y-6">
		<!-- Weekly Schedule -->
		<div class="card">
			<h3 class="text-lg font-semibold text-[var(--text-primary)] mb-4">{$t('availability.schedule')}</h3>

			<!-- Global settings -->
			<div class="grid grid-cols-2 gap-4 mb-6">
				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('availability.slotDuration')}</label>
					<input type="number" bind:value={slotDuration} class="input w-full" min="15" step="15" />
				</div>
				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('availability.bookingWindow')}</label>
					<input type="number" bind:value={bookingWindow} class="input w-full" min="1" max="365" />
				</div>
			</div>

			<!-- Day rows -->
			<div class="space-y-3">
				{#each DAY_KEYS as dayKey, i}
					<div class="rounded-lg border border-[var(--border-color)] p-3 {schedule[i].enabled ? 'bg-[var(--bg-secondary)]' : 'opacity-50'}">
						<label class="flex items-center gap-2 cursor-pointer">
							<input type="checkbox" bind:checked={schedule[i].enabled} class="rounded border-[var(--border-color)] text-brand-600 focus:ring-brand-500" />
							<span class="text-sm font-medium text-[var(--text-primary)]">{$t(`availability.${dayKey}`)}</span>
						</label>
						{#if schedule[i].enabled}
							<div class="mt-2 space-y-2 pl-6">
								{#each schedule[i].intervals as interval, j}
									<div class="flex items-center gap-2">
										<input type="time" bind:value={interval.start_time} class="input text-sm date-input flex-1 min-w-0" />
										<span class="text-[var(--text-secondary)] text-sm">-</span>
										<input type="time" bind:value={interval.end_time} class="input text-sm date-input flex-1 min-w-0" />
										<button
											type="button"
											on:click={() => (interval.is_online_only = !interval.is_online_only)}
											class="p-1 rounded shrink-0 transition-colors {interval.is_online_only
												? 'text-brand-600 bg-brand-50 dark:bg-brand-950 hover:bg-brand-100 dark:hover:bg-brand-900'
												: 'text-[var(--text-secondary)] hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-950'}"
											title={$t('availability.onlineOnly')}
											aria-label={$t('availability.onlineOnly')}
											aria-pressed={interval.is_online_only}
										>
											<Wifi size={14} />
										</button>
										{#if schedule[i].intervals.length > 1}
											<button
												on:click={() => removeInterval(i, j)}
												class="p-1 rounded text-[var(--text-secondary)] hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950 shrink-0"
												title={$t('common.delete')}
											>
												<Trash2 size={14} />
											</button>
										{/if}
									</div>
									{#if interval.is_online_only}
										<p class="pl-1 text-xs text-brand-600 dark:text-brand-400 flex items-center gap-1">
											<Wifi size={10} />
											{$t('availability.onlineOnly')}
										</p>
									{/if}
								{/each}
								<button
									on:click={() => addInterval(i)}
									class="flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700"
								>
									<Plus size={12} />
									{$t('availability.addInterval')}
								</button>
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<!-- Save button -->
			<div class="mt-4 flex items-center gap-3">
				<button
					on:click={saveSchedule}
					class="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
					disabled={saving}
				>
					<Save size={16} />
					{saving ? $t('common.saving') : $t('availability.saveSchedule')}
				</button>
				{#if saveMessage}
					<span class="text-sm {saveError ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}">{saveMessage}</span>
				{/if}
			</div>
		</div>

		<!-- Date Overrides -->
		<div class="card">
			<div class="flex items-center justify-between mb-4">
				<h3 class="text-lg font-semibold text-[var(--text-primary)]">{$t('availability.overrides')}</h3>
				<button
					on:click={() => {
						showOverrideForm = !showOverrideForm;
						if (showOverrideForm) {
							const d = new Date();
							d.setDate(d.getDate() + 1);
							overrideDate = d.toISOString().split('T')[0];
						}
					}}
					class="flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700"
				>
					{#if showOverrideForm}
						<X size={16} />
						{$t('common.cancel')}
					{:else}
						<Plus size={16} />
						{$t('availability.addOverride')}
					{/if}
				</button>
			</div>

			{#if showOverrideForm}
				<div class="mb-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] p-4 space-y-3">
					<div class="grid grid-cols-2 gap-3">
						<div>
							<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('professional.date')}</label>
							<input type="date" bind:value={overrideDate} class="input w-full date-input" />
						</div>
						<div>
							<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">Type</label>
							<select bind:value={overrideType} class="input w-full">
								<option value="block">{$t('availability.blockDay')}</option>
								<option value="extra">{$t('availability.extraHours')}</option>
							</select>
						</div>
					</div>

					{#if overrideType === 'extra'}
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('availability.startTime')}</label>
								<input type="time" bind:value={overrideStartTime} class="input w-full date-input" />
							</div>
							<div>
								<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">{$t('availability.endTime')}</label>
								<input type="time" bind:value={overrideEndTime} class="input w-full date-input" />
							</div>
						</div>
					{/if}

					<button
						on:click={addOverride}
						class="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
						disabled={addingOverride || !overrideDate}
					>
						{addingOverride ? $t('common.loading') : $t('availability.addOverride')}
					</button>
				</div>
			{/if}

			{#if overrides.length > 0}
				<div class="space-y-2">
					{#each overrides as override}
						<div class="flex items-center justify-between rounded-lg border border-[var(--border-color)] p-3">
							<div class="flex items-center gap-3">
								{#if override.override_type === 'block'}
									<div class="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/40">
										<ShieldOff size={14} class="text-red-600 dark:text-red-400" />
									</div>
								{:else}
									<div class="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/40">
										<Clock size={14} class="text-green-600 dark:text-green-400" />
									</div>
								{/if}
								<div>
									<p class="text-sm font-medium text-[var(--text-primary)]">
										{new Date(override.override_date + 'T00:00:00').toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
									</p>
									<p class="text-xs text-[var(--text-secondary)]">
										{#if override.override_type === 'block'}
											{$t('availability.blockDay')}
										{:else}
											{$t('availability.extraHours')}: {override.start_time} - {override.end_time}
										{/if}
									</p>
								</div>
							</div>
							<button
								on:click={() => removeOverride(override.id)}
								class="p-1.5 rounded text-[var(--text-secondary)] hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600"
							>
								<Trash2 size={14} />
							</button>
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-sm text-[var(--text-secondary)] text-center py-4">{$t('availability.noOverrides')}</p>
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
