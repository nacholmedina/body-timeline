<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { t, locale } from '$i18n/index';
	import { api, photoUrl } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime, formatDate } from '$lib/utils';
	import {
		ArrowLeft, TrendingUp, UtensilsCrossed, Dumbbell, Calendar,
		MessageSquare, X, Send, ChevronLeft, ChevronRight, AlertCircle, ChevronDown
	} from 'lucide-svelte';
	import {
		Chart as ChartJS,
		CategoryScale,
		LinearScale,
		PointElement,
		LineElement,
		Tooltip,
		Legend
	} from 'chart.js';
	import { Line } from 'svelte-chartjs';

	ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

	const patientId = $page.params.id;

	let patient: any = null;
	let weightData: any[] = [];
	let meals: any[] = [];
	let workouts: any[] = [];
	let loading = true;
	let tab: 'overview' | 'timeline' = 'overview';
	let timelineFilter: 'all' | 'day' | 'week' | 'month' | 'year' = 'all';

	// Comment modal state
	let showCommentModal = false;
	let selectedMeal: any = null;
	let commentText = '';
	let sendingComment = false;
	let commentError = '';

	// Lightbox state
	let lightboxPhoto: string | null = null;
	let lightboxPhotos: string[] = [];
	let lightboxIndex = 0;

	// Collapsible card state
	let expandedMealIds = new Set<string>();
	let expandedWorkoutIds = new Set<string>();

	function toggleMealExpanded(mealId: string) {
		if (expandedMealIds.has(mealId)) {
			expandedMealIds.delete(mealId);
		} else {
			expandedMealIds.add(mealId);
		}
		expandedMealIds = expandedMealIds; // Trigger reactivity
	}

	function toggleWorkoutExpanded(workoutId: string) {
		if (expandedWorkoutIds.has(workoutId)) {
			expandedWorkoutIds.delete(workoutId);
		} else {
			expandedWorkoutIds.add(workoutId);
		}
		expandedWorkoutIds = expandedWorkoutIds; // Trigger reactivity
	}

	$: isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');

	$: weightChartData = {
		labels: weightData.map((p) => formatDate(p.date, $locale)),
		datasets: [
			{
				label: $t('dashboard.weightOverTime'),
				data: weightData.map((p) => p.weight_kg),
				borderColor: '#6366f1',
				backgroundColor: 'rgba(99, 102, 241, 0.1)',
				fill: true,
				tension: 0.3,
				pointRadius: 4,
				pointBackgroundColor: '#6366f1',
				pointBorderColor: '#fff',
				pointBorderWidth: 2
			}
		]
	};

	$: weightChartOptions = {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: { display: false },
			tooltip: {
				callbacks: {
					label: (ctx: any) => `${ctx.parsed.y} kg`
				}
			}
		},
		scales: {
			x: {
				ticks: { color: isDark ? '#9ca3af' : '#6b7280', maxRotation: 45, font: { size: 10 }, maxTicksLimit: 5, autoSkip: true },
				grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }
			},
			y: {
				ticks: {
					color: isDark ? '#9ca3af' : '#6b7280',
					callback: (v: any) => `${v} kg`,
					maxTicksLimit: 7
				},
				grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }
			}
		}
	};

	function getTimelineFilterParams(): Record<string, string> {
		const now = new Date();
		const params: Record<string, string> = {};

		if (timelineFilter === 'day') {
			params.from = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
		} else if (timelineFilter === 'week') {
			const weekAgo = new Date(now.getTime() - 7 * 86400000);
			params.from = weekAgo.toISOString();
		} else if (timelineFilter === 'month') {
			params.from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
		} else if (timelineFilter === 'year') {
			params.from = new Date(now.getFullYear(), 0, 1).toISOString();
		}

		return params;
	}

	let mounted = false;
	onMount(async () => {
		await loadData();
		mounted = true;
	});

	// Reload data when timeline filter changes
	$: if (mounted && tab === 'timeline' && timelineFilter) {
		loadData();
	}

	async function loadData() {
		try {
			loading = true;
			const filterParams = tab === 'timeline' ? getTimelineFilterParams() : {};

			const [patientRes, weightRes, mealsRes, workoutsRes] = await Promise.all([
				api.get(`/professional/patients/${patientId}`),
				api.get('/dashboard/weight-series', { patient_id: patientId, days: '365' }),
				api.get('/meals', { patient_id: patientId, limit: '100', ...filterParams }),
				api.get('/workouts', { patient_id: patientId, limit: '100', ...filterParams })
			]);

			patient = patientRes;
			weightData = weightRes.data || [];
			meals = mealsRes.data || [];
			workouts = workoutsRes.data || [];
		} catch (err: any) {
			console.error('Failed to load patient data:', err);
		} finally {
			loading = false;
		}
	}

	async function openCommentModal(meal: any) {
		selectedMeal = meal;
		commentText = '';
		commentError = '';
		showCommentModal = true;

		// Load existing comments
		try {
			const res = await api.get(`/meal-comments/${meal.id}/comments`);
			selectedMeal.comments = res.data || [];
		} catch (err) {
			console.error('Failed to load comments:', err);
		}
	}

	async function sendComment() {
		if (!commentText.trim()) {
			commentError = 'Comment is required';
			return;
		}

		try {
			sendingComment = true;
			commentError = '';
			await api.post(`/meal-comments/${selectedMeal.id}/comments`, {
				comment: commentText
			});
			commentText = '';

			// Reload comments
			const res = await api.get(`/meal-comments/${selectedMeal.id}/comments`);
			selectedMeal.comments = res.data || [];

			// Update meal in list
			const mealIndex = meals.findIndex(m => m.id === selectedMeal.id);
			if (mealIndex !== -1) {
				meals[mealIndex].comments = res.data || [];
			}
		} catch (err: any) {
			commentError = err.message || 'Failed to send comment';
		} finally {
			sendingComment = false;
		}
	}

	function openLightbox(photos: any[], index: number) {
		lightboxPhotos = photos.map((p: any) => photoUrl(p.url));
		lightboxIndex = index;
		lightboxPhoto = lightboxPhotos[index];
	}

	function closeLightbox() {
		lightboxPhoto = null;
		lightboxPhotos = [];
	}

	function prevPhoto() {
		lightboxIndex = (lightboxIndex - 1 + lightboxPhotos.length) % lightboxPhotos.length;
		lightboxPhoto = lightboxPhotos[lightboxIndex];
	}

	function nextPhoto() {
		lightboxIndex = (lightboxIndex + 1) % lightboxPhotos.length;
		lightboxPhoto = lightboxPhotos[lightboxIndex];
	}
