<script lang="ts">
	import { goto } from '$app/navigation';
	import { t } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { BRANDING } from '$lib/config/branding';
	import { api, ApiError } from '$lib/api/client';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import LanguageToggle from '$components/LanguageToggle.svelte';

	let email = '';
	let password = '';
	let firstName = '';
	let lastName = '';
	let gender = '';
	let error = '';
	let loading = false;

	async function handleRegister() {
		error = '';
		loading = true;
		try {
			const data = await api.post('/auth/register', {
				email,
				password,
				first_name: firstName,
				last_name: lastName,
				gender: gender || undefined
			});
			authStore.login(data.user, data.access_token, data.refresh_token);
			goto('/app/dashboard');
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>{$t('auth.registerTitle')} - {BRANDING.appName}</title>
</svelte:head>

<div class="flex min-h-screen flex-col items-center justify-center px-4 bg-[var(--bg-secondary)]">
	<div class="absolute top-4 right-4 flex gap-2">
		<LanguageToggle />
		<ThemeToggle />
	</div>

	<div class="w-full max-w-sm">
		<div class="mb-8 text-center">
			<img src="/brand-icon-64.png" alt="Wellvio" class="mx-auto mb-4 h-16 w-16 rounded-2xl" />
			<h1 class="text-2xl font-bold text-[var(--text-primary)]">{$t('auth.registerTitle')}</h1>
			<p class="mt-1 text-sm text-[var(--text-secondary)]">{$t('auth.registerSubtitle')}</p>
		</div>

		<form on:submit|preventDefault={handleRegister} class="card space-y-4">
			{#if error}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">
					{error}
				</div>
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
				<label for="gender" class="label">{$t('profile.gender')}</label>
				<select id="gender" bind:value={gender} class="input">
					<option value="">{$t('profile.genderPlaceholder')}</option>
					<option value="male">{$t('profile.genderMale')}</option>
					<option value="female">{$t('profile.genderFemale')}</option>
					<option value="other">{$t('profile.genderOther')}</option>
				</select>
			</div>

			<div>
				<label for="email" class="label">{$t('auth.email')}</label>
				<input id="email" type="email" bind:value={email} class="input" required autocomplete="email" />
			</div>

			<div>
				<label for="password" class="label">{$t('auth.password')}</label>
				<input id="password" type="password" bind:value={password} class="input" required minlength="8" autocomplete="new-password" />
			</div>

			<button type="submit" class="btn-primary w-full" disabled={loading}>
				{loading ? $t('common.loading') : $t('auth.register')}
			</button>
		</form>

		<p class="mt-4 text-center text-sm text-[var(--text-secondary)]">
			{$t('auth.hasAccount')}
			<a href="/login" class="font-medium text-brand-600 hover:text-brand-700">{$t('auth.login')}</a>
		</p>
	</div>
</div>
