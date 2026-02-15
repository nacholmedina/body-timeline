<script lang="ts">
	import { goto } from '$app/navigation';
	import { t } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { BRANDING } from '$lib/config/branding';
	import { api, ApiError } from '$lib/api/client';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import LanguageToggle from '$components/LanguageToggle.svelte';
	import { Eye, EyeOff } from 'lucide-svelte';

	let email = '';
	let password = '';
	let showPassword = false;
	let error = '';
	let loading = false;

	async function handleLogin() {
		error = '';
		loading = true;
		try {
			const data = await api.post('/auth/login', { email, password });
			authStore.login(data.user, data.access_token, data.refresh_token);
			goto('/app/dashboard');
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>{$t('auth.loginTitle')} - {BRANDING.appName}</title>
</svelte:head>

<div class="flex min-h-screen flex-col items-center justify-center px-4 bg-[var(--bg-secondary)]">
	<div class="absolute top-4 right-4 flex gap-2">
		<LanguageToggle />
		<ThemeToggle />
	</div>

	<div class="w-full max-w-sm">
		<!-- Logo -->
		<div class="mb-8 text-center">
			<div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-600 text-white text-2xl font-bold">
				Wv
			</div>
			<h1 class="text-2xl font-bold text-[var(--text-primary)]">{BRANDING.appName}</h1>
			<p class="mt-1 text-sm text-[var(--text-secondary)]">{$t('auth.loginSubtitle')}</p>
		</div>

		<!-- Form -->
		<form on:submit|preventDefault={handleLogin} class="card space-y-4">
			{#if error}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">
					{error}
				</div>
			{/if}

			<div>
				<label for="email" class="label">{$t('auth.email')}</label>
				<input id="email" type="email" bind:value={email} class="input" required autocomplete="email" />
			</div>

			<div>
				<label for="password" class="label">{$t('auth.password')}</label>
				<div class="relative">
					{#if showPassword}
						<input id="password" type="text" bind:value={password} class="input pr-10" required autocomplete="current-password" />
					{:else}
						<input id="password" type="password" bind:value={password} class="input pr-10" required autocomplete="current-password" />
					{/if}
					<button
						type="button"
						on:click={() => (showPassword = !showPassword)}
						class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
					>
						{#if showPassword}<EyeOff size={18} />{:else}<Eye size={18} />{/if}
					</button>
				</div>
			</div>

			<button type="submit" class="btn-primary w-full" disabled={loading}>
				{loading ? $t('common.loading') : $t('auth.login')}
			</button>
		</form>

		<p class="mt-4 text-center text-sm text-[var(--text-secondary)]">
			{$t('auth.noAccount')}
			<a href="/register" class="font-medium text-brand-600 hover:text-brand-700">{$t('auth.register')}</a>
		</p>
	</div>
</div>
