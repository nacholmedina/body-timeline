<script lang="ts">
	import { t } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { Plus, Edit2, Trash2, Play, X, GripVertical, Check } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';
	import ConfirmModal from '$components/ConfirmModal.svelte';
	import { unitStore } from '$stores/units';
	import { toastStore } from '$stores/toast';

	export let exerciseDefinitions: any[] = [];

	const dispatch = createEventDispatcher();

	let routines: any[] = [];
	let loading = true;
	let error = '';

	// Form state
	let showForm = false;
	let editingRoutine: any = null;
	let routineName = '';
	let routineDescription = '';
	let selectedExercises: any[] = [];
	let formLoading = false;
	let formError = '';

	// Delete confirmation
	let showDeleteConfirm = false;
	let routineToDelete: string | null = null;
	let deleting = false;

	// Exercise selection
	let showExerciseSelect = false;
	let exerciseSearchQuery = '';
	let selectedCategory = 'all';
	let filteredExercises: any[] = [];

	// Get unique categories from exercise definitions
	$: categories = ['all', ...new Set(exerciseDefinitions.map(e => e.category))];

	async function loadRoutines() {
		loading = true;
		error = '';
		try {
			const res = await api.get('/exercise-routines');
			routines = res.data || [];
		} catch (err) {
			error = err instanceof ApiError ? err.message : $t('common.failedToLoad');
		} finally {
			loading = false;
		}
	}

	function openCreateForm() {
		editingRoutine = null;
		routineName = '';
		routineDescription = '';
		selectedExercises = [];
		formError = '';
		showForm = true;
	}

	function openEditForm(routine: any) {
		editingRoutine = routine;
		routineName = routine.name;
		routineDescription = routine.description || '';
		selectedExercises = routine.items.map((item: any, index: number) => ({
			...item,
			tempId: `${item.exercise_definition_id}-${index}`
		}));
		formError = '';
		showForm = true;
	}

	function addExerciseToRoutine(exercise: any) {
		const newItem = {
			tempId: `${exercise.id}-${Date.now()}`,
			exercise_definition_id: exercise.id,
			exercise_name: exercise.name,
			exercise_category: exercise.category,
			allowed_measurements: exercise.allowed_measurements,
			sort_order: selectedExercises.length,
			default_measurements: {},
			notes: ''
		};
		selectedExercises = [...selectedExercises, newItem];
		exerciseSearchQuery = '';
		showExerciseSelect = false;
	}

	function removeExercise(tempId: string) {
		selectedExercises = selectedExercises.filter(e => e.tempId !== tempId);
		// Update sort order
		selectedExercises = selectedExercises.map((e, index) => ({ ...e, sort_order: index }));
	}

	function moveExercise(index: number, direction: number) {
		const newIndex = index + direction;
		if (newIndex < 0 || newIndex >= selectedExercises.length) return;

		const items = [...selectedExercises];
		[items[index], items[newIndex]] = [items[newIndex], items[index]];
		selectedExercises = items.map((e, i) => ({ ...e, sort_order: i }));
	}

	async function saveRoutine() {
		formError = '';
		formLoading = true;

		try {
			if (!routineName.trim()) {
				formError = $t('routines.nameRequired');
				formLoading = false;
				return;
			}

			if (selectedExercises.length === 0) {
				formError = $t('routines.atLeastOneExercise');
				formLoading = false;
				return;
			}

			const payload = {
				name: routineName.trim(),
				description: routineDescription.trim() || undefined,
				items: selectedExercises.map(e => ({
					exercise_definition_id: e.exercise_definition_id,
					sort_order: e.sort_order,
					default_measurements: e.default_measurements,
					notes: e.notes || undefined
				}))
			};

			if (editingRoutine) {
				await api.patch(`/exercise-routines/${editingRoutine.id}`, payload);
			} else {
				await api.post('/exercise-routines', payload);
			}

			await loadRoutines();
			showForm = false;
			resetForm();
		} catch (err) {
			formError = err instanceof ApiError ? err.message : $t('common.failed');
		} finally {
			formLoading = false;
		}
	}

	function resetForm() {
		showForm = false;
		editingRoutine = null;
		routineName = '';
		routineDescription = '';
		selectedExercises = [];
		formError = '';
	}

	function deleteRoutine(id: string) {
		routineToDelete = id;
		showDeleteConfirm = true;
	}

	async function confirmDelete() {
		if (!routineToDelete) return;
		deleting = true;
		try {
			await api.delete(`/exercise-routines/${routineToDelete}`);
			routines = routines.filter(r => r.id !== routineToDelete);
			showDeleteConfirm = false;
			routineToDelete = null;
			toastStore.show($t('routines.deleted'), 'success');
		} catch (err) {
			toastStore.show(err instanceof ApiError ? err.message : $t('common.failed'), 'error');
		} finally {
			deleting = false;
		}
	}

	async function logRoutine(routine: any) {
		try {
			await api.post(`/exercise-routines/${routine.id}/log`, {
				performed_at: new Date().toISOString(),
				notes: `${$t('routines.logged')}: ${routine.name}`
			});
			dispatch('routineLogged');
			toastStore.show($t('routines.loggedSuccess'), 'success');
		} catch (err) {
			toastStore.show(err instanceof ApiError ? err.message : $t('common.failed'), 'error');
		}
	}

	function translateExerciseName(name: string): string {
		const key = `exercises.exerciseNames.${name}`;
		const translated = $t(key);
		return translated === key ? name : translated;
	}

	function getMeasurementLabel(type: string): string {
		const isImperial = $unitStore === 'imperial';
		if (type === 'weight') return isImperial ? `${$t('exercises.weight')} (lbs)` : $t('exercises.weightLabel');
		if (type === 'distance') return isImperial ? `${$t('exercises.distance')} (mi)` : $t('exercises.distanceLabel');
		return $t(`exercises.${type}Label`);
	}

	$: {
		const query = exerciseSearchQuery.toLowerCase();
		filteredExercises = exerciseDefinitions
			.filter(e => {
				const matchesSearch = !query || e.name.toLowerCase().includes(query);
				const matchesCategory = selectedCategory === 'all' || e.category === selectedCategory;
				return matchesSearch && matchesCategory;
			})
			.slice(0, 20); // Show more exercises
	}

	// Load routines on mount
	loadRoutines();
