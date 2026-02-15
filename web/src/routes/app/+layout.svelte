<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { t } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import Sidebar from '$components/Sidebar.svelte';
	import BottomNav from '$components/BottomNav.svelte';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import LanguageToggle from '$components/LanguageToggle.svelte';
	import { BRANDING } from '$lib/config/branding';
	import { Menu, X, User, Settings, LogOut, ShieldAlert } from 'lucide-svelte';
	import { browser } from '$app/environment';
	import { api, photoUrl } from '$lib/api/client';
	import { unreadCount } from '$stores/notifications';

	let mobileMenuOpen = false;
	let avatarMenuOpen = false;
	let isImpersonating = false;
	let impersonatingName = '';

	if (browser) {
		const saved = sessionStorage.getItem('bt_impersonation');
		if (saved) {
			isImpersonating = true;
		}
	}

	$: if (browser && isImpersonating && $authStore.user) {
		impersonatingName = `${$authStore.user.first_name} ${$authStore.user.last_name}`;
	}

	function stopImpersonation() {
		const saved = sessionStorage.getItem('bt_impersonation');
		if (saved) {
			const adminState = JSON.parse(saved);
			authStore.login(adminState.user, adminState.accessToken, adminState.refreshToken);
			sessionStorage.removeItem('bt_impersonation');
			window.location.href = '/app/admin/users';
		}
	}

	function handleLogout() {
		sessionStorage.removeItem('bt_impersonation');
		authStore.logout();
		window.location.href = '/login';
	}

	function toggleAvatarMenu(e: MouseEvent) {
		e.stopPropagation();
		avatarMenuOpen = !avatarMenuOpen;
	}

	async function fetchUnreadCount() {
		try {
			const res = await api.get('/notifications/unread-count');
			unreadCount.set(res.count || 0);
		} catch {}
	}

	onMount(() => {
		const unsubscribe = authStore.subscribe((state) => {
			if (!state.isAuthenticated) {
				goto('/login');
			}
		});
		fetchUnreadCount();
		return unsubscribe;
	});
</script>

<svelte:window on:click={() => (avatarMenuOpen = false)} />

{#if $authStore.isAuthenticated}
	{#if isImpersonating}
		<div class="fixed top-0 left-0 right-0 z-50 flex items-center justify-center gap-3 bg-amber-500 text-white px-4 py-2 text-sm font-medium">
			<ShieldAlert size={16} />
			<span>{$t('admin.impersonating')} <strong>{impersonatingName}</strong></span>
			<button
				on:click={stopImpersonation}
				class="ml-2 rounded-lg bg-white/20 px-3 py-1 text-xs font-semibold hover:bg-white/30 transition-colors"
			>
				{$t('admin.stopImpersonating')}
			</button>
		</div>
	{/if}

	<Sidebar />

	<div class="lg:pl-64" class:pt-10={isImpersonating}>
		<!-- Top bar -->
		<header class="sticky z-30 flex items-center justify-between border-b border-[var(--border-color)] bg-[var(--bg-card)] px-4 py-3 lg:px-6 lg:py-5" class:top-10={isImpersonating} class:top-0={!isImpersonating}>
			<div class="flex items-center gap-3">
				<button
					on:click={() => (mobileMenuOpen = !mobileMenuOpen)}
					class="lg:hidden rounded-lg p-1.5 text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]"
				>
					{#if mobileMenuOpen}<X size={22} />{:else}<Menu size={22} />{/if}
				</button>
				<h2 class="text-lg font-semibold text-[var(--text-primary)] lg:hidden">{BRANDING.appName}</h2>
			</div>

			<div class="flex items-center gap-1">
				<LanguageToggle />
				<ThemeToggle />
				<div class="relative ml-2">
					<button
						on:click={toggleAvatarMenu}
						class="flex h-8 w-8 items-center justify-center rounded-full overflow-hidden bg-brand-100 text-sm font-medium text-brand-700 dark:bg-brand-900 dark:text-brand-300 hover:ring-2 hover:ring-brand-400 transition-shadow"
					>
						{#if $authStore.user?.profile?.avatar_url}
							<img src={photoUrl($authStore.user.profile.avatar_url)} alt="" class="h-full w-full object-cover" />
						{:else}
							{$authStore.user?.first_name?.[0] || '?'}{$authStore.user?.last_name?.[0] || ''}
						{/if}
					</button>

					{#if avatarMenuOpen}
						<div class="absolute right-0 mt-2 w-56 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-lg py-1 z-50">
							<div class="px-4 py-3 border-b border-[var(--border-color)]">
								<p class="text-sm font-medium text-[var(--text-primary)]">{$authStore.user?.first_name} {$authStore.user?.last_name}</p>
								<p class="text-xs text-[var(--text-secondary)] truncate">{$authStore.user?.email}</p>
							</div>
							<a
								href="/app/profile"
								class="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] transition-colors"
							>
								<User size={16} />
								{$t('nav.profile')}
							</a>
							<a
								href="/app/settings"
								class="flex items-center gap-3 px-4 py-2.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)] transition-colors"
							>
								<Settings size={16} />
								{$t('nav.settings')}
							</a>
							<div class="border-t border-[var(--border-color)] mt-1 pt-1">
								<button
									on:click={handleLogout}
									class="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
								>
									<LogOut size={16} />
									{$t('nav.logout')}
								</button>
							</div>
						</div>
					{/if}
				</div>
			</div>
		</header>

		<!-- Mobile sidebar overlay -->
		{#if mobileMenuOpen}
			<div class="fixed inset-0 z-40 lg:hidden">
				<button
					class="absolute inset-0 bg-black/50"
					on:click={() => (mobileMenuOpen = false)}
					aria-label="Close menu"
				/>
				<div class="absolute inset-y-0 left-0 w-64 border-r border-[var(--border-color)] bg-[var(--bg-secondary)]">
					<Sidebar mobile={true} />
				</div>
			</div>
		{/if}

		<!-- Main content -->
		<main class="px-4 py-6 pb-24 lg:px-6 lg:pb-6">
			<slot />
		</main>
	</div>

	<BottomNav />
{/if}
