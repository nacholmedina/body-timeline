<script lang="ts">
	import { page } from '$app/stores';
	import { t } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { BRANDING } from '$lib/config/branding';
	import {
		LayoutDashboard, UtensilsCrossed, Scale, Target,
		Dumbbell, Bell, Calendar, User, Settings, LogOut
	} from 'lucide-svelte';

	export let mobile = false;

	const navItems = [
		{ href: '/app/dashboard', icon: LayoutDashboard, label: 'nav.dashboard' },
		{ href: '/app/meals', icon: UtensilsCrossed, label: 'nav.meals' },
		{ href: '/app/weigh-ins', icon: Scale, label: 'nav.weighIns' },
		{ href: '/app/goals', icon: Target, label: 'nav.goals' },
		{ href: '/app/workouts', icon: Dumbbell, label: 'nav.workouts' },
		{ href: '/app/notifications', icon: Bell, label: 'nav.notifications' },
		{ href: '/app/appointments', icon: Calendar, label: 'nav.appointments' },
	];

	const bottomItems = [
		{ href: '/app/profile', icon: User, label: 'nav.profile' },
		{ href: '/app/settings', icon: Settings, label: 'nav.settings' },
	];

	$: pathname = $page.url.pathname;

	function isActive(href: string, path: string): boolean {
		return path === href || path.startsWith(href + '/');
	}

	function handleLogout() {
		authStore.logout();
		window.location.href = '/login';
	}
</script>

<aside class="{mobile ? 'flex flex-col h-full' : 'hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0'} border-r border-[var(--border-color)] bg-[var(--bg-secondary)]">
	<!-- Logo -->
	<div class="flex items-center gap-3 px-6 py-5 border-b border-[var(--border-color)]">
		<div class="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white font-bold text-sm">
			BT
		</div>
		<span class="text-lg font-semibold text-[var(--text-primary)]">{BRANDING.appName}</span>
	</div>

	<!-- Navigation -->
	<nav class="flex-1 overflow-y-auto px-3 py-4 space-y-1">
		{#each navItems as item}
			<a
				href={item.href}
				class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors
				       {isActive(item.href, pathname)
					? 'bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
					: 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'}"
			>
				<svelte:component this={item.icon} size={20} />
				{$t(item.label)}
			</a>
		{/each}
	</nav>

	<!-- Bottom actions -->
	<div class="border-t border-[var(--border-color)] px-3 py-4 space-y-1">
		{#each bottomItems as item}
			<a
				href={item.href}
				class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors
				       {isActive(item.href, pathname)
					? 'bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
					: 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'}"
			>
				<svelte:component this={item.icon} size={20} />
				{$t(item.label)}
			</a>
		{/each}

		<button
			on:click={handleLogout}
			class="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-red-500 transition-colors hover:bg-red-50 dark:hover:bg-red-950"
		>
			<LogOut size={20} />
			{$t('nav.logout')}
		</button>
	</div>
</aside>
