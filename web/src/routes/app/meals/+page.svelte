<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { api, ApiError, photoUrl } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime } from '$lib/utils';
	import { onlineStore } from '$stores/online';
	import { addToSyncQueue } from '$lib/offline/db';
	import { Plus, Trash2, UtensilsCrossed, Camera, X } from 'lucide-svelte';
	import DateTimePicker from '$components/DateTimePicker.svelte';

	let meals: any[] = [];
	let loading = true;
	let error = '';
	let showForm = false;
	let mounted = false;

	// Form state
	let description = '';
	let eatenAt = new Date().toISOString().slice(0, 16);
	let notes = '';
	let selectedPhotos: File[] = [];
	let photoPreviews: string[] = [];
	let formLoading = false;
	let formError = '';
	let fileInput: HTMLInputElement;

	// Filters
	let filter: 'all' | 'day' | 'week' | 'month' | 'year' = 'all';

	function getFilterParams(): Record<string, string> {
		const now = new Date();
		const params: Record<string, string> = {};
		if (filter === 'day') {
			params.from = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
		} else if (filter === 'week') {
			const weekAgo = new Date(now.getTime() - 7 * 86400000);
			params.from = weekAgo.toISOString();
		} else if (filter === 'month') {
			params.from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
		} else if (filter === 'year') {
			params.from = new Date(now.getFullYear(), 0, 1).toISOString();
		}
		return params;
	}

	async function loadMeals() {
		loading = true;
		error = '';
		try {
			const params = getFilterParams();
			const res = await api.get('/meals', params);
			meals = res.data;
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load meals';
		} finally {
			loading = false;
		}
	}

	function handlePhotoSelect(e: Event) {
		const input = e.target as HTMLInputElement;
		if (!input.files?.length) return;
		for (const file of Array.from(input.files)) {
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

	async function createMeal() {
		formError = '';
		formLoading = true;
		const payload = {
			description,
			eaten_at: new Date(eatenAt).toISOString(),
			notes: notes || undefined
		};

		if (!$onlineStore) {
			await addToSyncQueue({ type: 'meal', action: 'create', payload });
			meals = [{ ...payload, id: `draft-${Date.now()}`, created_at: new Date().toISOString(), photos: [] }, ...meals];
			resetForm();
			return;
		}

		try {
			const res = await api.post('/meals', payload);
			const newMeal = res.data;

			// Upload photos if any
			for (let i = 0; i < selectedPhotos.length; i++) {
				try {
					await api.upload(`/meals/${newMeal.id}/photos`, selectedPhotos[i], { sort_order: String(i) });
				} catch {}
			}

			resetForm();
			await loadMeals();
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed to create meal';
		} finally {
			formLoading = false;
		}
	}

	async function deleteMeal(id: string) {
		try {
			await api.delete(`/meals/${id}`);
			meals = meals.filter((m) => m.id !== id);
		} catch (err) {
			error = 'Failed to delete meal';
		}
	}

	function resetForm() {
		showForm = false;
		description = '';
		eatenAt = new Date().toISOString().slice(0, 16);
		notes = '';
		photoPreviews.forEach((url) => URL.revokeObjectURL(url));
		selectedPhotos = [];
		photoPreviews = [];
		formLoading = false;
	}

	onMount(() => {
		loadMeals();
		mounted = true;
	});

	$: if (mounted && filter) {
		loadMeals();
	}
</script>

<svelte:head>
	<title>{$t('meals.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between gap-3">
		<h1 class="text-2xl font-bold text-[var(--text-primary)] min-w-0 truncate">{$t('meals.title')}</h1>
		<button on:click={() => (showForm = !showForm)} class="btn-primary flex items-center gap-2 shrink-0">
			<Plus size={18} />
			<span class="hidden sm:inline">{$t('meals.addMeal')}</span>
		</button>
	</div>

	<!-- Filters -->
	<div class="flex gap-2 overflow-x-auto">
		{#each ['all', 'day', 'week', 'month', 'year'] as f}
			<button
				on:click={() => (filter = f)}
				class="rounded-full px-4 py-1.5 text-sm font-medium transition-colors
				       {filter === f
					? 'bg-brand-600 text-white'
					: 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-card)]'}"
			>
				{$t(`common.${f}`)}
			</button>
		{/each}
	</div>

	<!-- Create Form -->
	{#if showForm}
		<form on:submit|preventDefault={createMeal} class="card space-y-4">
			{#if formError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{formError}</div>
			{/if}
			<div>
				<label for="description" class="label">{$t('meals.description')}</label>
				<input id="description" type="text" bind:value={description} class="input" required />
			</div>
			<div>
				<label class="label">{$t('meals.eatenAt')}</label>
				<DateTimePicker bind:value={eatenAt} id="eatenAt" required />
			</div>
			<div>
				<label for="notes" class="label">{$t('meals.notes')}</label>
				<textarea id="notes" bind:value={notes} class="input" rows="2"></textarea>
			</div>

			<!-- Photo upload -->
			<div>
				<label class="label">{$t('meals.photos')}</label>
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
				<button
					type="button"
					on:click={() => fileInput.click()}
					class="flex items-center gap-2 rounded-lg border-2 border-dashed border-[var(--border-color)] px-4 py-3 text-sm text-[var(--text-secondary)] hover:border-brand-400 hover:text-brand-500 transition-colors"
				>
					<Camera size={18} />
					{$t('meals.addPhoto')}
				</button>
			</div>

			<div class="flex gap-3">
				<button type="submit" class="btn-primary" disabled={formLoading}>
					{formLoading ? $t('common.loading') : $t('common.save')}
				</button>
				<button type="button" on:click={resetForm} class="btn-secondary">{$t('common.cancel')}</button>
			</div>
		</form>
	{/if}

	<!-- Meals List -->
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if error}
		<div class="rounded-lg bg-red-50 dark:bg-red-950 p-4 text-sm text-red-600 dark:text-red-400">{error}</div>
	{:else if meals.length === 0}
		<div class="py-12 text-center">
			<UtensilsCrossed size={48} class="mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
			<p class="text-[var(--text-secondary)]">{$t('meals.noMeals')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each meals as meal (meal.id)}
				<div class="card flex items-start justify-between">
					<div class="flex-1">
						<h3 class="font-medium text-[var(--text-primary)]">{meal.description}</h3>
						<p class="mt-1 text-xs text-[var(--text-secondary)]">{formatDateTime(meal.eaten_at || meal.eaten_at)}</p>
						{#if meal.notes}
							<p class="mt-2 text-sm text-[var(--text-secondary)]">{meal.notes}</p>
						{/if}
						{#if meal.photos?.length > 0}
							<div class="mt-2 flex gap-2 overflow-x-auto">
								{#each meal.photos as photo}
									<img
										src={photoUrl(photo.url)}
										alt={photo.caption || meal.description}
										class="h-16 w-16 rounded-lg object-cover border border-[var(--border-color)] flex-shrink-0"
									/>
								{/each}
							</div>
						{/if}
						{#if meal.id?.startsWith('draft-')}
							<span class="mt-2 inline-block rounded-full bg-amber-100 dark:bg-amber-900 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-300">
								{$t('meals.draftOffline')}
							</span>
						{/if}
					</div>
					{#if !meal.id?.startsWith('draft-')}
						<button
							on:click={() => deleteMeal(meal.id)}
							class="ml-2 rounded-lg p-2 text-red-400 hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600"
						>
							<Trash2 size={16} />
						</button>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
