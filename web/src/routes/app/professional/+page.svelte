<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { t, locale } from '$i18n/index';
	import { api } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatWeight } from '$lib/utils';
	import { unitStore } from '$stores/units';
	import { Users, UserPlus, Mail, TrendingUp, UtensilsCrossed, Dumbbell, Calendar as CalendarIcon } from 'lucide-svelte';

	let patients: any[] = [];
	let invitations: any[] = [];
	let loading = true;
	let showInviteModal = false;
	let inviteEmail = '';
	let inviteMessage = '';
	let inviting = false;
	let inviteError = '';

	$: localeCode = $locale === 'es' ? 'es-ES' : 'en-US';

	// Map backend error messages to translation keys
	function translateError(message: string): string {
		const errorMap: Record<string, string> = {
			'User not found. Ask patient to register first.': $t('professional.userNotFound'),
			'Patient already assigned': $t('professional.patientAlreadyAssigned'),
			'Invitation already sent to this patient': $t('professional.invitationExists')
		};
		return errorMap[message] || message;
	}

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		try {
			loading = true;
			const [patientsRes, invitationsRes] = await Promise.all([
				api.get('/professional/patients'),
				api.get('/professional/invitations')
			]);
			patients = patientsRes.data || [];
			invitations = invitationsRes.data || [];
		} catch (err: any) {
			console.error('Failed to load professional data:', err);
		} finally {
			loading = false;
		}
	}

	async function sendInvitation() {
		if (!inviteEmail.trim()) {
			inviteError = $t('professional.emailRequired');
			return;
		}

		try {
			inviting = true;
			inviteError = '';
			await api.post('/professional/invitations', {
				patient_email: inviteEmail,
				message: inviteMessage || undefined
			});
			showInviteModal = false;
			inviteEmail = '';
			inviteMessage = '';
			await loadData();
		} catch (err: any) {
			inviteError = translateError(err.message || $t('professional.invitationFailed'));
		} finally {
			inviting = false;
		}
	}

	function openInviteModal() {
		showInviteModal = true;
		inviteError = '';
		inviteEmail = '';
		inviteMessage = '';
	}
</script>

