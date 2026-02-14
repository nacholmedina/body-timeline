<script lang="ts">
	import { page } from '$app/stores';
	import { t } from '$i18n/index';
	import { LayoutDashboard, UtensilsCrossed, Target, Dumbbell, Bell } from 'lucide-svelte';

	const items = [
		{ href: '/app/dashboard', icon: LayoutDashboard, label: 'nav.dashboard' },
		{ href: '/app/meals', icon: UtensilsCrossed, label: 'nav.meals' },
		{ href: '/app/goals', icon: Target, label: 'nav.goals' },
		{ href: '/app/workouts', icon: Dumbbell, label: 'nav.workouts' },
		{ href: '/app/notifications', icon: Bell, label: 'nav.notifications' },
	];

	$: pathname = $page.url.pathname;

	function isActive(href: string, path: string): boolean {
		return path === href || path.startsWith(href + '/');
	}
</script>

<nav class="fixed bottom-0 left-0 right-0 z-40 border-t border-[var(--border-color)] bg-[var(--bg-card)] lg:hidden safe-area-bottom">
	<div class="flex items-center justify-around py-2 px-1">
		{#each items as item}
			<a
				href={item.href}
				class="flex flex-col items-center gap-0.5 px-1 py-1 min-w-0 flex-1 text-[0.65rem] font-medium transition-colors
				       {isActive(item.href, pathname)
					? 'text-brand-600 dark:text-brand-400'
					: 'text-[var(--text-secondary)]'}"
			>
				<svelte:component this={item.icon} size={20} />
				<span class="truncate w-full text-center">{$t(item.label)}</span>
			</a>
		{/each}
	</div>
</nav>

<style>
	.safe-area-bottom {
		padding-bottom: env(safe-area-inset-bottom, 0px);
	}
</style>