</script>

<div class="space-y-4">
	<!-- Header -->
	<div class="flex items-center justify-between gap-3">
		<h2 class="text-xl font-semibold text-[var(--text-primary)]">{$t('routines.title')}</h2>
		<button on:click={openCreateForm} class="btn-primary flex items-center gap-2">
			<Plus size={18} />
			<span class="hidden sm:inline">{$t('routines.create')}</span>
		</button>
	</div>

	<!-- Loading / Error -->
	{#if loading}
		<div class="flex items-center justify-center py-8">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if error}
		<div class="rounded-lg bg-red-50 dark:bg-red-950 p-4 text-red-600 dark:text-red-400">
			{error}
		</div>
	{:else if routines.length === 0}
		<div class="card text-center py-8">
			<p class="text-[var(--text-secondary)]">{$t('routines.noRoutines')}</p>
			<button on:click={openCreateForm} class="btn-primary mt-4">
				{$t('routines.createFirst')}
			</button>
		</div>
	{:else}
		<!-- Routine List -->
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each routines as routine (routine.id)}
				<div class="card hover:shadow-lg transition-shadow">
					<div class="flex items-start justify-between gap-2 mb-3">
						<div class="flex-1 min-w-0">
							<h3 class="font-semibold text-[var(--text-primary)] truncate">{routine.name}</h3>
							{#if routine.description}
								<p class="text-sm text-[var(--text-secondary)] line-clamp-2 mt-1">{routine.description}</p>
							{/if}
						</div>
						<div class="flex gap-1">
							<button
								on:click={() => openEditForm(routine)}
								class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-[var(--text-secondary)]"
								title={$t('common.edit')}
							>
								<Edit2 size={16} />
							</button>
							<button
								on:click={() => deleteRoutine(routine.id)}
								class="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/50 text-red-600"
								title={$t('common.delete')}
							>
								<Trash2 size={16} />
							</button>
						</div>
					</div>

					<!-- Exercise count -->
					<div class="text-sm text-[var(--text-secondary)] mb-3">
						{routine.exercise_count} {routine.exercise_count === 1 ? $t('routines.exercise') : $t('routines.exercises')}
					</div>

					<!-- Exercises preview -->
					<div class="space-y-1 mb-3 text-sm">
						{#each routine.items.slice(0, 3) as item, index}
							<div class="flex items-center gap-2 text-[var(--text-secondary)]">
								<span class="text-xs text-[var(--text-tertiary)]">{index + 1}.</span>
								<span class="truncate">{translateExerciseName(item.exercise_name)}</span>
							</div>
						{/each}
						{#if routine.items.length > 3}
							<div class="text-xs text-[var(--text-tertiary)]">
								+{routine.items.length - 3} {$t('common.more')}
							</div>
						{/if}
					</div>

					<!-- Log button -->
					<button
						on:click={() => logRoutine(routine)}
						class="btn-primary w-full flex items-center justify-center gap-2"
					>
						<Play size={16} />
						{$t('routines.logNow')}
					</button>
				</div>
			{/each}
		</div>
	{/if}

	<!-- Create/Edit Form -->
	{#if showForm}
		<div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
			<div class="card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-semibold text-[var(--text-primary)]">
						{editingRoutine ? $t('routines.edit') : $t('routines.create')}
					</h3>
					<button on:click={resetForm} class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
						<X size={20} />
					</button>
				</div>

				{#if formError}
					<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400 mb-4">
						{formError}
					</div>
				{/if}

				<form on:submit|preventDefault={saveRoutine} class="space-y-4">
					<!-- Name -->
					<div>
						<label for="routineName" class="label">{$t('routines.name')}</label>
						<input
							id="routineName"
							type="text"
							bind:value={routineName}
							class="input"
							placeholder={$t('routines.namePlaceholder')}
							required
						/>
					</div>

					<!-- Description -->
					<div>
						<label for="routineDesc" class="label">{$t('routines.description')} ({$t('common.optional')})</label>
						<textarea
							id="routineDesc"
							bind:value={routineDescription}
							class="input"
							rows="2"
							placeholder={$t('routines.descriptionPlaceholder')}
						></textarea>
					</div>

					<!-- Exercises -->
					<div>
						<div class="flex items-center justify-between mb-2">
							<label class="label">{$t('routines.exercises')}</label>
							<button
								type="button"
								on:click={() => (showExerciseSelect = !showExerciseSelect)}
								class="btn-secondary text-sm flex items-center gap-1"
							>
								<Plus size={16} />
								{$t('routines.addExercise')}
							</button>
						</div>

						{#if showExerciseSelect}
							<div class="mb-3 p-3 border border-[var(--border-color)] rounded-lg">
								<!-- Category filter and search -->
								<div class="flex gap-2 mb-2">
									<select bind:value={selectedCategory} class="input flex-1">
										{#each categories as category}
											<option value={category}>
												{category === 'all' ? $t('exercises.allCategories') : category}
											</option>
										{/each}
									</select>
									<input
										type="text"
										bind:value={exerciseSearchQuery}
										class="input flex-1"
										placeholder={$t('exercises.search')}
										autocomplete="off"
									/>
								</div>
								<!-- Exercise list -->
								<div class="max-h-64 overflow-y-auto space-y-1">
									{#if filteredExercises.length === 0}
										<div class="text-center py-4 text-[var(--text-secondary)] text-sm">
											{$t('exercises.noResults')}
										</div>
									{:else}
										{#each filteredExercises as exercise}
											<button
												type="button"
												on:click={() => addExerciseToRoutine(exercise)}
												class="w-full text-left px-3 py-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-sm"
											>
												<div class="font-medium">{translateExerciseName(exercise.name)}</div>
												<div class="text-xs text-[var(--text-secondary)]">
													{exercise.category}
												</div>
											</button>
										{/each}
									{/if}
								</div>
							</div>
						{/if}

						{#if selectedExercises.length === 0}
							<div class="text-center py-4 text-[var(--text-secondary)] text-sm border border-dashed border-[var(--border-color)] rounded-lg">
								{$t('routines.noExercisesAdded')}
							</div>
						{:else}
							<div class="space-y-3">
								{#each selectedExercises as exercise, index (exercise.tempId)}
									<div class="border border-[var(--border-color)] rounded-lg p-3">
										<div class="flex items-start gap-2 mb-2">
											<div class="flex flex-col gap-1 pt-1">
												<button
													type="button"
													on:click={() => moveExercise(index, -1)}
													disabled={index === 0}
													class="p-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30"
												>
													<GripVertical size={14} />
												</button>
												<button
													type="button"
													on:click={() => moveExercise(index, 1)}
													disabled={index === selectedExercises.length - 1}
													class="p-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-30"
												>
													<GripVertical size={14} />
												</button>
											</div>
											<div class="flex-1 min-w-0">
												<div class="font-medium text-sm text-[var(--text-primary)]">{translateExerciseName(exercise.exercise_name)}</div>
												<div class="text-xs text-[var(--text-secondary)]">{exercise.exercise_category}</div>
											</div>
											<button
												type="button"
												on:click={() => removeExercise(exercise.tempId)}
												class="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/50 text-red-600"
											>
												<Trash2 size={16} />
											</button>
										</div>

										<!-- Default measurements -->
										{#if exercise.allowed_measurements && exercise.allowed_measurements.length > 0}
											<div class="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2 pt-2 border-t border-[var(--border-color)]">
												{#each exercise.allowed_measurements as measurement}
													<div>
														<label class="text-xs text-[var(--text-secondary)] block mb-1">
															{getMeasurementLabel(measurement)}
														</label>
														<input
															type="number"
															bind:value={exercise.default_measurements[measurement]}
															class="input text-sm py-1"
															placeholder={$t('common.optional')}
															step={measurement === 'weight' ? '0.1' : '1'}
															min="0"
														/>
													</div>
												{/each}
											</div>
										{/if}

										<!-- Notes -->
										<div class="mt-2">
											<label class="text-xs text-[var(--text-secondary)] block mb-1">
												{$t('exercises.notes')} ({$t('common.optional')})
											</label>
											<input
												type="text"
												bind:value={exercise.notes}
												class="input text-sm py-1"
												placeholder={$t('exercises.notesPlaceholder')}
											/>
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>

					<!-- Actions -->
					<div class="flex gap-3 pt-2">
						<button type="submit" class="btn-primary flex-1" disabled={formLoading}>
							{formLoading ? $t('common.saving') : $t('common.save')}
						</button>
						<button type="button" on:click={resetForm} class="btn-secondary">
							{$t('common.cancel')}
						</button>
					</div>
				</form>
			</div>
		</div>
	{/if}

	<!-- Delete Confirmation -->
	<ConfirmModal
		bind:show={showDeleteConfirm}
		title={$t('routines.deleteConfirm')}
		message={$t('routines.deleteMessage')}
		confirmText={$t('common.delete')}
		cancelText={$t('common.cancel')}
		danger={true}
		loading={deleting}
		onConfirm={confirmDelete}
	/>
</div>
