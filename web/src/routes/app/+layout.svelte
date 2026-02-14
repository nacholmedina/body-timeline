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
	import { Menu, X, User, Settings, LogOut } from 'lucide-svelte';

	let mobileMenuOpen = false;
	let avatarMenuOpen = false;

	function handleLogout() {
		authStore.logout();
		window.location.href = '/login';
	}

	function toggleAvatarMenu(e: MouseEvent) {
		e.stopPropagation();
		avatarMenuOpen = !avatarMenuOpen;
	}

	onMount(() => {
		const unsubscribe = authStore.subscribe((state) => {
			if (!state.isAuthenticated) {
				goto('/login');
			}
		});
		return unsubscribe;
	});
</script>

<svelte:window on:click={() => (avatarMenuOpen = false)} />

{#if $authStore.isAuthenticated}
	<Sidebar />

	<div class="lg:pl-64">
		<!-- Top bar -->
		<header class="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--border-color)] bg-[var(--bg-card)] px-4 py-3 lg:px-6 lg:py-5">
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
						class="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-medium text-brand-700 dark:bg-brand-900 dark:text-brand-300 hover:ring-2 hover:ring-brand-400 transition-shadow"
					>
						{$authStore.user?.first_name?.[0] || '?'}{$authStore.user?.last_name?.[0] || ''}
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
