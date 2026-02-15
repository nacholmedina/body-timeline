<script lang="ts">
	import { page } from '$app/stores';
	import { t } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { unreadCount } from '$stores/notifications';
	import { BRANDING } from '$lib/config/branding';
	import {
		LayoutDashboard, UtensilsCrossed, Scale, Target,
		Dumbbell, Bell, Calendar, User, Settings, LogOut, ShieldCheck, Users
	} from 'lucide-svelte';

	export let mobile = false;

	const patientOnlyItems = ['/app/meals', '/app/weigh-ins', '/app/goals', '/app/workouts'];

	const allNavItems = [
		{ href: '/app/dashboard', icon: LayoutDashboard, label: 'nav.dashboard' },
		{ href: '/app/meals', icon: UtensilsCrossed, label: 'nav.meals' },
		{ href: '/app/weigh-ins', icon: Scale, label: 'nav.weighIns' },
		{ href: '/app/goals', icon: Target, label: 'nav.goals' },
		{ href: '/app/workouts', icon: Dumbbell, label: 'nav.workouts' },
		{ href: '/app/notifications', icon: Bell, label: 'nav.notifications' },
		{ href: '/app/appointments', icon: Calendar, label: 'nav.appointments' },
	];

	$: navItems = $authStore.user?.role === 'patient'
		? allNavItems
		: allNavItems.filter(item => !patientOnlyItems.includes(item.href));

	$: isAdmin = $authStore.user?.role === 'devadmin';
	$: isProfessional = $authStore.user?.role === 'professional';

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
			Wv
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
				<div class="relative">
					<svelte:component this={item.icon} size={20} />
					{#if item.href === '/app/notifications' && $unreadCount > 0}
						<span class="absolute -top-1.5 -right-1.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[0.6rem] font-bold text-white">
							{$unreadCount > 99 ? '99+' : $unreadCount}
						</span>
					{/if}
				</div>
				{$t(item.label)}
			</a>
		{/each}

		{#if isProfessional || isAdmin}
			<div class="pt-3 mt-3 border-t border-[var(--border-color)]">
				{#if isProfessional}
					<a
						href="/app/professional"
						class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors
						       {isActive('/app/professional', pathname)
							? 'bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
							: 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'}"
					>
						<Users size={20} />
						{$t('nav.myPatients')}
					</a>
				{/if}
				{#if isAdmin}
					<a
						href="/app/admin"
						class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors
						       {isActive('/app/admin', pathname)
							? 'bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
							: 'text-[var(--text-secondary)] hover:bg-[var(--bg-primary)] hover:text-[var(--text-primary)]'}"
					>
						<ShieldCheck size={20} />
						{$t('nav.admin')}
					</a>
				{/if}
			</div>
		{/if}
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
