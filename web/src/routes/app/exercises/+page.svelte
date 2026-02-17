<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api, ApiError, photoUrl } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime, localNow, kgToLbs, lbsToKg, kmToMi, miToKm } from '$lib/utils';
	import { Plus, Dumbbell, Trash2, Search, X, Camera, ImagePlus, ChevronDown } from 'lucide-svelte';
	import DateTimePicker from '$components/DateTimePicker.svelte';
	import ConfirmModal from '$components/ConfirmModal.svelte';
	import { addToSyncQueue } from '$lib/offline/db';
	import { onlineStore } from '$stores/online';
	import { unitStore } from '$stores/units';
	import RoutineManager from '$components/RoutineManager.svelte';

	let currentView: 'exercises' | 'routines' = 'exercises';
	let exerciseLogs: any[] = [];
	let exerciseDefinitions: any[] = [];
	let filteredDefinitions: any[] = [];
	let loading = true;
	let error = '';
	let showForm = false;
	let showRequestForm = false;

	// Delete confirmation
	let showDeleteConfirm = false;
	let exerciseToDelete: string | null = null;
	let deleting = false;

	// Form state
	let selectedDefinitionId = '';
	let customExerciseName = '';
	let customExerciseDescription = '';
	let performedAt = localNow();
	let measurements: Record<string, number> = {};
	let notes = '';
	let selectedPhotos: File[] = [];
	let photoPreviews: string[] = [];
	let fileInput: HTMLInputElement;
	let cameraInput: HTMLInputElement;
	let formLoading = false;
	let formError = '';
	const MAX_PHOTOS = 3;

	// Request form state
	let requestName = '';
	let requestCategory = 'general';
	let requestDescription = '';
	let requestMeasurements: string[] = [];
	let requestLoading = false;
	let requestError = '';

	// Filter state
	let selectedCategory = 'all';
	let searchQuery = '';
	let showDropdown = false;
	let showSelectDropdown = false;
	let dropdownWrapper: HTMLDivElement;
	let selectWrapper: HTMLDivElement;
	let timeFilter: 'all' | 'day' | 'week' | 'month' | 'year' = 'all';

	const categories = ['all', 'cardio', 'strength', 'sports', 'flexibility', 'general'];
	const measurementTypes = ['duration', 'reps', 'jumps', 'distance', 'sets', 'weight'];

	function getTimeFilterParams(): Record<string, string> {
		const now = new Date();
		const params: Record<string, string> = {};
		if (timeFilter === 'day') {
			params.from = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
		} else if (timeFilter === 'week') {
			params.from = new Date(now.getTime() - 7 * 86400000).toISOString();
		} else if (timeFilter === 'month') {
			params.from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
		} else if (timeFilter === 'year') {
			params.from = new Date(now.getFullYear(), 0, 1).toISOString();
		}
		return params;
	}

	async function loadExerciseLogs() {
		loading = true;
		try {
			const res = await api.get('/exercise-logs', getTimeFilterParams());
			exerciseLogs = res.data || [];
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	async function loadExerciseDefinitions() {
		try {
			const res = await api.get('/exercise-definitions?limit=500');
			exerciseDefinitions = res.data || [];
			filterDefinitions();
		} catch (err) {
			console.error('Failed to load exercise definitions:', err);
		}
	}

	function filterDefinitions() {
		let filtered = exerciseDefinitions;

		// Filter by category
		if (selectedCategory !== 'all') {
			filtered = filtered.filter((def) => def.category === selectedCategory);
		}

		// Filter by search query (search translated names)
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			filtered = filtered.filter((def) => translateExerciseName(def.name).toLowerCase().includes(query));
		}

		// Sort by usage count
		filtered.sort((a, b) => b.usage_count - a.usage_count);

		filteredDefinitions = filtered;
	}

	function selectExercise(def: any) {
		selectedDefinitionId = def.id;
		searchQuery = translateExerciseName(def.name);
		showDropdown = false;
		showSelectDropdown = false;
		measurements = {};
	}

	function selectCustomExercise() {
		selectedDefinitionId = 'custom';
		searchQuery = $t('exercises.customExercise');
		showDropdown = false;
		showSelectDropdown = false;
		measurements = {};
	}

	function handleClickOutside(e: MouseEvent) {
		if (dropdownWrapper && !dropdownWrapper.contains(e.target as Node)) {
			showDropdown = false;
		}
		if (selectWrapper && !selectWrapper.contains(e.target as Node)) {
			showSelectDropdown = false;
		}
	}

	function handlePhotoSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		if (!input.files?.length) return;
		const remaining = MAX_PHOTOS - selectedPhotos.length;
		const files = Array.from(input.files).slice(0, remaining);
		for (const file of files) {
			selectedPhotos = [...selectedPhotos, file];
			photoPreviews = [...photoPreviews, URL.createObjectURL(file)];
		}
		input.value = '';
	}

	function removePhoto(index: number) {
		URL.revokeObjectURL(photoPreviews[index]);
		selectedPhotos = selectedPhotos.filter((_, i) => i !== index);
		photoPreviews = photoPreviews.filter((_, i) => i !== index);
	}

	async function createExerciseLog() {
		formError = '';
		formLoading = true;

		try {
			const payload: any = {
				performed_at: new Date(performedAt).toISOString(),
				notes: notes || undefined
			};

			// If custom exercise (Other)
			if (selectedDefinitionId === 'custom') {
				payload.custom_exercise_name = customExerciseName;
				payload.custom_exercise_description = customExerciseDescription;
			} else {
				payload.exercise_definition_id = selectedDefinitionId;

				// Add measurements
				const selectedDef = exerciseDefinitions.find((d) => d.id === selectedDefinitionId);
				if (selectedDef && selectedDef.allowed_measurements) {
					const allowed = selectedDef.allowed_measurements; // Already an array!
					const measurementData: Record<string, number> = {};

					for (const measurementType of allowed) {
						if (measurements[measurementType] !== undefined && measurements[measurementType] !== null) {
							let val = Number(measurements[measurementType]);
							if ($unitStore === 'imperial') {
								if (measurementType === 'weight') val = lbsToKg(val);
								if (measurementType === 'distance') val = miToKm(val);
							}
							measurementData[measurementType] = parseFloat(val.toFixed(2));
						}
					}

					if (Object.keys(measurementData).length > 0) {
						payload.measurements = measurementData;
					}
				}
			}

			if ($onlineStore) {
				const res = await api.post('/exercise-logs', payload);
				const newLog = res.data;

				// Upload photos if any
				for (let i = 0; i < selectedPhotos.length; i++) {
					try {
						await api.upload(`/exercise-logs/${newLog.id}/photos`, selectedPhotos[i], { sort_order: String(i) });
					} catch (err) {
						console.error('Photo upload failed:', err);
					}
				}
			} else {
				await addToSyncQueue({ type: 'exercise', action: 'create', payload });
			}

			resetForm();
			await loadExerciseLogs();
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			formLoading = false;
		}
	}

	function deleteExerciseLog(id: string) {
		exerciseToDelete = id;
		showDeleteConfirm = true;
	}

	async function confirmDelete() {
		if (!exerciseToDelete) return;
		deleting = true;
		try {
			if ($onlineStore) {
				await api.delete(`/exercise-logs/${exerciseToDelete}`);
			} else {
				await addToSyncQueue({ type: 'exercise', action: 'delete', payload: { id: exerciseToDelete } });
			}
			exerciseLogs = exerciseLogs.filter((e) => e.id !== exerciseToDelete);
			showDeleteConfirm = false;
			exerciseToDelete = null;
		} catch (err) {
			error = 'Failed to delete exercise';
		} finally {
			deleting = false;
		}
	}

	async function submitExerciseRequest() {
		requestError = '';
		requestLoading = true;

		try {
			const payload = {
				name: requestName,
				category: requestCategory,
				description: requestDescription || undefined,
				suggested_measurements: requestMeasurements.length > 0
					? JSON.stringify(requestMeasurements)
					: undefined
			};

			await api.post('/exercise-requests', payload);

			alert($t('exercises.requestSuccess'));
			resetRequestForm();
		} catch (err) {
			requestError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			requestLoading = false;
		}
	}

	function resetForm() {
		showForm = false;
		selectedDefinitionId = '';
		customExerciseName = '';
		customExerciseDescription = '';
		performedAt = localNow();
		measurements = {};
		notes = '';
		searchQuery = '';
		showDropdown = false;
		photoPreviews.forEach((url) => URL.revokeObjectURL(url));
		selectedPhotos = [];
		photoPreviews = [];
		formLoading = false;
		formError = '';
	}

	function resetRequestForm() {
		showRequestForm = false;
		requestName = '';
		requestCategory = 'general';
		requestDescription = '';
		requestMeasurements = [];
		requestLoading = false;
		requestError = '';
	}

	function getAllowedMeasurements(definitionId: string): string[] {
		if (!definitionId || definitionId === 'custom') return [];
		const def = exerciseDefinitions.find((d) => d.id === definitionId);
		if (!def || !def.allowed_measurements) return [];
		// API already returns this as an array, no need to parse
		return def.allowed_measurements;
	}

	function getMeasurementLabel(type: string): string {
		const isImperial = $unitStore === 'imperial';
		if (type === 'weight') return isImperial ? `${$t('exercises.weight')} (lbs)` : $t('exercises.weightLabel');
		if (type === 'distance') return isImperial ? `${$t('exercises.distance')} (mi)` : $t('exercises.distanceLabel');
		return $t(`exercises.${type}Label`);
	}

	function getMeasurementStep(type: string): number {
		if (['reps', 'jumps', 'sets'].includes(type)) return 1;
		if (type === 'weight') return 0.5;
		if (type === 'distance') return 0.1;
		return 0.5;
	}

	function stepMeasurement(type: string, direction: 1 | -1) {
		const step = getMeasurementStep(type);
		const current = Number(measurements[type]) || 0;
		const next = current + step * direction;
		measurements[type] = parseFloat(Math.max(0, next).toFixed(2));
	}

	function getMeasurementDisplay(exercise: any): string {
		if (!exercise.measurements || typeof exercise.measurements !== 'object') return '';
		const m = exercise.measurements;
		const parts: string[] = [];
		const isImperial = $unitStore === 'imperial';

		if (m.duration) parts.push(`${m.duration} ${$t('exercises.minutes')}`);
		if (m.reps) parts.push(`${m.reps} ${$t('exercises.reps').toLowerCase()}`);
		if (m.jumps) parts.push(`${m.jumps} ${$t('exercises.jumps').toLowerCase()}`);
		if (m.distance) parts.push(`${isImperial ? kmToMi(m.distance).toFixed(1) : m.distance} ${isImperial ? $t('exercises.miles') : $t('exercises.kilometers')}`);
		if (m.sets) parts.push(`${m.sets} ${$t('exercises.sets').toLowerCase()}`);
		if (m.weight) parts.push(`${isImperial ? kgToLbs(m.weight).toFixed(1) : m.weight} ${isImperial ? $t('exercises.pounds') : $t('exercises.kilograms')}`);

		return parts.join(' · ');
	}

	function toggleMeasurementRequest(type: string) {
		if (requestMeasurements.includes(type)) {
			requestMeasurements = requestMeasurements.filter((m) => m !== type);
		} else {
			requestMeasurements = [...requestMeasurements, type];
		}
	}

	function translateExerciseName(name: string): string {
		// Try to get translation from exerciseNames, fallback to original name
		const key = `exercises.exerciseNames.${name}`;
		const translated = $t(key);
		return translated === key ? name : translated;
	}

	$: if (selectedCategory || searchQuery !== undefined || $locale) {
		filterDefinitions();
	}

	$: allowedMeasurements = getAllowedMeasurements(selectedDefinitionId);

	let mounted = false;
	$: if (mounted && timeFilter) {
		loadExerciseLogs();
	}

	onMount(() => {
		loadExerciseLogs();
		loadExerciseDefinitions();
		mounted = true;
	});
