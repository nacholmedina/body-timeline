<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDate } from '$lib/utils';
	import { Plus, Target, Check, Circle, Trash2, Edit2 } from 'lucide-svelte';
	import ConfirmModal from '$components/ConfirmModal.svelte';

	let goals: any[] = [];
	let loading = true;
	let error = '';
	let showForm = false;
	let filterPeriod: string = '';
	let filterCompleted: string = '';

	let editingGoal: any = null;
	let title = '';
	let description = '';
	let period = 'weekly';
	let targetDate = '';
	let formLoading = false;
	let formError = '';

	// Delete confirmation
	let showDeleteConfirm = false;
	let goalToDelete: string | null = null;
	let deleting = false;

	async function loadGoals() {
		loading = true;
		try {
			const params: Record<string, string> = {};
			if (filterPeriod) params.period = filterPeriod;
			if (filterCompleted) params.completed = filterCompleted;
			const res = await api.get('/goals', params);
			goals = res.data;
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	function startEditGoal(goal: any) {
		editingGoal = goal;
		title = goal.title;
		description = goal.description || '';
		period = goal.period;
		targetDate = goal.target_date || '';
		formError = '';
		showForm = true;
	}

	async function saveGoal() {
		formError = '';
		formLoading = true;
		try {
			const payload = {
				title,
				description: description || undefined,
				period,
				target_date: targetDate || undefined
			};

			if (editingGoal) {
				const res = await api.patch(`/goals/${editingGoal.id}`, payload);
				goals = goals.map((g) => (g.id === editingGoal.id ? res.data : g));
			} else {
				const res = await api.post('/goals', payload);
				goals = [res.data, ...goals];
			}
			resetForm();
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			formLoading = false;
		}
	}

	async function toggleGoal(id: string) {
		try {
			const res = await api.post(`/goals/${id}/toggle`);
			goals = goals.map((g) => (g.id === id ? res.data : g));
		} catch {}
	}

	function deleteGoal(id: string) {
		goalToDelete = id;
		showDeleteConfirm = true;
	}

	async function confirmDelete() {
		if (!goalToDelete) return;
		deleting = true;
		try {
			await api.delete(`/goals/${goalToDelete}`);
			goals = goals.filter((g) => g.id !== goalToDelete);
			showDeleteConfirm = false;
			goalToDelete = null;
		} catch (err) {
			error = 'Failed to delete goal';
		} finally {
			deleting = false;
		}
	}

	function resetForm() {
		showForm = false;
		editingGoal = null;
		title = '';
		description = '';
		period = 'weekly';
		targetDate = '';
		formLoading = false;
	}

	onMount(loadGoals);
</script>

<svelte:head>
	<title>{$t('goals.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between gap-3">
		<h1 class="text-2xl font-bold text-[var(--text-primary)] min-w-0 truncate">{$t('goals.title')}</h1>
		<button on:click={() => { if (showForm && !editingGoal) { resetForm(); } else { resetForm(); showForm = true; } }} class="btn-primary flex items-center gap-2 shrink-0">
			<Plus size={18} />
			<span class="hidden sm:inline">{$t('goals.addGoal')}</span>
		</button>
	</div>

	<!-- Filters -->
	<div class="flex flex-wrap gap-2">
		{#each ['', 'weekly', 'monthly', 'yearly'] as p}
			<button
				on:click={() => { filterPeriod = p; loadGoals(); }}
				class="rounded-full px-4 py-1.5 text-sm font-medium transition-colors
				       {filterPeriod === p
					? 'bg-brand-600 text-white'
					: 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'}"
			>
				{p === '' ? $t('common.all') : $t(`goals.${p}`)}
			</button>
		{/each}
		<span class="mx-1"></span>
		{#each [['', 'common.all'], ['false', 'goals.pending'], ['true', 'goals.completed']] as [val, labelKey]}
			<button
				on:click={() => { filterCompleted = val; loadGoals(); }}
				class="rounded-full px-4 py-1.5 text-sm font-medium transition-colors
				       {filterCompleted === val
					? 'bg-accent-600 text-white'
					: 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]'}"
			>
				{$t(labelKey)}
			</button>
		{/each}
	</div>

	{#if showForm}
		<form on:submit|preventDefault={saveGoal} class="card space-y-4">
			<h2 class="text-lg font-semibold text-[var(--text-primary)]">
				{editingGoal ? $t('goals.editGoal') : $t('goals.addGoal')}
			</h2>
			{#if formError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{formError}</div>
			{/if}
			<div>
				<label for="title" class="label">{$t('goals.goalTitle')}</label>
				<input id="title" type="text" bind:value={title} class="input" required />
			</div>
			<div>
				<label for="desc" class="label">{$t('meals.description')}</label>
				<textarea id="desc" bind:value={description} class="input" rows="2"></textarea>
			</div>
			<div class="grid grid-cols-2 gap-3">
				<div>
					<label for="period" class="label">{$t('goals.period')}</label>
					<select id="period" bind:value={period} class="input">
						<option value="weekly">{$t('goals.weekly')}</option>
						<option value="monthly">{$t('goals.monthly')}</option>
						<option value="yearly">{$t('goals.yearly')}</option>
					</select>
				</div>
				<div>
					<label for="targetDate" class="label">{$t('goals.targetDate')}</label>
					<input id="targetDate" type="date" bind:value={targetDate} class="input" />
				</div>
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
	{:else if goals.length === 0}
		<div class="py-12 text-center">
			<Target size={48} class="mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
			<p class="text-[var(--text-secondary)]">{$t('goals.noGoals')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each goals as goal (goal.id)}
				<div class="card flex items-start gap-3">
					<button
						on:click={() => toggleGoal(goal.id)}
						class="mt-0.5 flex-shrink-0 rounded-lg p-1 transition-colors
						       {goal.is_completed ? 'text-accent-500' : 'text-[var(--text-secondary)] hover:text-accent-500'}"
					>
						{#if goal.is_completed}
							<Check size={22} />
						{:else}
							<Circle size={22} />
						{/if}
					</button>
					<div class="flex-1 min-w-0">
						<h3 class="font-medium {goal.is_completed ? 'line-through text-[var(--text-secondary)]' : 'text-[var(--text-primary)]'}">
							{goal.title}
						</h3>
						{#if goal.description}
							<p class="mt-1 text-sm text-[var(--text-secondary)]">{goal.description}</p>
						{/if}
						<div class="mt-2 flex gap-2">
							<span class="inline-flex items-center rounded-full bg-brand-50 dark:bg-brand-950 px-2 py-0.5 text-xs font-medium text-brand-700 dark:text-brand-300">
								{$t(`goals.${goal.period}`)}
							</span>
							{#if goal.target_date}
								<span class="text-xs text-[var(--text-secondary)]">{formatDate(goal.target_date, $locale)}</span>
							{/if}
						</div>
					</div>
					<div class="flex gap-1 shrink-0">
						<button
							on:click={() => startEditGoal(goal)}
							class="rounded-lg p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
							title={$t('common.edit')}
						>
							<Edit2 size={16} />
						</button>
						<button
							on:click={() => deleteGoal(goal.id)}
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

<!-- Delete Confirmation Modal -->
<ConfirmModal
	bind:show={showDeleteConfirm}
	title={$t('common.delete')}
	message={$t('goals.confirmDelete')}
	onConfirm={confirmDelete}
	loading={deleting}
/>
