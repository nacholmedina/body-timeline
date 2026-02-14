<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { api } from '$lib/api/client';
	import { Users, UserPlus, Link2, TrendingUp } from 'lucide-svelte';

	let stats: any = null;
	let loading = true;

	onMount(async () => {
		try {
			stats = await api.get('/admin/stats');
		} catch (err) {
			console.error('Failed to load stats', err);
		} finally {
			loading = false;
		}
	});
</script>

{#if loading}
	<div class="flex justify-center py-12">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent"></div>
	</div>
{:else if stats}
	<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
		<div class="card p-5">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900">
					<Users size={20} class="text-blue-600 dark:text-blue-400" />
				</div>
				<div>
					<p class="text-sm text-[var(--text-secondary)]">{$t('admin.totalUsers')}</p>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{stats.total_users}</p>
				</div>
			</div>
		</div>

		<div class="card p-5">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900">
					<UserPlus size={20} class="text-green-600 dark:text-green-400" />
				</div>
				<div>
					<p class="text-sm text-[var(--text-secondary)]">{$t('admin.recentRegistrations')}</p>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{stats.recent_registrations}</p>
				</div>
			</div>
		</div>

		<div class="card p-5">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900">
					<Link2 size={20} class="text-purple-600 dark:text-purple-400" />
				</div>
				<div>
					<p class="text-sm text-[var(--text-secondary)]">{$t('admin.totalAssignments')}</p>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{stats.total_assignments}</p>
				</div>
			</div>
		</div>

		<div class="card p-5">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900">
					<TrendingUp size={20} class="text-amber-600 dark:text-amber-400" />
				</div>
				<div>
					<p class="text-sm text-[var(--text-secondary)]">{$t('admin.recentRegistrations')} (30d)</p>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{stats.recent_registrations}</p>
				</div>
			</div>
		</div>
	</div>

	<!-- Role breakdown -->
	<div class="mt-6 card p-5">
		<h3 class="text-lg font-semibold text-[var(--text-primary)] mb-4">{$t('admin.users')} by {$t('admin.role')}</h3>
		<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
			{#each Object.entries(stats.users_by_role) as [role, count]}
				<div class="flex items-center justify-between rounded-lg bg-[var(--bg-secondary)] p-4">
					<span class="text-sm font-medium text-[var(--text-primary)] capitalize">{$t(`roles.${role}`)}</span>
					<span class="text-lg font-bold text-brand-600 dark:text-brand-400">{count}</span>
				</div>
			{/each}
		</div>
	</div>
{/if}