</script>

<svelte:head>
	<title>{$t('exercises.title')} - {BRANDING.appName}</title>
</svelte:head>

<svelte:window on:click={handleClickOutside} />

<div class="space-y-6">
	<div class="flex items-center justify-between gap-3">
		<h1 class="text-2xl font-bold text-[var(--text-primary)] min-w-0 truncate">
			{$t('exercises.title')}
		</h1>
		<div class="flex gap-2 shrink-0">
			{#if currentView === 'exercises'}
				<button on:click={() => (showRequestForm = !showRequestForm)} class="btn-secondary flex items-center gap-2">
					<Plus size={18} />
					<span class="hidden sm:inline">{$t('exercises.requestNew')}</span>
				</button>
				<button on:click={() => (showForm = !showForm)} class="btn-primary flex items-center gap-2">
					<Plus size={18} />
					<span class="hidden sm:inline">{$t('exercises.addExercise')}</span>
				</button>
			{/if}
		</div>
	</div>

	<!-- View Tabs -->
	<div class="flex gap-2 border-b border-[var(--border-color)]">
		<button
			on:click={() => (currentView = 'exercises')}
			class="px-4 py-2 font-medium transition-colors border-b-2 {currentView === 'exercises'
				? 'border-brand-600 text-brand-600'
				: 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}"
		>
			{$t('exercises.title')}
		</button>
		<button
			on:click={() => (currentView = 'routines')}
			class="px-4 py-2 font-medium transition-colors border-b-2 {currentView === 'routines'
				? 'border-brand-600 text-brand-600'
				: 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}"
		>
			{$t('routines.title')}
		</button>
	</div>

	{#if currentView === 'exercises'}
	<!-- EXERCISES VIEW -->
	{#if showRequestForm}
		<form on:submit|preventDefault={submitExerciseRequest} class="card space-y-4">
			<h2 class="text-lg font-semibold text-[var(--text-primary)]">{$t('exercises.requestExercise')}</h2>
			{#if requestError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">
					{requestError}
				</div>
			{/if}
			<div>
				<label for="requestName" class="label">{$t('exercises.exerciseName')}</label>
				<input id="requestName" type="text" bind:value={requestName} class="input" required />
			</div>
			<div>
				<label for="requestCategory" class="label">{$t('exercises.category')}</label>
				<select id="requestCategory" bind:value={requestCategory} class="input">
					<option value="cardio">{$t('exercises.cardio')}</option>
					<option value="strength">{$t('exercises.strength')}</option>
					<option value="sports">{$t('exercises.sports')}</option>
					<option value="flexibility">{$t('exercises.flexibility')}</option>
					<option value="general">{$t('exercises.general')}</option>
				</select>
			</div>
			<div>
				<label for="requestDescription" class="label">{$t('exercises.requestDescription')}</label>
				<textarea id="requestDescription" bind:value={requestDescription} class="input" rows="2"></textarea>
			</div>
			<div>
				<label class="label">{$t('exercises.suggestedMeasurements')} ({$t('exercises.optional')})</label>
				<div class="flex flex-wrap gap-2">
					{#each measurementTypes as type}
						<button
							type="button"
							on:click={() => toggleMeasurementRequest(type)}
							class="px-3 py-1.5 text-sm rounded-lg border transition-colors {requestMeasurements.includes(type)
								? 'bg-brand-500 text-white border-brand-500'
								: 'bg-[var(--bg-card)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-brand-500'}"
						>
							{$t(`exercises.${type}`)}
						</button>
					{/each}
				</div>
			</div>
			<div class="flex gap-3">
				<button type="submit" class="btn-primary" disabled={requestLoading || !requestName.trim()}>
					{requestLoading ? $t('common.loading') : $t('common.save')}
				</button>
				<button type="button" on:click={resetRequestForm} class="btn-secondary">{$t('common.cancel')}</button>
			</div>
		</form>
	{/if}

	{#if showForm}
		<form on:submit|preventDefault={createExerciseLog} class="card space-y-4">
			{#if formError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">
					{formError}
				</div>
			{/if}

			<!-- Category Filter -->
			<div class="flex flex-wrap gap-2">
				{#each categories as cat}
					<button
						type="button"
						on:click={() => (selectedCategory = cat)}
						class="px-3 py-1.5 text-sm rounded-lg border transition-colors {selectedCategory === cat
							? 'bg-brand-500 text-white border-brand-500'
							: 'bg-[var(--bg-card)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-brand-500'}"
					>
						{$t(`exercises.${cat}`)}
					</button>
				{/each}
			</div>

			<!-- Exercise Search & Selection -->
			<div class="relative" bind:this={dropdownWrapper}>
				<label for="exercise-search" class="label">{$t('exercises.selectExercise')}</label>
				<div class="relative">
					<Search size={18} class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
					<input
						id="exercise-search"
						type="text"
						bind:value={searchQuery}
						placeholder={$t('exercises.search')}
						class="input pl-10 pr-10"
						autocomplete="off"
						on:input={() => {
							if (searchQuery.length > 0) {
								showDropdown = true;
								selectedDefinitionId = '';
							} else {
								showDropdown = false;
							}
						}}
						on:focus={() => {
							if (searchQuery.length > 0) showDropdown = true;
						}}
					/>
					{#if searchQuery}
						<button
							type="button"
							on:click={() => { searchQuery = ''; selectedDefinitionId = ''; showDropdown = false; }}
							class="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
						>
							<X size={18} />
						</button>
					{/if}
				</div>

				{#if showDropdown && searchQuery.length > 0}
					<div class="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] shadow-lg">
						{#if filteredDefinitions.length > 0}
							{#each filteredDefinitions.slice(0, 30) as def (def.id)}
								<button
									type="button"
									on:click={() => selectExercise(def)}
									class="w-full flex items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-[var(--bg-secondary)] transition-colors border-b border-[var(--border-color)] last:border-b-0"
								>
									<span class="text-[var(--text-primary)] truncate">{translateExerciseName(def.name)}</span>
									<span class="ml-2 shrink-0 px-2 py-0.5 text-xs rounded-full bg-brand-100 dark:bg-brand-900 text-brand-700 dark:text-brand-300">
										{$t(`exercises.${def.category}`)}
									</span>
								</button>
							{/each}
						{:else}
							<div class="px-4 py-3 text-sm text-[var(--text-secondary)]">
								{$t('exercises.noResults') || 'No exercises found'}
							</div>
						{/if}
						<button
							type="button"
							on:click={selectCustomExercise}
							class="w-full flex items-center gap-2 px-4 py-2.5 text-left text-sm text-brand-500 hover:bg-[var(--bg-secondary)] transition-colors border-t border-[var(--border-color)]"
						>
							<Plus size={16} />
							{$t('exercises.customExercise')}
						</button>
					</div>
				{/if}
			</div>

			<!-- Exercise Selection Dropdown -->
			<div class="relative" bind:this={selectWrapper}>
				<label class="label">{$t('exercises.selectExercise')}</label>
				<button
					type="button"
					on:click={() => { showSelectDropdown = !showSelectDropdown; showDropdown = false; }}
					class="input w-full flex items-center justify-between text-left"
				>
					<span class={selectedDefinitionId ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}>
						{#if selectedDefinitionId === 'custom'}
							{$t('exercises.customExercise')}
						{:else if selectedDefinitionId}
							{@const selectedDef = exerciseDefinitions.find((d) => d.id === selectedDefinitionId)}
							{selectedDef ? translateExerciseName(selectedDef.name) : $t('exercises.selectExercise')}
						{:else}
							{$t('exercises.selectExercise')}
						{/if}
					</span>
					<ChevronDown size={18} class="shrink-0 text-[var(--text-secondary)] transition-transform {showSelectDropdown ? 'rotate-180' : ''}" />
				</button>

				{#if showSelectDropdown}
					<div class="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] shadow-lg">
						{#each filteredDefinitions as def (def.id)}
							<button
								type="button"
								on:click={() => selectExercise(def)}
								class="w-full flex items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-[var(--bg-secondary)] transition-colors border-b border-[var(--border-color)] last:border-b-0
									{selectedDefinitionId === def.id ? 'bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400' : 'text-[var(--text-primary)]'}"
							>
								<span class="truncate">{translateExerciseName(def.name)}</span>
								<span class="ml-2 shrink-0 px-2 py-0.5 text-xs rounded-full bg-brand-100 dark:bg-brand-900 text-brand-700 dark:text-brand-300">
									{$t(`exercises.${def.category}`)}
								</span>
							</button>
						{/each}
						<button
							type="button"
							on:click={selectCustomExercise}
							class="w-full flex items-center gap-2 px-4 py-2.5 text-left text-sm text-brand-500 hover:bg-[var(--bg-secondary)] transition-colors border-t border-[var(--border-color)]"
						>
							<Plus size={16} />
							{$t('exercises.customExercise')}
						</button>
					</div>
				{/if}
			</div>

			<!-- Custom Exercise Fields -->
			{#if selectedDefinitionId === 'custom'}
				<div>
					<label for="customName" class="label">{$t('exercises.exerciseName')}</label>
					<input id="customName" type="text" bind:value={customExerciseName} class="input" required />
				</div>
				<div>
					<label for="customDescription" class="label">{$t('exercises.customDescription')}</label>
					<textarea id="customDescription" bind:value={customExerciseDescription} class="input" rows="2"></textarea>
				</div>
			{/if}

			<!-- Dynamic Measurement Fields -->
			{#if selectedDefinitionId && selectedDefinitionId !== 'custom' && allowedMeasurements.length > 0}
				<div class="space-y-3">
					<label class="label">{$t('exercises.measurements')} ({$t('exercises.optional')})</label>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						{#each allowedMeasurements as measurementType}
							<div>
								<label for={measurementType} class="text-sm text-[var(--text-secondary)] mb-1 block">
									{getMeasurementLabel(measurementType)}
								</label>
								<div class="flex items-center">
									<button
										type="button"
										on:click={() => stepMeasurement(measurementType, -1)}
										class="flex h-[42px] w-11 shrink-0 items-center justify-center rounded-l-lg border border-r-0 border-[var(--border-color)] bg-[var(--bg-secondary)] text-lg font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-card)] hover:text-[var(--text-primary)] transition-colors"
									>&minus;</button>
									<input
										id={measurementType}
										type="number"
										step={getMeasurementStep(measurementType)}
										min="0"
										bind:value={measurements[measurementType]}
										class="input rounded-none border-x-0 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
										placeholder="0"
									/>
									<button
										type="button"
										on:click={() => stepMeasurement(measurementType, 1)}
										class="flex h-[42px] w-11 shrink-0 items-center justify-center rounded-r-lg border border-l-0 border-[var(--border-color)] bg-[var(--bg-secondary)] text-lg font-bold text-[var(--text-secondary)] hover:bg-[var(--bg-card)] hover:text-[var(--text-primary)] transition-colors"
									>+</button>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Common Fields -->
			<div>
				<label class="label">{$t('exercises.performedAt')}</label>
				<DateTimePicker bind:value={performedAt} id="performedAt" required />
			</div>

			<div>
				<label for="notes" class="label">{$t('meals.notes')}</label>
				<textarea id="notes" bind:value={notes} class="input" rows="2"></textarea>
			</div>

			<!-- Photo upload -->
			<div>
				<label class="label">{$t('meals.photos')}</label>
				<!-- Camera capture input (opens camera directly on mobile) -->
				<input
					bind:this={cameraInput}
					type="file"
					accept="image/*"
					capture="environment"
					on:change={handlePhotoSelect}
					class="hidden"
				/>
				<!-- Gallery picker input -->
				<input
					bind:this={fileInput}
					type="file"
					accept="image/*"
					multiple
					on:change={handlePhotoSelect}
					class="hidden"
				/>
				{#if photoPreviews.length > 0}
					<div class="flex flex-wrap gap-2 mb-2">
						{#each photoPreviews as preview, i}
							<div class="relative group">
								<img src={preview} alt="Preview" class="h-20 w-20 rounded-lg object-cover border border-[var(--border-color)]" />
								<button
									type="button"
									on:click={() => removePhoto(i)}
									class="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-white opacity-0 group-hover:opacity-100 transition-opacity"
								>
									<X size={12} />
								</button>
							</div>
						{/each}
					</div>
				{/if}
				{#if selectedPhotos.length < MAX_PHOTOS}
					<div class="flex gap-2">
						<button
							type="button"
							on:click={() => cameraInput.click()}
							class="flex flex-1 items-center justify-center gap-2 rounded-lg border-2 border-dashed border-[var(--border-color)] px-3 py-3 text-sm text-[var(--text-secondary)] hover:border-brand-400 hover:text-brand-500 transition-colors"
						>
							<Camera size={18} />
							{$t('meals.takePhoto')}
						</button>
						<button
							type="button"
							on:click={() => fileInput.click()}
							class="flex flex-1 items-center justify-center gap-2 rounded-lg border-2 border-dashed border-[var(--border-color)] px-3 py-3 text-sm text-[var(--text-secondary)] hover:border-brand-400 hover:text-brand-500 transition-colors"
						>
							<ImagePlus size={18} />
							{$t('meals.choosePhoto')}
						</button>
					</div>
				{:else}
					<p class="text-sm text-[var(--text-secondary)]">{$t('meals.maxPhotos')}</p>
				{/if}
			</div>

			<div class="flex gap-3">
				<button type="submit" class="btn-primary" disabled={formLoading || !selectedDefinitionId}>
					{formLoading ? $t('common.loading') : $t('common.save')}
				</button>
				<button type="button" on:click={resetForm} class="btn-secondary">{$t('common.cancel')}</button>
			</div>
		</form>
	{/if}

	<!-- Time Filter -->
	<div class="flex gap-2 overflow-x-auto">
		{#each ['all', 'day', 'week', 'month', 'year'] as f}
			<button
				on:click={() => (timeFilter = f)}
				class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors {timeFilter === f
					? 'bg-brand-600 text-white'
					: 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}"
			>
				{$t(`common.${f}`)}
			</button>
		{/each}
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if exerciseLogs.length === 0}
		<div class="py-12 text-center">
			<Dumbbell size={48} class="mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
			<p class="text-[var(--text-secondary)]">{$t('exercises.noExercises')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each exerciseLogs as exercise (exercise.id)}
				<div class="card">
					<div class="flex items-start justify-between">
						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2 mb-1">
								<Dumbbell size={18} class="text-brand-500 shrink-0" />
								<span class="font-medium text-[var(--text-primary)] truncate">
									{exercise.exercise_name ? translateExerciseName(exercise.exercise_name) : (exercise.custom_exercise_name || $t('exercises.customExercise'))}
								</span>
							</div>
							<div class="text-sm text-[var(--text-secondary)]">
								{formatDateTime(exercise.performed_at, $locale)}
							</div>
							{#if getMeasurementDisplay(exercise)}
								<div class="mt-2 text-sm text-accent-600 dark:text-accent-400">
									{getMeasurementDisplay(exercise)}
								</div>
							{/if}
							{#if exercise.custom_exercise_description}
								<p class="mt-2 text-sm text-[var(--text-secondary)] whitespace-pre-wrap">
									{exercise.custom_exercise_description}
								</p>
							{/if}
							{#if exercise.notes}
								<p class="mt-2 text-sm text-[var(--text-secondary)] whitespace-pre-wrap">
									{exercise.notes}
								</p>
							{/if}
							{#if exercise.photos && exercise.photos.length > 0}
								<div class="mt-3 flex flex-wrap gap-2">
									{#each exercise.photos as photo}
										<img
											src={photoUrl(photo.storage_key)}
											alt={photo.caption || 'Exercise photo'}
											class="h-20 w-20 rounded-lg object-cover cursor-pointer border border-[var(--border-color)]"
										/>
									{/each}
								</div>
							{/if}
						</div>
						<button
							on:click={() => deleteExerciseLog(exercise.id)}
							class="rounded-lg p-2 text-red-400 hover:bg-red-50 dark:hover:bg-red-950 shrink-0"
						>
							<Trash2 size={16} />
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}

	{:else if currentView === 'routines'}
	<!-- ROUTINES VIEW -->
	<RoutineManager
		{exerciseDefinitions}
		on:routineLogged={loadExerciseLogs}
	/>
	{/if}
</div>

<!-- Delete Confirmation Modal -->
<ConfirmModal
	bind:show={showDeleteConfirm}
	title={$t('common.delete')}
	message={$t('exercises.confirmDelete')}
	onConfirm={confirmDelete}
	loading={deleting}
/>
