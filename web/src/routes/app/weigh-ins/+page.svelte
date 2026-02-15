<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDate, localToday } from '$lib/utils';
	import { onlineStore } from '$stores/online';
	import { addToSyncQueue } from '$lib/offline/db';
	import { Plus, Scale, Trash2, TrendingDown, TrendingUp } from 'lucide-svelte';

	let weighIns: any[] = [];
	let loading = true;
	let error = '';
	let showForm = false;

	let weightKg = '';
	let recordedAt = localToday();
	let formLoading = false;
	let formError = '';

	async function loadWeighIns() {
		loading = true;
		try {
			const res = await api.get('/weigh-ins');
			weighIns = res.data;
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	async function createWeighIn() {
		formError = '';
		formLoading = true;
		const payload = {
			weight_kg: parseFloat(weightKg),
			recorded_at: new Date(recordedAt + 'T00:00:00').toISOString()
		};

		if (!$onlineStore) {
			await addToSyncQueue({ type: 'weighIn', action: 'create', payload });
			weighIns = [{ ...payload, id: `draft-${Date.now()}`, created_at: new Date().toISOString() }, ...weighIns];
			resetForm();
			return;
		}

		try {
			await api.post('/weigh-ins', payload);
			resetForm();
			await loadWeighIns();
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
		} finally {
			formLoading = false;
		}
	}

	async function deleteWeighIn(id: string) {
		await api.delete(`/weigh-ins/${id}`);
		weighIns = weighIns.filter((w) => w.id !== id);
	}

	function resetForm() {
		showForm = false;
		weightKg = '';
		recordedAt = localToday();
		formLoading = false;
	}

	function getTrend(index: number): 'up' | 'down' | 'same' {
		if (index >= weighIns.length - 1) return 'same';
		const current = weighIns[index].weight_kg;
		const previous = weighIns[index + 1].weight_kg;
		if (current > previous) return 'up';
		if (current < previous) return 'down';
		return 'same';
	}

	onMount(loadWeighIns);
</script>

<svelte:head>
	<title>{$t('weighIns.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between gap-3">
		<h1 class="text-2xl font-bold text-[var(--text-primary)] min-w-0 truncate">{$t('weighIns.title')}</h1>
		<button on:click={() => (showForm = !showForm)} class="btn-primary flex items-center gap-2 shrink-0">
			<Plus size={18} />
			<span class="hidden sm:inline">{$t('weighIns.addWeighIn')}</span>
		</button>
	</div>

	{#if showForm}
		<form on:submit|preventDefault={createWeighIn} class="card space-y-4">
			{#if formError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{formError}</div>
			{/if}
			<div>
				<label for="weight" class="label">{$t('weighIns.weight')}</label>
				<input id="weight" type="number" step="0.1" bind:value={weightKg} class="input" required />
			</div>
			<div>
				<label for="recordedAt" class="label">{$t('weighIns.recordedAt')}</label>
				<input id="recordedAt" type="date" bind:value={recordedAt} class="input" required />
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
	{:else if weighIns.length === 0}
		<div class="py-12 text-center">
			<Scale size={48} class="mx-auto mb-4 text-[var(--text-secondary)] opacity-50" />
			<p class="text-[var(--text-secondary)]">{$t('weighIns.noWeighIns')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each weighIns as wi, index (wi.id)}
				<div class="card flex items-center justify-between">
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-950">
							{#if getTrend(index) === 'down'}
								<TrendingDown size={22} class="text-green-500" />
							{:else if getTrend(index) === 'up'}
								<TrendingUp size={22} class="text-red-500" />
							{:else}
								<Scale size={22} class="text-brand-500" />
							{/if}
						</div>
						<div>
							<p class="text-xl font-bold text-[var(--text-primary)]">{wi.weight_kg} kg</p>
							<p class="text-xs text-[var(--text-secondary)]">{formatDate(wi.recorded_at, $locale)}</p>
						</div>
					</div>
					{#if !wi.id?.startsWith('draft-')}
						<button
							on:click={() => deleteWeighIn(wi.id)}
							class="rounded-lg p-2 text-red-400 hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600"
						>
							<Trash2 size={16} />
						</button>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
