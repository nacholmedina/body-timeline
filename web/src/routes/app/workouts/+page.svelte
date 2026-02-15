<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime, localNow } from '$lib/utils';
	import { Plus, Dumbbell, Trash2, Clock } from 'lucide-svelte';
	import DateTimePicker from '$components/DateTimePicker.svelte';

	let workouts: any[] = [];
	let loading = true;
	let error = '';
	let showForm = false;

	let startedAt = localNow();
	let endedAt = '';
	let notes = '';
	let formLoading = false;
	let formError = '';

	async function loadWorkouts() {
		loading = true;
		try {
			const res = await api.get('/workouts');
			workouts = res.data;
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	async function createWorkout() {
		formError = '';
		formLoading = true;
		try {
			await api.post('/workouts', {
				started_at: new Date(startedAt).toISOString(),
				ended_at: endedAt ? new Date(endedAt).toISOString() : undefined,
				notes: notes || undefined,
				items: []
			});
			resetForm();
			await loadWorkouts();
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			formLoading = false;
		}
	}

	async function deleteWorkout(id: string) {
		await api.delete(`/workouts/${id}`);
		workouts = workouts.filter((w) => w.id !== id);
	}

	function resetForm() {
		showForm = false;
		startedAt = localNow();
		endedAt = '';
		notes = '';
		formLoading = false;
	}

	function getDuration(workout: any): string {
		if (!workout.started_at || !workout.ended_at) return '';
		const ms = new Date(workout.ended_at).getTime() - new Date(workout.started_at).getTime();
		const mins = Math.round(ms / 60000);
		if (mins < 60) return `${mins}m`;
		return `${Math.floor(mins / 60)}h ${mins % 60}m`;
	}

	onMount(loadWorkouts);
</script>

<svelte:head>
	<title>{$t('workouts.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between gap-3">
		<h1 class="text-2xl font-bold text-[var(--text-primary)] min-w-0 truncate">{$t('workouts.title')}</h1>
		<button on:click={() => (showForm = !showForm)} class="btn-primary flex items-center gap-2 shrink-0">
			<Plus size={18} />
			<span class="hidden sm:inline">{$t('workouts.addWorkout')}</span>
		</button>
	</div>

	{#if showForm}
		<form on:submit|preventDefault={createWorkout} class="card space-y-4">
			{#if formError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{formError}</div>
			{/if}
			<div>
				<label class="label">{$t('workouts.startTime')}</label>
				<DateTimePicker bind:value={startedAt} id="startedAt" required />
			</div>
			<div>
				<label class="label">{$t('workouts.endTime')}</label>
				<DateTimePicker bind:value={endedAt} id="endedAt" />
			</div>
			<div>
				<label for="notes" class="label">{$t('meals.notes')}</label>
				<textarea id="notes" bind:value={notes} class="input" rows="2"></textarea>
			</div>
			<div class="flex gap-3">
				<button type="submit" class="btn-primary" disabled={formLoading}>
					{formLoading ? $t('common.loading') : $t('common.save')}
				</button>
				<button type="button" on:click={resetForm} class="btn-secondary">{$t('common.cancel')}</button>
			</div>
		</form>
	{/if}

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if workouts.length === 0}
		<div class="py-12 text-center">
			<Dumbbell size={48} class="mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
			<p class="text-[var(--text-secondary)]">{$t('workouts.noWorkouts')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each workouts as workout (workout.id)}
				<div class="card">
					<div class="flex items-start justify-between">
						<div>
							<div class="flex items-center gap-2">
								<Dumbbell size={18} class="text-brand-500" />
								<span class="text-sm text-[var(--text-secondary)]">{formatDateTime(workout.started_at, $locale)}</span>
								{#if getDuration(workout)}
									<span class="flex items-center gap-1 text-xs text-accent-600 dark:text-accent-400">
										<Clock size={12} />{getDuration(workout)}
									</span>
								{/if}
							</div>
							{#if workout.notes}
								<p class="mt-2 text-sm text-[var(--text-secondary)]">{workout.notes}</p>
							{/if}
							{#if workout.items?.length > 0}
								<div class="mt-3 space-y-1">
									{#each workout.items as item}
										<div class="flex items-center gap-2 text-sm">
											<span class="font-medium text-[var(--text-primary)]">{item.exercise_name || $t('workouts.exercise')}</span>
											{#if item.sets && item.reps}
												<span class="text-[var(--text-secondary)]">{item.sets}x{item.reps}</span>
											{/if}
											{#if item.weight_kg}
												<span class="text-[var(--text-secondary)]">{item.weight_kg}kg</span>
											{/if}
											{#if item.duration_seconds}
												<span class="text-[var(--text-secondary)]">{Math.round(item.duration_seconds / 60)}min</span>
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>
						<button
							on:click={() => deleteWorkout(workout.id)}
							class="rounded-lg p-2 text-red-400 hover:bg-red-50 dark:hover:bg-red-950"
						>
							<Trash2 size={16} />
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
