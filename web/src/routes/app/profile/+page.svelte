<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { api, ApiError } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDate } from '$lib/utils';
	import { User, Scale, Stethoscope, Mail, Phone, Camera } from 'lucide-svelte';
	import { photoUrl } from '$lib/api/client';

	let firstName = $authStore.user?.first_name || '';
	let avatarUrl = $authStore.user?.profile?.avatar_url || '';
	let avatarInput: HTMLInputElement;
	let uploadingAvatar = false;
	let lastName = $authStore.user?.last_name || '';
	let bio = $authStore.user?.profile?.bio || '';
	let phone = $authStore.user?.profile?.phone || '';
	let dateOfBirth = $authStore.user?.profile?.date_of_birth || '';
	let gender = $authStore.user?.gender || '';
	let heightCm = $authStore.user?.profile?.height_cm?.toString() || '';

	let weightStats: {
		initial_weight_kg: number | null;
		initial_weight_date: string | null;
		current_weight_kg: number | null;
		current_weight_date: string | null;
	} = $authStore.user?.weight_stats || { initial_weight_kg: null, initial_weight_date: null, current_weight_kg: null, current_weight_date: null };

	let myProfessional: { first_name: string; last_name: string; email: string; phone?: string; bio?: string } | null =
		$authStore.user?.my_professional || null;

	let loading = false;
	let error = '';
	let success = false;

	async function loadProfile() {
		try {
			const res = await api.get('/auth/me');
			authStore.updateUser(res.user);
			avatarUrl = res.user.profile?.avatar_url || '';
			gender = res.user.gender || '';
			weightStats = res.user.weight_stats || weightStats;
			myProfessional = res.user.my_professional || null;
		} catch (err) {
			console.error('Profile load error:', err);
		}
	}

	async function handleAvatarUpload() {
		const file = avatarInput?.files?.[0];
		if (!file) return;
		uploadingAvatar = true;
		try {
			const res = await api.upload('/auth/me/avatar', file);
			authStore.updateUser(res.user);
			avatarUrl = res.user.profile?.avatar_url || '';
		} catch (err) {
			console.error('Avatar upload error:', err);
		} finally {
			uploadingAvatar = false;
		}
	}

	onMount(loadProfile);

	async function saveProfile() {
		loading = true;
		error = '';
		success = false;
		try {
			const res = await api.patch('/auth/me', {
				first_name: firstName,
				last_name: lastName,
				gender: gender || null,
				bio: bio || null,
				phone: phone || null,
				date_of_birth: dateOfBirth || null,
				height_cm: heightCm ? parseFloat(heightCm) : null
			});
			authStore.updateUser(res.user);
			success = true;
			setTimeout(() => (success = false), 3000);
		} catch (err) {
			error = err instanceof ApiError ? err.message : 'Failed to save';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>{$t('profile.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="mx-auto max-w-lg space-y-6">
	<h1 class="text-2xl font-bold text-[var(--text-primary)]">{$t('profile.title')}</h1>

	<!-- Avatar -->
	<div class="flex items-center gap-4">
		<button
			on:click={() => avatarInput.click()}
			class="relative group h-20 w-20 rounded-full overflow-hidden shrink-0"
			disabled={uploadingAvatar}
		>
			{#if avatarUrl}
				<img src={photoUrl(avatarUrl)} alt="Avatar" class="h-full w-full object-cover" />
			{:else}
				<div class="flex h-full w-full items-center justify-center bg-brand-100 dark:bg-brand-900">
					<User size={36} class="text-brand-600 dark:text-brand-400" />
				</div>
			{/if}
			<div class="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity">
				{#if uploadingAvatar}
					<div class="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
				{:else}
					<Camera size={20} class="text-white" />
				{/if}
			</div>
		</button>
		<input
			bind:this={avatarInput}
			type="file"
			accept="image/*"
			class="hidden"
			on:change={handleAvatarUpload}
		/>
		<div>
			<p class="text-lg font-semibold text-[var(--text-primary)]">{firstName} {lastName}</p>
			<p class="text-sm text-[var(--text-secondary)]">{$authStore.user?.email}</p>
			<span class="mt-1 inline-block rounded-full bg-brand-50 dark:bg-brand-950 px-2.5 py-0.5 text-xs font-medium text-brand-700 dark:text-brand-300">
				{$t(`roles.${$authStore.user?.role}`)}
			</span>
		</div>
	</div>

	<!-- Weight stats -->
	{#if weightStats.initial_weight_kg || weightStats.current_weight_kg}
		<div class="grid grid-cols-2 gap-3">
			<div class="card flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-950 shrink-0">
					<Scale size={20} class="text-brand-500" />
				</div>
				<div class="min-w-0">
					<p class="text-xs text-[var(--text-secondary)]">{$t('profile.initialWeight')}</p>
					{#if weightStats.initial_weight_kg}
						<p class="text-lg font-bold text-[var(--text-primary)]">{weightStats.initial_weight_kg} kg</p>
						<p class="text-[0.65rem] text-[var(--text-secondary)] truncate">{formatDate(weightStats.initial_weight_date || '')}</p>
					{:else}
						<p class="text-sm text-[var(--text-secondary)]">—</p>
					{/if}
				</div>
			</div>
			<div class="card flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-green-50 dark:bg-green-950 shrink-0">
					<Scale size={20} class="text-green-500" />
				</div>
				<div class="min-w-0">
					<p class="text-xs text-[var(--text-secondary)]">{$t('profile.currentWeight')}</p>
					{#if weightStats.current_weight_kg}
						<p class="text-lg font-bold text-[var(--text-primary)]">{weightStats.current_weight_kg} kg</p>
						<p class="text-[0.65rem] text-[var(--text-secondary)] truncate">{formatDate(weightStats.current_weight_date || '')}</p>
					{:else}
						<p class="text-sm text-[var(--text-secondary)]">—</p>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<!-- My professional -->
	{#if myProfessional}
		<div class="card space-y-3">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-50 dark:bg-purple-950 shrink-0">
					<Stethoscope size={20} class="text-purple-500" />
				</div>
				<div>
					<p class="text-xs text-[var(--text-secondary)]">{$t('profile.myProfessional')}</p>
					<p class="font-semibold text-[var(--text-primary)]">{myProfessional.first_name} {myProfessional.last_name}</p>
				</div>
			</div>
			<div class="space-y-1.5 pl-[52px]">
				<div class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
					<Mail size={14} class="shrink-0" />
					<span class="truncate">{myProfessional.email}</span>
				</div>
				{#if myProfessional.phone}
					<div class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
						<Phone size={14} class="shrink-0" />
						<span>{myProfessional.phone}</span>
					</div>
				{/if}
				{#if myProfessional.bio}
					<p class="text-sm text-[var(--text-secondary)] italic">{myProfessional.bio}</p>
				{/if}
			</div>
		</div>
	{/if}

	<form on:submit|preventDefault={saveProfile} class="card space-y-4">
		{#if error}
			<div class="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-sm text-red-600 dark:text-red-400">{error}</div>
		{/if}
		{#if success}
			<div class="rounded-lg bg-green-50 dark:bg-green-950 p-3 text-sm text-green-600 dark:text-green-400">{$t('common.success')}</div>
		{/if}

		<div class="grid grid-cols-2 gap-3">
			<div>
				<label for="firstName" class="label">{$t('auth.firstName')}</label>
				<input id="firstName" type="text" bind:value={firstName} class="input" required />
			</div>
			<div>
				<label for="lastName" class="label">{$t('auth.lastName')}</label>
				<input id="lastName" type="text" bind:value={lastName} class="input" required />
			</div>
		</div>

		<div>
			<label for="gender" class="label">{$t('profile.gender')}</label>
			<select id="gender" bind:value={gender} class="input">
				<option value="">{$t('profile.genderPlaceholder')}</option>
				<option value="male">{$t('profile.genderMale')}</option>
				<option value="female">{$t('profile.genderFemale')}</option>
				<option value="other">{$t('profile.genderOther')}</option>
			</select>
		</div>

		<div>
			<label for="bio" class="label">{$t('profile.bio')}</label>
			<textarea id="bio" bind:value={bio} class="input" rows="3"></textarea>
		</div>

		<div class="grid grid-cols-2 gap-3">
			<div>
				<label for="phone" class="label">{$t('profile.phone')}</label>
				<input id="phone" type="tel" bind:value={phone} class="input" />
			</div>
			<div>
				<label for="dob" class="label">{$t('profile.dateOfBirth')}</label>
				<input id="dob" type="date" bind:value={dateOfBirth} class="input" />
			</div>
		</div>

		<div>
			<label for="height" class="label">{$t('profile.height')}</label>
			<input id="height" type="number" step="0.1" bind:value={heightCm} class="input" />
		</div>

		<button type="submit" class="btn-primary w-full" disabled={loading}>
			{loading ? $t('common.loading') : $t('common.save')}
		</button>
	</form>
</div>
