<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { LayoutDashboard, Users, Link2, Dumbbell } from 'lucide-svelte';

	const tabs = [
		{ href: '/app/admin', icon: LayoutDashboard, label: 'admin.overview' },
		{ href: '/app/admin/users', icon: Users, label: 'admin.users' },
		{ href: '/app/admin/assignments', icon: Link2, label: 'admin.assignments' },
		{ href: '/app/admin/exercises', icon: Dumbbell, label: 'admin.exercises' },
	];

	$: pathname = $page.url.pathname;

	function isActive(href: string, path: string): boolean {
		if (href === '/app/admin') return path === href;
		return path === href || path.startsWith(href + '/');
	}

	onMount(() => {
		if ($authStore.user?.role !== 'devadmin') {
			goto('/app/dashboard');
		}
	});
</script>

<div>
	<div class="mb-6">
		<h1 class="text-2xl font-bold text-[var(--text-primary)]">{$t('admin.title')}</h1>
	</div>

	<!-- Tabs -->
	<div class="flex gap-1 mb-6 overflow-x-auto overflow-y-hidden border-b border-[var(--border-color)]">
		{#each tabs as tab}
			<a
				href={tab.href}
				class="flex items-center gap-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors -mb-px
				       {isActive(tab.href, pathname)
					? 'border-brand-600 text-brand-600 dark:text-brand-400 dark:border-brand-400'
					: 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-color)]'}"
			>
				<svelte:component this={tab.icon} size={16} />
				{$t(tab.label)}
			</a>
		{/each}
	</div>

	<slot />
</div>
