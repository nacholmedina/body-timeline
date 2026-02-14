<script lang="ts">
	import { t } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { api, ApiError } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { User } from 'lucide-svelte';

	let firstName = $authStore.user?.first_name || '';
	let lastName = $authStore.user?.last_name || '';
	let bio = $authStore.user?.profile?.bio || '';
	let phone = $authStore.user?.profile?.phone || '';
	let dateOfBirth = $authStore.user?.profile?.date_of_birth || '';
	let heightCm = $authStore.user?.profile?.height_cm?.toString() || '';

	let loading = false;
	let error = '';
	let success = false;

	async function saveProfile() {
		loading = true;
		error = '';
		success = false;
		try {
			const res = await api.patch('/auth/me', {
				first_name: firstName,
				last_name: lastName,
				bio: bio || null,
				phone: phone || null,
				date_of_birth: dateOfBirth || null,
				height_cm: heightCm ? parseFloat(heightCm) : null
			});
			authStore.updateUser(res.user);
			success = true;
			setTimeout(() => (success = false), 3000);
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to save';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>{$t('profile.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="mx-auto max-w-lg space-y-6">
	<h1 class="text-2xl font-bold text-[var(--text-primary)]">{$t('profile.title')}</h1>

	<!-- Avatar -->
	<div class="flex items-center gap-4">
		<div class="flex h-20 w-20 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900">
			<User size={36} class="text-brand-600 dark:text-brand-400" />
		</div>
		<div>
			<p class="text-lg font-semibold text-[var(--text-primary)]">{firstName} {lastName}</p>
			<p class="text-sm text-[var(--text-secondary)]">{$authStore.user?.email}</p>
			<span class="mt-1 inline-block rounded-full bg-brand-50 dark:bg-brand-950 px-2.5 py-0.5 text-xs font-medium text-brand-700 dark:text-brand-300">
				{$t(`roles.${$authStore.user?.role}`)}
			</span>
		</div>
	</div>

	<form on:submit|preventDefault={saveProfile} class="card space-y-4">
		{#if error}
			<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{error}</div>
		{/if}
		{#if success}
			<div class="rounded-lg bg-green-50 dark:bg-green-950 p-3 text-sm text-green-600 dark:text-green-400">{$t('common.success')}</div>
		{/if}

		<div class="grid grid-cols-2 gap-3">
			<div>
				<label for="firstName" class="label">{$t('auth.firstName')}</label>
				<input id="firstName" type="text" bind:value={firstName} class="input" required />
			</div>
			<div>
				<label for="lastName" class="label">{$t('auth.lastName')}</label>
				<input id="lastName" type="text" bind:value={lastName} class="input" required />
			</div>
		</div>

		<div>
			<label for="bio" class="label">{$t('profile.bio')}</label>
			<textarea id="bio" bind:value={bio} class="input" rows="3"></textarea>
		</div>

		<div class="grid grid-cols-2 gap-3">
			<div>
				<label for="phone" class="label">{$t('profile.phone')}</label>
				<input id="phone" type="tel" bind:value={phone} class="input" />
			</div>
			<div>
				<label for="dob" class="label">{$t('profile.dateOfBirth')}</label>
				<input id="dob" type="date" bind:value={dateOfBirth} class="input" />
			</div>
		</div>

		<div>
			<label for="height" class="label">{$t('profile.height')}</label>
			<input id="height" type="number" step="0.1" bind:value={heightCm} class="input" />
		</div>

		<button type="submit" class="btn-primary w-full" disabled={loading}>
			{loading ? $t('common.loading') : $t('common.save')}
		</button>
	</form>
</div>
