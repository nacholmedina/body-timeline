<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { BRANDING } from '$lib/config/branding';
	import { api, ApiError } from '$lib/api/client';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import LanguageToggle from '$components/LanguageToggle.svelte';
	import { Eye, EyeOff } from 'lucide-svelte';

	const GOOGLE_CLIENT_ID = '195898924440-jmhmuef02mb8afdioumnhj40bbrgms01.apps.googleusercontent.com';

	const errorMap: Record<string, string> = {
		'Invalid email or password': 'auth.invalidEmailOrPassword',
		'Email already registered': 'auth.emailAlreadyRegistered',
	};

	function translateError(msg: string): string {
		const key = errorMap[msg];
		return key ? $t(key) : msg;
	}

	let email = '';
	let password = '';
	let showPassword = false;
	let error = '';
	let loading = false;
	let emailNotVerified = false;
	let resendLoading = false;
	let resendSuccess = false;
	let googleLoading = false;

	async function handleLogin() {
		error = '';
		emailNotVerified = false;
		resendSuccess = false;
		loading = true;
		try {
			const data = await api.post('/auth/login', { email, password });
			authStore.login(data.user, data.access_token, data.refresh_token);
			goto('/app/dashboard');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.message === 'Please verify your email before logging in') {
					emailNotVerified = true;
					error = $t('auth.emailNotVerified');
				} else {
					error = translateError(err.message);
				}
			} else {
				error = $t('auth.loginFailed');
			}
		} finally {
			loading = false;
		}
	}

	async function handleResendVerification() {
		resendLoading = true;
		resendSuccess = false;
		try {
			await api.post('/auth/resend-verification', { email });
			resendSuccess = true;
		} catch {
			resendSuccess = true;
		} finally {
			resendLoading = false;
		}
	}

	async function handleGoogleCredential(credential: string) {
		error = '';
		googleLoading = true;
		try {
			const data = await api.post('/auth/google', { credential });
			authStore.login(data.user, data.access_token, data.refresh_token);
			goto('/app/dashboard');
		} catch (err) {
			error = err instanceof ApiError ? translateError(err.message) : $t('auth.googleSignInFailed');
		} finally {
			googleLoading = false;
		}
	}

	function handleGoogleClick() {
		const google = (window as any).google;
		if (!google?.accounts?.id) {
			error = 'Google SDK not loaded yet. Please try again.';
			return;
		}
		google.accounts.id.prompt((notification: any) => {
			if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
				google.accounts.id.prompt();
			}
		});
	}

	onMount(() => {
		const script = document.createElement('script');
		script.src = 'https://accounts.google.com/gsi/client';
		script.async = true;
		script.onload = () => {
			const google = (window as any).google;
			google.accounts.id.initialize({
				client_id: GOOGLE_CLIENT_ID,
				callback: (response: any) => handleGoogleCredential(response.credential),
				auto_select: false,
			});
		};
		document.head.appendChild(script);
	});
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
		<div class="mb-8 text-center">
			<img src="/brand-icon-64.png" alt="Wellvio" class="mx-auto mb-4 h-16 w-16 rounded-2xl" />
			<h1 class="text-2xl font-bold text-[var(--text-primary)]">{BRANDING.appName}</h1>
			<p class="mt-1 text-sm text-[var(--text-secondary)]">{$t('auth.loginSubtitle')}</p>
		</div>

		<form on:submit|preventDefault={handleLogin} class="card space-y-4">
			{#if error}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">
					{error}
					{#if emailNotVerified}
						<button
							type="button"
							on:click={handleResendVerification}
							disabled={resendLoading}
							class="mt-2 block w-full text-center font-medium text-brand-600 hover:text-brand-700 underline"
						>
							{resendLoading ? $t('common.loading') : $t('auth.resendVerification')}
						</button>
					{/if}
				</div>
			{/if}

			{#if resendSuccess}
				<div class="rounded-lg bg-green-50 dark:bg-green-950 p-3 text-sm text-green-600 dark:text-green-400">
					{$t('auth.resendSuccess')}
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

		<!-- Google Sign-In -->
		<div class="mt-4">
			<div class="relative my-4">
				<div class="absolute inset-0 flex items-center">
					<div class="w-full border-t border-[var(--border-primary)]"></div>
				</div>
				<div class="relative flex justify-center text-xs">
					<span class="bg-[var(--bg-secondary)] px-3 text-[var(--text-secondary)]">{$t('auth.orContinueWith')}</span>
				</div>
			</div>
			<button
				type="button"
				on:click={handleGoogleClick}
				disabled={googleLoading}
				class="flex w-full items-center justify-center gap-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] px-4 py-3 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-secondary)]"
			>
				<svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
					<path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4"/>
					<path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853"/>
					<path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.997 8.997 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z" fill="#FBBC05"/>
					<path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 6.29C4.672 4.163 6.656 2.58 9 3.58Z" fill="#EA4335"/>
				</svg>
				{googleLoading ? $t('common.loading') : $t('auth.continueWithGoogle')}
			</button>
		</div>

		<p class="mt-4 text-center text-sm text-[var(--text-secondary)]">
			{$t('auth.noAccount')}
			<a href="/register" class="font-medium text-brand-600 hover:text-brand-700">{$t('auth.register')}</a>
		</p>
	</div>
</div>