</script>

<svelte:head>
	<title>{patient?.first_name} {patient?.last_name} - {BRANDING.appName}</title>
</svelte:head>

<svelte:window
	on:keydown={(e) => {
		if (lightboxPhoto) {
			if (e.key === 'Escape') closeLightbox();
			if (e.key === 'ArrowLeft') prevPhoto();
			if (e.key === 'ArrowRight') nextPhoto();
		}
	}}
/>

<div class="space-y-6">
	<!-- Back Button -->
	<button
		on:click={() => goto('/app/professional')}
		class="flex items-center gap-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
	>
		<ArrowLeft size={16} />
		{$t('common.back')}
	</button>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if patient}
		<!-- Patient Header -->
		<div class="card p-6">
			<div class="flex items-start justify-between">
				<div class="flex items-center gap-4">
					<div class="flex h-16 w-16 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900">
						<span class="text-2xl font-bold text-brand-600 dark:text-brand-400">
							{patient.first_name?.[0]}{patient.last_name?.[0]}
						</span>
					</div>
					<div>
						<h1 class="text-2xl font-bold text-[var(--text-primary)]">
							{patient.first_name} {patient.last_name}
						</h1>
						<p class="text-sm text-[var(--text-secondary)]">{patient.email}</p>
						{#if patient.phone}
							<p class="text-sm text-[var(--text-secondary)]">{patient.phone}</p>
						{/if}
					</div>
				</div>
			</div>
		</div>

		<!-- Tabs -->
		<div class="flex gap-2 border-b border-[var(--border-color)]">
			<button
				on:click={() => (tab = 'overview')}
				class="px-4 py-2 text-sm font-medium transition-colors border-b-2 {tab === 'overview'
					? 'border-brand-600 text-brand-600'
					: 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}"
			>
				{$t('professional.overview')}
			</button>
			<button
				on:click={() => (tab = 'timeline')}
				class="px-4 py-2 text-sm font-medium transition-colors border-b-2 {tab === 'timeline'
					? 'border-brand-600 text-brand-600'
					: 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}"
			>
				{$t('professional.timeline')}
			</button>
		</div>

		{#if tab === 'overview'}
			<!-- Overview Tab -->
			<div class="grid gap-6 lg:grid-cols-2">
				<!-- Weight Chart -->
				<div class="card">
					<div class="mb-4 flex items-center gap-2">
						<TrendingUp size={18} class="text-brand-600" />
						<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.weightOverTime')}</h3>
					</div>
					{#if weightData.length > 0}
						<div class="h-56">
							<Line data={weightChartData} options={weightChartOptions} />
						</div>
					{:else}
						<p class="text-sm text-[var(--text-secondary)]">{$t('common.noData')}</p>
					{/if}
				</div>

				<!-- Stats Summary -->
				<div class="card">
					<h3 class="mb-4 font-semibold text-[var(--text-primary)]">Summary</h3>
					<div class="space-y-4">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2">
								<TrendingUp size={18} class="text-green-600" />
								<span class="text-sm text-[var(--text-secondary)]">{$t('professional.latestWeight')}</span>
							</div>
							<span class="text-lg font-bold text-[var(--text-primary)]">
								{weightData.length > 0 ? `${weightData[weightData.length - 1].weight_kg} kg` : '-'}
							</span>
						</div>
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2">
								<UtensilsCrossed size={18} class="text-orange-600" />
								<span class="text-sm text-[var(--text-secondary)]">{$t('professional.totalMeals')}</span>
							</div>
							<span class="text-lg font-bold text-[var(--text-primary)]">{meals.length}</span>
						</div>
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2">
								<Dumbbell size={18} class="text-blue-600" />
								<span class="text-sm text-[var(--text-secondary)]">{$t('professional.totalWorkouts')}</span>
							</div>
							<span class="text-lg font-bold text-[var(--text-primary)]">{workouts.length}</span>
						</div>
					</div>
				</div>
			</div>
		{:else if tab === 'timeline'}
			<!-- Timeline Tab -->
			<!-- Date Range Filter -->
			<div class="card p-4">
				<div class="flex gap-2 overflow-x-auto">
					{#each ['all', 'day', 'week', 'month', 'year'] as f}
						<button
							on:click={() => (timelineFilter = f)}
							class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors {timelineFilter === f
								? 'bg-brand-600 text-white'
								: 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]'}"
						>
							{$t(`common.${f}`)}
						</button>
					{/each}
				</div>
			</div>

			<div class="space-y-4">
				<!-- Recent Meals -->
				<div class="card">
					<div class="mb-4 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<UtensilsCrossed size={18} class="text-brand-600" />
							<h3 class="font-semibold text-[var(--text-primary)]">{$t('nav.meals')}</h3>
						</div>
					</div>
					{#if meals.length > 0}
						<div class="space-y-4">
							{#each meals as meal}
								<div class="rounded-lg border border-[var(--border-color)] p-4">
									<div class="flex items-start gap-3 mb-2">
										<button
											on:click={() => toggleMealExpanded(meal.id)}
											class="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-transform {expandedMealIds.has(meal.id) ? 'rotate-180' : ''}"
										>
											<ChevronDown size={18} />
										</button>
										<div class="flex-1">
											<p class="font-medium text-[var(--text-primary)]">{meal.description}</p>
											<p class="text-sm text-[var(--text-secondary)]">
												{formatDateTime(meal.eaten_at, $locale)}
											</p>
										</div>
										<button
											on:click={() => openCommentModal(meal)}
											class="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700"
										>
											<MessageSquare size={16} />
											{meal.comments?.length || 0}
										</button>
									</div>

									{#if expandedMealIds.has(meal.id)}
										{#if meal.notes}
										<p class="text-sm text-[var(--text-secondary)] mt-2">{meal.notes}</p>
									{/if}

									{#if meal.photos && meal.photos.length > 0}
										<div class="flex gap-2 mt-3">
											{#each meal.photos as photo, i}
												<button
													on:click={() => openLightbox(meal.photos, i)}
													class="relative h-20 w-20 overflow-hidden rounded-lg"
												>
													<img
														src={photoUrl(photo.url)}
														alt={photo.caption || 'Meal photo'}
														class="h-full w-full object-cover hover:opacity-90 transition-opacity"
													/>
												</button>
											{/each}
										</div>
									{/if}

									{#if meal.comments && meal.comments.length > 0}
										<div class="mt-3 space-y-2 border-t border-[var(--border-color)] pt-3">
											{#each meal.comments as comment}
												<div class="rounded bg-[var(--bg-secondary)] p-2">
													<div class="flex items-center justify-between mb-1">
														<span class="text-xs font-medium text-brand-600">{comment.professional_name}</span>
														<span class="text-xs text-[var(--text-secondary)]">
															{formatDate(comment.created_at, $locale)}
														</span>
													</div>
													<p class="text-sm text-[var(--text-primary)]">{comment.comment}</p>
												</div>
											{/each}
										</div>
									{/if}
									{/if}
								</div>
							{/each}
						</div>
					{:else}
						<p class="text-sm text-[var(--text-secondary)]">{$t('meals.noMeals')}</p>
					{/if}
				</div>

				<!-- Recent Workouts -->
				<div class="card">
					<div class="mb-4 flex items-center gap-2">
						<Dumbbell size={18} class="text-brand-600" />
						<h3 class="font-semibold text-[var(--text-primary)]">{$t('nav.workouts')}</h3>
					</div>
					{#if workouts.length > 0}
						<div class="space-y-3">
							{#each workouts as workout}
								<div class="rounded-lg border border-[var(--border-color)] p-3">
									<div class="flex items-center gap-3">
										<button
											on:click={() => toggleWorkoutExpanded(workout.id)}
											class="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-transform {expandedWorkoutIds.has(workout.id) ? 'rotate-180' : ''}"
										>
											<ChevronDown size={18} />
										</button>
										<div class="flex-1">
											<p class="font-medium text-[var(--text-primary)]">
												{workout.exercises?.length || 0} {$t('workouts.exercises').toLowerCase()}
											</p>
											<p class="text-sm text-[var(--text-secondary)]">
												{formatDateTime(workout.start_time, $locale)}
											</p>
										</div>
									</div>

									{#if expandedWorkoutIds.has(workout.id) && workout.notes}
										<p class="text-sm text-[var(--text-secondary)] mt-2">{workout.notes}</p>
									{/if}
								</div>
							{/each}
						</div>
					{:else}
						<p class="text-sm text-[var(--text-secondary)]">{$t('workouts.noWorkouts')}</p>
					{/if}
				</div>
			</div>
		{/if}
	{:else}
		<div class="card p-12 text-center">
			<AlertCircle size={48} class="mx-auto mb-4 text-red-500" />
			<p class="text-lg font-medium text-[var(--text-primary)]">Patient not found</p>
		</div>
	{/if}
</div>

<!-- Comment Modal -->
{#if showCommentModal && selectedMeal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
		<div class="w-full max-w-lg rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl max-h-[90vh] overflow-y-auto">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-xl font-bold text-[var(--text-primary)]">{$t('professional.comments')}</h2>
				<button
					on:click={() => (showCommentModal = false)}
					class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
				>
					<X size={20} />
				</button>
			</div>

			<!-- Meal Info -->
			<div class="mb-4 rounded-lg bg-[var(--bg-secondary)] p-3">
				<p class="font-medium text-[var(--text-primary)]">{selectedMeal.description}</p>
				<p class="text-sm text-[var(--text-secondary)]">{formatDateTime(selectedMeal.eaten_at, $locale)}</p>
			</div>

			<!-- Existing Comments -->
			{#if selectedMeal.comments && selectedMeal.comments.length > 0}
				<div class="mb-4 space-y-2 max-h-60 overflow-y-auto">
					<h3 class="text-sm font-medium text-[var(--text-secondary)]">{$t('professional.comments')}</h3>
					{#each selectedMeal.comments as comment}
						<div class="rounded-lg border border-[var(--border-color)] p-3">
							<div class="flex items-center justify-between mb-1">
								<span class="text-xs font-medium text-brand-600">{comment.professional_name}</span>
								<span class="text-xs text-[var(--text-secondary)]">
									{new Date(comment.created_at).toLocaleDateString()}
								</span>
							</div>
							<p class="text-sm text-[var(--text-primary)]">{comment.comment}</p>
						</div>
					{/each}
				</div>
			{/if}

			<!-- Add Comment -->
			<div class="space-y-3">
				<div>
					<label class="mb-1 block text-sm font-medium text-[var(--text-primary)]">
						{$t('professional.addComment')}
					</label>
					<textarea
						bind:value={commentText}
						class="input w-full"
						rows="3"
						placeholder={$t('professional.writeComment')}
					></textarea>
				</div>

				{#if commentError}
					<p class="text-sm text-red-600 dark:text-red-400">{commentError}</p>
				{/if}

				<div class="flex gap-3">
					<button
						on:click={() => (showCommentModal = false)}
						class="flex-1 rounded-lg border border-[var(--border-color)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
						disabled={sendingComment}
					>
						{$t('common.cancel')}
					</button>
					<button
						on:click={sendComment}
						class="flex-1 flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
						disabled={sendingComment}
					>
						{#if sendingComment}
							<span class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
						{:else}
							<Send size={16} />
						{/if}
						{sendingComment ? 'Sending...' : $t('common.send')}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- Lightbox -->
{#if lightboxPhoto}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4" on:click={closeLightbox}>
		<button
			on:click={(e) => { e.stopPropagation(); closeLightbox(); }}
			class="absolute top-4 right-4 text-white hover:text-gray-300"
		>
			<X size={32} />
		</button>

		{#if lightboxPhotos.length > 1}
			<button
				on:click={(e) => { e.stopPropagation(); prevPhoto(); }}
				class="absolute left-4 text-white hover:text-gray-300"
			>
				<ChevronLeft size={48} />
			</button>
			<button
				on:click={(e) => { e.stopPropagation(); nextPhoto(); }}
				class="absolute right-4 text-white hover:text-gray-300"
			>
				<ChevronRight size={48} />
			</button>
		{/if}

		<img
			src={lightboxPhoto}
			alt="Meal photo"
			class="max-h-full max-w-full object-contain"
			on:click={(e) => e.stopPropagation()}
		/>
	</div>
{/if}

<style>
	.input {
		@apply rounded-lg border border-[var(--border-color)] bg-white dark:bg-gray-900 px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500;
	}
</style>
