<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { api, ApiError } from '$lib/api/client';
	import { authStore } from '$stores/auth';
	import {
		Search, Plus, Eye, UserCheck, UserX, ChevronDown, X
	} from 'lucide-svelte';

	interface UserItem {
		id: string;
		email: string;
		first_name: string;
		last_name: string;
		role: string;
		is_active: boolean;
		created_at: string;
	}

	let users: UserItem[] = [];
	let loading = true;
	let search = '';
	let roleFilter = '';
	let page = 1;
	let total = 0;
	const limit = 20;

	// Create user modal
	let showCreate = false;
	let createForm = { email: '', password: '', first_name: '', last_name: '', role: 'patient' };
	let createError = '';
	let creating = false;

	// Role change
	let roleEditId: string | null = null;
	let roleEditValue = '';

	async function loadUsers() {
		loading = true;
		try {
			const params: Record<string, string> = {
				page: String(page),
				limit: String(limit)
			};
			if (search) params.search = search;
			if (roleFilter) params.role = roleFilter;
			const res = await api.get('/admin/users', params);
			users = res.data;
			total = res.total;
		} catch (err) {
			console.error('Failed to load users', err);
		} finally {
			loading = false;
		}
	}

	onMount(loadUsers);

	let searchTimeout: ReturnType<typeof setTimeout>;
	function handleSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			page = 1;
			loadUsers();
		}, 300);
	}

	function handleRoleFilter() {
		page = 1;
		loadUsers();
	}

	async function toggleActive(user: UserItem) {
		try {
			const res = await api.post(`/admin/users/${user.id}/toggle-active`);
			user.is_active = res.data.is_active;
			users = users;
		} catch (err) {
			console.error('Failed to toggle active', err);
		}
	}

	function startRoleEdit(user: UserItem) {
		roleEditId = user.id;
		roleEditValue = user.role;
	}

	async function saveRole(user: UserItem) {
		if (roleEditValue === user.role) {
			roleEditId = null;
			return;
		}
		try {
			const res = await api.patch(`/admin/users/${user.id}/role`, { role: roleEditValue });
			user.role = res.data.role;
			users = users;
		} catch (err) {
			console.error('Failed to change role', err);
		}
		roleEditId = null;
	}

	async function handleCreate() {
		createError = '';
		creating = true;
		try {
			await api.post('/admin/users', createForm);
			showCreate = false;
			createForm = { email: '', password: '', first_name: '', last_name: '', role: 'patient' };
			loadUsers();
		} catch (err) {
			createError = err instanceof ApiError ? err.message : 'Failed to create user';
		} finally {
			creating = false;
		}
	}

	async function impersonate(user: UserItem) {
		try {
			const res = await api.post(`/admin/impersonate/${user.id}`);
			// Save admin state to sessionStorage before switching
			const adminState = {
				user: $authStore.user,
				accessToken: $authStore.accessToken,
				refreshToken: $authStore.refreshToken,
			};
			sessionStorage.setItem('wv_impersonation', JSON.stringify(adminState));
			// Login as the target user
			authStore.login(res.user, res.access_token, res.refresh_token);
			window.location.href = '/app/dashboard';
		} catch (err) {
			console.error('Failed to impersonate', err);
		}
	}

	$: totalPages = Math.ceil(total / limit);
</script>

<!-- Header -->
<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
	<div class="flex flex-col sm:flex-row gap-3 flex-1">
		<div class="relative flex-1 max-w-sm">
			<Search size={16} class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
			<input
				type="text"
				bind:value={search}
				on:input={handleSearch}
				placeholder={$t('admin.searchUsers')}
				class="input pl-9 w-full"
			/>
		</div>
		<select bind:value={roleFilter} on:change={handleRoleFilter} class="input w-auto">
			<option value="">{$t('admin.allRoles')}</option>
			<option value="devadmin">{$t('roles.devadmin')}</option>
			<option value="professional">{$t('roles.professional')}</option>
			<option value="patient">{$t('roles.patient')}</option>
		</select>
	</div>
	<button on:click={() => (showCreate = true)} class="btn-primary flex items-center gap-2">
		<Plus size={16} />
		{$t('admin.createUser')}
	</button>
</div>