<svelte:head>
	<title>{$t('professional.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-[var(--text-primary)]">{$t('professional.title')}</h1>
			<p class="text-sm text-[var(--text-secondary)]">
				{patients.length} {patients.length === 1 ? $t('professional.patientSingular') : $t('professional.patients')}
			</p>
		</div>
		<div class="flex items-center gap-2">
			<a
				href="/app/professional/calendar"
				class="flex items-center gap-2 rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
			>
				<CalendarIcon size={18} />
				<span class="hidden sm:inline">{$t('professional.calendar')}</span>
			</a>
			<button
				on:click={openInviteModal}
				class="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors"
			>
				<UserPlus size={18} />
				<span class="hidden sm:inline">{$t('professional.invitePatient')}</span>
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else}
		<!-- Pending Invitations -->
		{#if invitations.filter((i) => i.status === 'pending').length > 0}
			<div class="card">
				<div class="mb-4 flex items-center gap-2">
					<Mail size={18} class="text-amber-600" />
					<h3 class="font-semibold text-[var(--text-primary)]">{$t('professional.invitations')}</h3>
				</div>
				<div class="space-y-2">
					{#each invitations.filter((i) => i.status === 'pending') as invitation}
						<div class="flex items-center justify-between rounded-lg bg-amber-50 dark:bg-amber-950 p-3">
							<div>
								<p class="text-sm font-medium text-[var(--text-primary)]">{invitation.patient_email}</p>
								<p class="text-xs text-[var(--text-secondary)]">
									{$t('professional.sent')} {new Date(invitation.created_at).toLocaleDateString(localeCode)}
								</p>
							</div>
							<span class="rounded-full bg-amber-200 dark:bg-amber-800 px-3 py-1 text-xs font-medium text-amber-900 dark:text-amber-100">
								{$t('invitations.pending')}
							</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Patients Grid -->
		{#if patients.length > 0}
			<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{#each patients as patient}
					<button
						on:click={() => goto(`/app/professional/patients/${patient.id}`)}
						class="card p-5 text-left transition-all hover:shadow-lg hover:border-brand-300 dark:hover:border-brand-700"
					>
						<!-- Avatar & Name -->
						<div class="flex items-center gap-3 mb-4">
							<div class="flex h-12 w-12 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900">
								<span class="text-lg font-bold text-brand-600 dark:text-brand-400">
									{patient.first_name?.[0]}{patient.last_name?.[0]}
								</span>
							</div>
							<div>
								<p class="font-semibold text-[var(--text-primary)]">
									{patient.first_name} {patient.last_name}
								</p>
								<p class="text-xs text-[var(--text-secondary)]">{patient.email}</p>
							</div>
						</div>

						<!-- Stats -->
						<div class="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-[var(--border-color)]">
							<div class="text-center">
								<div class="flex items-center justify-center gap-1 mb-1">
									<TrendingUp size={14} class="text-green-600 dark:text-green-400" />
									<p class="text-xs text-[var(--text-secondary)]">{$t('professional.latestWeight')}</p>
								</div>
								<p class="text-sm font-bold text-[var(--text-primary)]">
									{patient.latest_weight ? formatWeight(patient.latest_weight, $unitStore) : '-'}
								</p>
							</div>
							<div class="text-center">
								<div class="flex items-center justify-center gap-1 mb-1">
									<UtensilsCrossed size={14} class="text-orange-600 dark:text-orange-400" />
									<p class="text-xs text-[var(--text-secondary)]">{$t('nav.meals')}</p>
								</div>
								<p class="text-sm font-bold text-[var(--text-primary)]">{patient.total_meals || 0}</p>
							</div>
							<div class="text-center">
								<div class="flex items-center justify-center gap-1 mb-1">
									<Dumbbell size={14} class="text-blue-600 dark:text-blue-400" />
									<p class="text-xs text-[var(--text-secondary)]">{$t('nav.workouts')}</p>
								</div>
								<p class="text-sm font-bold text-[var(--text-primary)]">{patient.total_workouts || 0}</p>
							</div>
						</div>
					</button>
				{/each}
			</div>
		{:else}
			<div class="card p-12 text-center">
				<Users size={48} class="mx-auto mb-4 text-[var(--text-secondary)]" />
				<p class="text-lg font-medium text-[var(--text-primary)]">{$t('professional.noPatients')}</p>
			</div>
		{/if}
	{/if}
</div>

<!-- Invite Modal -->
{#if showInviteModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-md rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl">
			<h2 class="mb-4 text-xl font-bold text-[var(--text-primary)]">{$t('professional.inviteByEmail')}</h2>

			<div class="space-y-4">
				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
						{$t('professional.patientEmail')}
					</label>
					<input
						type="email"
						bind:value={inviteEmail}
						class="input w-full"
						placeholder="patient@example.com"
					/>
				</div>

				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
						{$t('professional.invitationMessage')} ({$t('common.optional')})
					</label>
					<textarea
						bind:value={inviteMessage}
						class="input w-full"
						rows="3"
						placeholder={$t('professional.invitationMessage')}
					></textarea>
				</div>

				{#if inviteError}
					<p class="text-sm text-red-600 dark:text-red-400">{inviteError}</p>
				{/if}

				<div class="flex gap-3">
					<button
						on:click={() => (showInviteModal = false)}
						class="flex-1 rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
						disabled={inviting}
					>
						{$t('common.cancel')}
					</button>
					<button
						on:click={sendInvitation}
						class="flex-1 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
						disabled={inviting}
					>
						{#if inviting}
							<span class="flex items-center justify-center gap-2">
								<span class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
								{$t('professional.sending')}
							</span>
						{:else}
							{$t('professional.sendInvitation')}
						{/if}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.input {
		@apply rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500;
	}
</style>
