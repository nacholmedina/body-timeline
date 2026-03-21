<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { formatDate } from '$lib/utils';
	import {
		Plus, Search, Check, X, Edit2, Trash2
	} from 'lucide-svelte';

	interface ExerciseItem {
		id: string;
		name: string;
		description: string | null;
		exercise_type: string;
		muscle_group: string | null;
		is_active: boolean;
	}

	let exercises: ExerciseItem[] = [];
	let loading = true;
	let search = '';
	let page = 1;
	let total = 0;
	const limit = 20;

	// Create modal
	let showCreate = false;
	let createForm = { name: '', description: '', exercise_type: 'sets_reps', muscle_group: '' };
	let createError = '';
	let creating = false;

	// Edit inline
	let editId: string | null = null;
	let editForm = { name: '', description: '', exercise_type: '', muscle_group: '' };

	async function loadExercises() {
		loading = true;
		try {
			const params: Record<string, string> = { page: String(page), limit: String(limit) };
			if (search) params.search = search;
			const res = await api.get('/exercises', params);
			exercises = res.data;
			total = res.total;
		} catch (err) {
			console.error('Failed to load exercises', err);
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadExercises();
	});

	let searchTimeout: ReturnType<typeof setTimeout>;
	function handleSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			page = 1;
			loadExercises();
		}, 300);
	}

	async function handleCreate() {
		createError = '';
		creating = true;
		try {
			await api.post('/exercises', {
				name: createForm.name,
				description: createForm.description || undefined,
				exercise_type: createForm.exercise_type,
				muscle_group: createForm.muscle_group || undefined
			});
			showCreate = false;
			createForm = { name: '', description: '', exercise_type: 'sets_reps', muscle_group: '' };
			loadExercises();
		} catch (err) {
			createError = err instanceof ApiError ? err.message : 'Failed to create exercise';
		} finally {
			creating = false;
		}
	}

	function startEdit(ex: ExerciseItem) {
		editId = ex.id;
		editForm = {
			name: ex.name,
			description: ex.description || '',
			exercise_type: ex.exercise_type,
			muscle_group: ex.muscle_group || ''
		};
	}

	async function saveEdit(ex: ExerciseItem) {
		try {
			const res = await api.patch(`/exercises/${ex.id}`, {
				name: editForm.name,
				description: editForm.description || null,
				exercise_type: editForm.exercise_type,
				muscle_group: editForm.muscle_group || null
			});
			Object.assign(ex, res.data);
			exercises = exercises;
		} catch (err) {
			console.error('Failed to update exercise', err);
		}
		editId = null;
	}

	async function toggleExercise(ex: ExerciseItem) {
		try {
			const res = await api.patch(`/exercises/${ex.id}`, { is_active: !ex.is_active });
			ex.is_active = res.data.is_active;
			exercises = exercises;
		} catch (err) {
			console.error('Failed to toggle exercise', err);
		}
	}


	function typeLabel(t: string): string {
		if (t === 'sets_reps') return 'Sets & Reps';
		if (t === 'duration') return 'Duration';
		return 'Both';
	}

	$: totalPages = Math.ceil(total / limit);
</script>

<!-- Header -->
<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
	<div class="relative flex-1 max-w-sm">
		<Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
		<input
			type="text"
			bind:value={search}
			on:input={handleSearch}
			placeholder="{$t('admin.exerciseName')}..."
			class="input pl-9 w-full"
		/>
	</div>
	<button on:click={() => (showCreate = true)} class="btn-primary flex items-center gap-2">
		<Plus size={16} />
		{$t('admin.createExercise')}
	</button>
</div>

