<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDate, localToday, formatWeight, kgToLbs, lbsToKg, weightUnit } from '$lib/utils';
	import { onlineStore } from '$stores/online';
	import { addToSyncQueue } from '$lib/offline/db';
	import { unitStore } from '$stores/units';
	import { Plus, Scale, Trash2, TrendingDown, TrendingUp, ChevronDown, Pencil } from 'lucide-svelte';
	import ConfirmModal from '$components/ConfirmModal.svelte';
	import {
		BODY_METRICS,
		displayRange,
		displayToMetric,
		isOutOfRangeMetric,
		metricToDisplay,
		unitFor,
		type BodyMetricKey
	} from '$lib/bodyMetrics';

	let weighIns: any[] = [];
	let loading = true;
	let error = '';
	let showForm = false;

	let weightKg = '';
	let recordedAt = localToday();
	let formLoading = false;
	let formError = '';

	// Edit state. When editingId is set, the form is in edit mode and patches/posts/deletes
	// existing records. editingBodyIds tracks which body-metric log entries already exist
	// for the current recorded_at so we know whether to PATCH/DELETE/POST per metric.
	let editingId: string | null = null;
	let editingBodyIds: Record<BodyMetricKey, string | null> = {} as Record<BodyMetricKey, string | null>;

	// Svelte coerces <input type="number"> bindings to number | '' | null, so values here
	// can be either string (initial '') or number (after user input). Normalize before use.
	type BodyValue = string | number | null | undefined;
	const blankBodyValues = (): Record<BodyMetricKey, BodyValue> =>
		Object.fromEntries(BODY_METRICS.map((m) => [m.key, ''])) as Record<BodyMetricKey, BodyValue>;
	const blankBodyIds = (): Record<BodyMetricKey, string | null> =>
		Object.fromEntries(BODY_METRICS.map((m) => [m.key, null])) as Record<BodyMetricKey, string | null>;
	let bodyValues: Record<BodyMetricKey, BodyValue> = blankBodyValues();

	function isFilled(v: BodyValue): boolean {
		if (v === '' || v === null || v === undefined) return false;
		const n = Number(v);
		return Number.isFinite(n);
	}

	// Delete confirmation
	let showDeleteConfirm = false;
	let weighInToDelete: string | null = null;
	let deleting = false;

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

	function weightToDisplay(kg: number): string {
		const v = $unitStore === 'imperial' ? kgToLbs(kg) : kg;
		return v.toFixed(1);
	}

	async function enterEdit(wi: any) {
		if (!$onlineStore || wi.id?.startsWith('draft-')) return;
		formError = '';
		editingId = wi.id;
		weightKg = weightToDisplay(wi.weight_kg);
		recordedAt = (wi.recorded_at || '').slice(0, 10);
		bodyValues = blankBodyValues();
		editingBodyIds = blankBodyIds();
		showForm = true;

		// One roundtrip: server returns body-comp entries linked to this weigh-in
		// (matched by patient_id + recorded_at) inside `body_metrics`.
		try {
			const res = await api.get(`/weigh-ins/${wi.id}`, { include: 'body_metrics' });
			const body = res.data?.body_metrics || {};
			for (const m of BODY_METRICS) {
				const entry = body[m.key];
				if (entry) {
					editingBodyIds[m.key] = entry.id;
					bodyValues[m.key] = metricToDisplay(m.family, $unitStore, entry[m.key]).toFixed(1);
				}
			}
		} catch (err) {
			console.warn('enterEdit: body-comp lookup failed', err);
		}
		bodyValues = bodyValues;
		editingBodyIds = editingBodyIds;
	}

	function startCreate() {
		resetForm();
		showForm = true;
	}

	async function saveWeighIn() {
		formError = '';
		formLoading = true;
		try {
			const rawValue = parseFloat(weightKg);
			if (!Number.isFinite(rawValue)) {
				formError = $t('weighIns.weight') + ': ' + $t('common.error');
				return;
			}
			if (!recordedAt) {
				formError = $t('weighIns.recordedAt') + ': ' + $t('common.error');
				return;
			}
			const recordedAtIso = new Date(recordedAt + 'T00:00:00').toISOString();
			const weightMetric = $unitStore === 'imperial' ? lbsToKg(rawValue) : rawValue;

			const filledMetrics = BODY_METRICS.filter((m) => isFilled(bodyValues[m.key]));

			// Frontend range validation — backend re-validates.
			for (const m of filledMetrics) {
				const displayValue = Number(bodyValues[m.key]);
				const metricValue = displayToMetric(m.family, $unitStore, displayValue);
				if (isOutOfRangeMetric(m, metricValue)) {
					const r = displayRange(m, $unitStore);
					formError = `${$t(m.labelKey)}: ${$t('profile.bodyComposition.outOfRange')} (${r.min}–${r.max} ${unitFor(m.family, $unitStore)})`;
					return;
				}
			}

			if (editingId) {
				await saveEdit(weightMetric, recordedAtIso, filledMetrics);
			} else {
				await saveCreate(weightMetric, recordedAtIso, filledMetrics);
			}
		} catch (err) {
			console.error('saveWeighIn failed:', err);
			formError = err instanceof Error ? err.message : 'Unexpected error';
		} finally {
			formLoading = false;
		}
	}

	// Build the body_metrics dict for the bulk endpoint: filled values become numbers,
	// every other key becomes null (which the server treats as "delete if exists, else
	// no-op"). This is a full-sync contract — one shot covers create / update / delete.
	function buildBodyMetricsPayload(): Record<string, number | null> {
		const out: Record<string, number | null> = {};
		for (const m of BODY_METRICS) {
			if (isFilled(bodyValues[m.key])) {
				const metricValue = displayToMetric(m.family, $unitStore, Number(bodyValues[m.key]));
				out[m.key] = parseFloat(metricValue.toFixed(2));
			} else {
				out[m.key] = null;
			}
		}
		return out;
	}

	async function saveCreate(
		weightMetric: number,
		recordedAtIso: string,
		filledMetrics: typeof BODY_METRICS
	) {
		const offlinePayload = { weight_kg: weightMetric, recorded_at: recordedAtIso };

		if (!$onlineStore) {
			if (filledMetrics.length > 0) {
				formError = $t('weighIns.bodyOnlineRequired');
				formLoading = false;
				return;
			}
			await addToSyncQueue({ type: 'weighIn', action: 'create', payload: offlinePayload });
			weighIns = [
				{ ...offlinePayload, id: `draft-${Date.now()}`, created_at: new Date().toISOString() },
				...weighIns
			];
			resetForm();
			return;
		}

		try {
			const res = await api.post('/weigh-ins', {
				weight_kg: weightMetric,
				recorded_at: recordedAtIso,
				body_metrics: buildBodyMetricsPayload()
			});
			weighIns = [res.data, ...weighIns];
			resetForm();
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
			formLoading = false;
		}
	}

	async function saveEdit(
		weightMetric: number,
		recordedAtIso: string,
		_filledMetrics: typeof BODY_METRICS
	) {
		if (!$onlineStore) {
			formError = $t('weighIns.editOnlineRequired');
			formLoading = false;
			return;
		}

		try {
			const res = await api.patch(`/weigh-ins/${editingId}`, {
				weight_kg: weightMetric,
				recorded_at: recordedAtIso,
				body_metrics: buildBodyMetricsPayload()
			});
			// Replace the edited row in-place; avoids an extra GET /weigh-ins.
			weighIns = weighIns.map((w) => (w.id === editingId ? res.data : w));
			resetForm();
		} catch (err) {
			formError = err instanceof ApiError ? err.message : 'Failed';
			formLoading = false;
		}
	}

	function deleteWeighIn(id: string) {
		weighInToDelete = id;
		showDeleteConfirm = true;
	}

	async function confirmDelete() {
		if (!weighInToDelete) return;
		deleting = true;
		try {
			await api.delete(`/weigh-ins/${weighInToDelete}`);
			weighIns = weighIns.filter((w) => w.id !== weighInToDelete);
			showDeleteConfirm = false;
			weighInToDelete = null;
		} catch (err) {
			error = 'Failed to delete weigh-in';
		} finally {
			deleting = false;
		}
	}

	function resetForm() {
		showForm = false;
		weightKg = '';
		recordedAt = localToday();
		formLoading = false;
		formError = '';
		bodyValues = blankBodyValues();
		editingId = null;
		editingBodyIds = blankBodyIds();
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
		<button on:click={() => (showForm ? resetForm() : startCreate())} class="btn-primary flex items-center gap-2 shrink-0">
			<Plus size={18} />
			<span class="hidden sm:inline">{$t('weighIns.addWeighIn')}</span>
		</button>
	</div>

	{#if showForm}
		<form on:submit|preventDefault={saveWeighIn} class="card space-y-4">
			<p class="text-sm font-semibold text-[var(--text-primary)]">
				{editingId ? $t('weighIns.editWeighIn') : $t('weighIns.addWeighIn')}
			</p>
			{#if formError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{formError}</div>
			{/if}
			<div>
				<label for="weight" class="label">{$t('weighIns.weight')} ({weightUnit($unitStore)})</label>
				<input id="weight" type="number" step="0.1" bind:value={weightKg} class="input" required />
			</div>
			<div>
				<label for="recordedAt" class="label">{$t('weighIns.recordedAt')}</label>
				<input id="recordedAt" type="date" bind:value={recordedAt} class="input" required />
			</div>

			<details class="rounded-lg border border-[var(--border)] p-3 group" open={editingId !== null && Object.values(editingBodyIds).some((v) => v !== null)}>
				<summary class="flex cursor-pointer items-center justify-between gap-2 list-none">
					<span class="text-sm font-medium text-[var(--text-primary)]">
						{$t('profile.bodyComposition.sectionTitle')}
					</span>
					<ChevronDown size={16} class="shrink-0 text-[var(--text-secondary)] transition-transform group-open:rotate-180" />
				</summary>
				<div class="mt-3 space-y-3">
					{#each BODY_METRICS as metric (metric.key)}
						{@const range = displayRange(metric, $unitStore)}
						{@const u = unitFor(metric.family, $unitStore)}
						<div>
							<label for="bm-{metric.key}" class="label">
								{$t(metric.labelKey)} ({u})
							</label>
							<input
								id="bm-{metric.key}"
								type="number"
								step="0.1"
								min={range.min}
								max={range.max}
								placeholder="{range.min}–{range.max}"
								bind:value={bodyValues[metric.key]}
								class="input"
							/>
						</div>
					{/each}
				</div>
			</details>

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
					<div class="flex items-center gap-4 min-w-0">
						<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-950 shrink-0">
							{#if getTrend(index) === 'down'}
								<TrendingDown size={22} class="text-green-500" />
							{:else if getTrend(index) === 'up'}
								<TrendingUp size={22} class="text-red-500" />
							{:else}
								<Scale size={22} class="text-brand-500" />
							{/if}
						</div>
						<div class="min-w-0">
							<p class="text-xl font-bold text-[var(--text-primary)]">{formatWeight(wi.weight_kg, $unitStore)}</p>
							<p class="text-xs text-[var(--text-secondary)]">{formatDate(wi.recorded_at, $locale)}</p>
						</div>
					</div>
					{#if !wi.id?.startsWith('draft-')}
						<div class="flex items-center gap-1 shrink-0">
							<button
								on:click={() => enterEdit(wi)}
								class="rounded-lg p-2 text-[var(--text-secondary)] hover:bg-brand-50 dark:hover:bg-brand-950 hover:text-brand-600"
								aria-label={$t('common.edit')}
							>
								<Pencil size={16} />
							</button>
							<button
								on:click={() => deleteWeighIn(wi.id)}
								class="rounded-lg p-2 text-red-400 hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600"
								aria-label={$t('common.delete')}
							>
								<Trash2 size={16} />
							</button>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Delete Confirmation Modal -->
<ConfirmModal
	bind:show={showDeleteConfirm}
	title={$t('common.delete')}
	message={$t('weighIns.confirmDelete')}
	onConfirm={confirmDelete}
	loading={deleting}
/>