<!-- Users table -->
{#if loading}
	<div class="flex justify-center py-12">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent"></div>
	</div>
{:else if users.length === 0}
	<div class="card p-8 text-center text-[var(--text-secondary)]">{$t('admin.noUsers')}</div>
{:else}
	<div class="card overflow-hidden">
		<div class="overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('auth.firstName')}</th>
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('auth.email')}</th>
						<th class="text-left px-4 py-3 font-medium text-[var(--text-secondary)]">{$t('admin.role')}</th>
						<th class="text-center px-4 py-3 font-medium text-[var(--text-secondary)]">Status</th>
						<th class="text-right px-4 py-3 font-medium text-[var(--text-secondary)]">Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each users as user (user.id)}
						<tr class="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors">
							<td class="px-4 py-3">
								<div class="font-medium text-[var(--text-primary)]">{user.first_name} {user.last_name}</div>
							</td>
							<td class="px-4 py-3 text-[var(--text-secondary)]">{user.email}</td>
							<td class="px-4 py-3">
								{#if roleEditId === user.id}
									<div class="flex items-center gap-2">
										<select bind:value={roleEditValue} class="input py-1 px-2 text-xs w-auto">
											<option value="devadmin">{$t('roles.devadmin')}</option>
											<option value="professional">{$t('roles.professional')}</option>
											<option value="patient">{$t('roles.patient')}</option>
										</select>
										<button on:click={() => saveRole(user)} class="text-green-600 hover:text-green-700">
											<UserCheck size={16} />
										</button>
										<button on:click={() => (roleEditId = null)} class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
											<X size={16} />
										</button>
									</div>
								{:else}
									<button
										on:click={() => startRoleEdit(user)}
										class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium
										{user.role === 'devadmin' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
										 user.role === 'professional' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' :
										 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'}"
									>
										{$t(`roles.${user.role}`)}
										<ChevronDown size={12} />
									</button>
								{/if}
							</td>
							<td class="px-4 py-3 text-center">
								<button
									on:click={() => toggleActive(user)}
									class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors
									{user.is_active
										? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
										: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'}"
								>
									{user.is_active ? $t('admin.active') : $t('admin.inactive')}
								</button>
							</td>
							<td class="px-4 py-3 text-right">
								{#if user.id !== $authStore.user?.id}
									<button
										on:click={() => impersonate(user)}
										class="inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-950 transition-colors"
										title={$t('admin.viewAs')}
									>
										<Eye size={14} />
										{$t('admin.viewAs')}
									</button>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>

	<!-- Pagination -->
	{#if totalPages > 1}
		<div class="flex items-center justify-between mt-4">
			<p class="text-sm text-[var(--text-secondary)]">{total} {$t('admin.users').toLowerCase()}</p>
			<div class="flex gap-1">
				{#each Array.from({ length: totalPages }, (_, i) => i + 1) as p}
					<button
						on:click={() => { page = p; loadUsers(); }}
						class="px-3 py-1 rounded-lg text-sm font-medium transition-colors
						{p === page
							? 'bg-brand-600 text-white'
							: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
					>
						{p}
					</button>
				{/each}
			</div>
		</div>
	{/if}
{/if}

<!-- Create user modal -->
{#if showCreate}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<button class="absolute inset-0 bg-black/50" on:click={() => (showCreate = false)} aria-label="Close" />
		<div class="relative w-full max-w-md card p-6 space-y-4">
			<div class="flex items-center justify-between">
				<h3 class="text-lg font-semibold text-[var(--text-primary)]">{$t('admin.createUser')}</h3>
				<button on:click={() => (showCreate = false)} class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
					<X size={20} />
				</button>
			</div>

			{#if createError}
				<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{createError}</div>
			{/if}

			<form on:submit|preventDefault={handleCreate} class="space-y-3">
				<div class="grid grid-cols-2 gap-3">
					<div>
						<label for="c_first" class="label">{$t('auth.firstName')}</label>
						<input id="c_first" type="text" bind:value={createForm.first_name} class="input" required />
					</div>
					<div>
						<label for="c_last" class="label">{$t('auth.lastName')}</label>
						<input id="c_last" type="text" bind:value={createForm.last_name} class="input" required />
					</div>
				</div>
				<div>
					<label for="c_email" class="label">{$t('auth.email')}</label>
					<input id="c_email" type="email" bind:value={createForm.email} class="input" required />
				</div>
				<div>
					<label for="c_pass" class="label">{$t('auth.password')}</label>
					<input id="c_pass" type="password" bind:value={createForm.password} class="input" required minlength="8" />
				</div>
				<div>
					<label for="c_role" class="label">{$t('admin.role')}</label>
					<select id="c_role" bind:value={createForm.role} class="input">
						<option value="patient">{$t('roles.patient')}</option>
						<option value="professional">{$t('roles.professional')}</option>
						<option value="devadmin">{$t('roles.devadmin')}</option>
					</select>
				</div>
				<div class="flex gap-3 pt-2">
					<button type="button" on:click={() => (showCreate = false)} class="btn-secondary flex-1">{$t('common.cancel')}</button>
					<button type="submit" class="btn-primary flex-1" disabled={creating}>
						{creating ? $t('common.loading') : $t('admin.createUser')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}