<!-- Exercises table -->
{#if loading}
	<div class="flex justify-center py-12">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent"></div>
	</div>
{:else if exercises.length === 0}
	<div class="card p-8 text-center text-[var(--text-secondary)]">{$t('admin.noExercises')}</div>
{:else}
	<div class="card overflow-hidden">
		<div class="overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('admin.exerciseName')}</th>
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('admin.exerciseType')}</th>
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('admin.muscleGroup')}</th>
						<th class="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each exercises as ex (ex.id)}
						{#if editId === ex.id}
							<tr class="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
								<td class="px-4 py-2">
									<input bind:value={editForm.name} class="input py-1 text-sm w-full" />
								</td>
								<td class="px-4 py-2">
									<select bind:value={editForm.exercise_type} class="input py-1 text-sm">
										<option value="sets_reps">Sets & Reps</option>
										<option value="duration">Duration</option>
										<option value="both">Both</option>
									</select>
								</td>
								<td class="px-4 py-2">
									<input bind:value={editForm.muscle_group} class="input py-1 text-sm w-full" placeholder="e.g. chest" />
								</td>
								<td class="px-4 py-2 text-right">
									<div class="flex items-center justify-end gap-1">
										<button on:click={() => saveEdit(ex)} class="text-green-600 hover:text-green-700 p-1"><Check size={16} /></button>
										<button on:click={() => (editId = null)} class="text-[var(--text-secondary)] hover:text-[var(--text-primary)] p-1"><X size={16} /></button>
									</div>
								</td>
							</tr>
						{:else}
							<tr class="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors {!ex.is_active ? 'opacity-50' : ''}">
								<td class="px-4 py-3 font-medium text-[var(--text-primary)]">{ex.name}</td>
								<td class="px-4 py-3 text-[var(--text-secondary)]">{typeLabel(ex.exercise_type)}</td>
								<td class="px-4 py-3 text-[var(--text-secondary)]">{ex.muscle_group || '—'}</td>
								<td class="px-4 py-3 text-right">
									<div class="flex items-center justify-end gap-1">
										<button on:click={() => startEdit(ex)} class="p-1.5 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]" title={$t('common.edit')}>
											<Edit2 size={14} />
										</button>
										<button
											on:click={() => toggleExercise(ex)}
											class="p-1.5 rounded-lg transition-colors {ex.is_active ? 'text-red-500 hover:bg-red-50 dark:hover:bg-red-950' : 'text-green-600 hover:bg-green-50 dark:hover:bg-green-950'}"
											title={ex.is_active ? 'Deactivate' : 'Activate'}
										>
											{#if ex.is_active}<Trash2 size={14} />{:else}<Check size={14} />{/if}
										</button>
									</div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	</div>

	<!-- Pagination -->
	{#if totalPages > 1}
		<div class="flex items-center justify-between mt-4">
			<p class="text-sm text-[var(--text-secondary)]">{total} exercises</p>
			<div class="flex gap-1">
				{#each Array.from({ length: totalPages }, (_, i) => i + 1) as p}
					<button
						on:click={() => { page = p; loadExercises(); }}
						class="px-3 py-1 rounded-lg text-sm font-medium transition-colors
						{p === page
							? 'bg-brand-600 text-white'
							: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
					>
						{p}
					</button>
				{/each}
			</div>
		</div>
	{/if}
{/if}

<!-- Create exercise modal -->
{#if showCreate}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<button class="absolute inset-0 bg-black/50" on:click={() => (showCreate = false)} aria-label="Close" />
		<div class="relative w-full max-w-md card p-6 space-y-4">
			<div class="flex items-center justify-between">
				<h3 class="text-lg font-semibold text-[var(--text-primary)]">{$t('admin.createExercise')}</h3>
				<button on:click={() => (showCreate = false)} class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
					<X size={20} />
				</button>
			</div>

			{#if createError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{createError}</div>
			{/if}

			<form on:submit|preventDefault={handleCreate} class="space-y-3">
				<div>
					<label for="e_name" class="label">{$t('admin.exerciseName')}</label>
					<input id="e_name" type="text" bind:value={createForm.name} class="input" required />
				</div>
				<div>
					<label for="e_desc" class="label">{$t('meals.description')}</label>
					<textarea id="e_desc" bind:value={createForm.description} class="input" rows="2"></textarea>
				</div>
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label for="e_type" class="label">{$t('admin.exerciseType')}</label>
						<select id="e_type" bind:value={createForm.exercise_type} class="input">
							<option value="sets_reps">{$t('admin.setsReps')}</option>
							<option value="duration">{$t('admin.duration')}</option>
							<option value="both">{$t('admin.both')}</option>
						</select>
					</div>
					<div>
						<label for="e_muscle" class="label">{$t('admin.muscleGroup')}</label>
						<input id="e_muscle" type="text" bind:value={createForm.muscle_group} class="input" placeholder="e.g. chest" />
					</div>
				</div>
				<div class="flex gap-3 pt-2">
					<button type="button" on:click={() => (showCreate = false)} class="btn-secondary flex-1">{$t('common.cancel')}</button>
					<button type="submit" class="btn-primary flex-1" disabled={creating}>
						{creating ? $t('common.loading') : $t('admin.createExercise')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
