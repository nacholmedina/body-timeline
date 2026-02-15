<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { formatDate } from '$lib/utils';
	import { Plus, Trash2, X } from 'lucide-svelte';

	interface Assignment {
		id: string;
		professional_id: string;
		patient_id: string;
		professional_name: string;
		patient_name: string;
		is_active: boolean;
		created_at: string;
	}

	interface UserOption {
		id: string;
		first_name: string;
		last_name: string;
		email: string;
	}

	let assignments: Assignment[] = [];
	let loading = true;

	// Create modal
	let showCreate = false;
	let professionals: UserOption[] = [];
	let patients: UserOption[] = [];
	let selectedProfessional = '';
	let selectedPatient = '';
	let createError = '';
	let creating = false;

	async function loadAssignments() {
		loading = true;
		try {
			const res = await api.get('/admin/assignments');
			assignments = res.data;
		} catch (err) {
			console.error('Failed to load assignments', err);
		} finally {
			loading = false;
		}
	}

	async function loadUsersForCreate() {
		try {
			const [proRes, patRes] = await Promise.all([
				api.get('/admin/users', { role: 'professional', limit: '100' }),
				api.get('/admin/users', { role: 'patient', limit: '100' })
			]);
			professionals = proRes.data;
			patients = patRes.data;
		} catch (err) {
			console.error('Failed to load users', err);
		}
	}

	function openCreate() {
		showCreate = true;
		selectedProfessional = '';
		selectedPatient = '';
		createError = '';
		loadUsersForCreate();
	}

	async function handleCreate() {
		if (!selectedProfessional || !selectedPatient) {
			createError = 'Select both professional and patient';
			return;
		}
		createError = '';
		creating = true;
		try {
			await api.post('/admin/assignments', {
				professional_id: selectedProfessional,
				patient_id: selectedPatient
			});
			showCreate = false;
			loadAssignments();
		} catch (err) {
			createError = err instanceof ApiError ? err.message : 'Failed to create assignment';
		} finally {
			creating = false;
		}
	}

	async function removeAssignment(id: string) {
		try {
			await api.delete(`/admin/assignments/${id}`);
			assignments = assignments.filter((a) => a.id !== id);
		} catch (err) {
			console.error('Failed to remove assignment', err);
		}
	}

	onMount(loadAssignments);
</script>

<div class="flex items-center justify-between mb-6">
	<div></div>
	<button on:click={openCreate} class="btn-primary flex items-center gap-2">
		<Plus size={16} />
		{$t('admin.assignProfessional')}
	</button>
</div>

{#if loading}
	<div class="flex justify-center py-12">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent"></div>
	</div>
{:else if assignments.length === 0}
	<div class="card p-8 text-center text-[var(--text-secondary)]">{$t('admin.noAssignments')}</div>
{:else}
	<div class="card overflow-hidden">
		<div class="overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('admin.professional')}</th>
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('admin.patient')}</th>
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('appointments.dateTime')}</th>
						<th class="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each assignments as assignment (assignment.id)}
						<tr class="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors">
							<td class="px-4 py-3 font-medium text-[var(--text-primary)]">{assignment.professional_name}</td>
							<td class="px-4 py-3 text-[var(--text-primary)]">{assignment.patient_name}</td>
							<td class="px-4 py-3 text-[var(--text-secondary)]">{formatDate(assignment.created_at, $locale)}</td>
							<td class="px-4 py-3 text-right">
								<button
									on:click={() => removeAssignment(assignment.id)}
									class="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
								>
									<Trash2 size={14} />
									{$t('admin.removeAssignment')}
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
{/if}

<!-- Create assignment modal -->
{#if showCreate}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<button class="absolute inset-0 bg-black/50" on:click={() => (showCreate = false)} aria-label="Close" />
		<div class="relative w-full max-w-md card p-6 space-y-4">
			<div class="flex items-center justify-between">
				<h3 class="text-lg font-semibold text-[var(--text-primary)]">{$t('admin.assignProfessional')}</h3>
				<button on:click={() => (showCreate = false)} class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
					<X size={20} />
				</button>
			</div>

			{#if createError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{createError}</div>
			{/if}

			<form on:submit|preventDefault={handleCreate} class="space-y-3">
				<div>
					<label for="a_pro" class="label">{$t('admin.selectProfessional')}</label>
					<select id="a_pro" bind:value={selectedProfessional} class="input" required>
						<option value="">--</option>
						{#each professionals as p}
							<option value={p.id}>{p.first_name} {p.last_name} ({p.email})</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="a_pat" class="label">{$t('admin.selectPatient')}</label>
					<select id="a_pat" bind:value={selectedPatient} class="input" required>
						<option value="">--</option>
						{#each patients as p}
							<option value={p.id}>{p.first_name} {p.last_name} ({p.email})</option>
						{/each}
					</select>
				</div>
				<div class="flex gap-3 pt-2">
					<button type="button" on:click={() => (showCreate = false)} class="btn-secondary flex-1">{$t('common.cancel')}</button>
					<button type="submit" class="btn-primary flex-1" disabled={creating}>
						{creating ? $t('common.loading') : $t('admin.assignProfessional')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
