<script lang="ts">
	import { page } from '$app/stores';
	import { t } from '$i18n/index';
	import { BRANDING } from '$lib/config/branding';
	import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-svelte';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import LanguageToggle from '$components/LanguageToggle.svelte';

	$: status = $page.url.searchParams.get('status');
	$: token = $page.url.searchParams.get('token');

	// If there's a token but no status, the user clicked the email link directly
	// The backend /auth/verify-email endpoint redirects here with a status param
	// So if we have a token, redirect to the backend to verify it
	$: if (token && !status && typeof window !== 'undefined') {
		const apiBase = import.meta.env.VITE_PUBLIC_API_URL || 'http://localhost:5000/api/v1';
		window.location.href = `${apiBase}/auth/verify-email?token=${token}`;
	}
</script>

<svelte:head>
	<title>{$t('auth.verifyEmailTitle')} - {BRANDING.appName}</title>
</svelte:head>

<div class="flex min-h-screen flex-col items-center justify-center px-4 bg-[var(--bg-secondary)]">
	<div class="absolute top-4 right-4 flex gap-2">
		<LanguageToggle />
		<ThemeToggle />
	</div>

	<div class="w-full max-w-sm">
		<div class="mb-8 text-center">
			<img src="/brand-icon-64.png" alt="Wellvio" class="mx-auto mb-4 h-16 w-16 rounded-2xl" />
		</div>

		<div class="card space-y-4 text-center">
			{#if !status && token}
				<!-- Redirecting to verify -->
				<div class="mx-auto flex h-16 w-16 items-center justify-center">
					<Loader2 size={40} class="text-brand-600 animate-spin" />
				</div>
				<p class="text-sm text-[var(--text-secondary)]">{$t('auth.verifyingEmail')}</p>

			{:else if status === 'success'}
				<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
					<CheckCircle size={32} class="text-green-600" />
				</div>
				<h2 class="text-lg font-semibold text-[var(--text-primary)]">{$t('auth.verifyEmailTitle')}</h2>
				<p class="text-sm text-[var(--text-secondary)]">{$t('auth.verifySuccess')}</p>
				<a href="/login" class="btn-primary inline-block w-full text-center">{$t('auth.goToLogin')}</a>

			{:else if status === 'already_verified'}
				<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
					<CheckCircle size={32} class="text-brand-600" />
				</div>
				<h2 class="text-lg font-semibold text-[var(--text-primary)]">{$t('auth.verifyEmailTitle')}</h2>
				<p class="text-sm text-[var(--text-secondary)]">{$t('auth.verifyAlreadyVerified')}</p>
				<a href="/login" class="btn-primary inline-block w-full text-center">{$t('auth.goToLogin')}</a>

			{:else if status === 'expired'}
				<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900/30">
					<AlertCircle size={32} class="text-yellow-600" />
				</div>
				<h2 class="text-lg font-semibold text-[var(--text-primary)]">{$t('auth.verifyEmailTitle')}</h2>
				<p class="text-sm text-[var(--text-secondary)]">{$t('auth.verifyExpired')}</p>
				<a href="/login" class="btn-primary inline-block w-full text-center">{$t('auth.backToLogin')}</a>

			{:else}
				<div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
					<XCircle size={32} class="text-red-600" />
				</div>
				<h2 class="text-lg font-semibold text-[var(--text-primary)]">{$t('auth.verifyEmailTitle')}</h2>
				<p class="text-sm text-[var(--text-secondary)]">{$t('auth.verifyError')}</p>
				<a href="/login" class="btn-primary inline-block w-full text-center">{$t('auth.backToLogin')}</a>
			{/if}
		</div>
	</div>
</div>
