<script lang="ts">
	import { onMount } from 'svelte';
	import { t, locale } from '$i18n/index';
	import { authStore } from '$stores/auth';
	import { api } from '$lib/api/client';
	import { BRANDING } from '$lib/config/branding';
	import { formatDateTime, formatDate, formatWeight, displayWeight, weightUnit } from '$lib/utils';
	import { unitStore } from '$stores/units';
	import {
		UtensilsCrossed, Dumbbell, Target, Calendar,
		Bell, TrendingUp, Newspaper, BarChart3, List,
		Users, Clock, Mail, ArrowRight
	} from 'lucide-svelte';
	import {
		Chart as ChartJS,
		CategoryScale,
		LinearScale,
		PointElement,
		LineElement,
		BarElement,
		Filler,
		Tooltip,
		Legend
	} from 'chart.js';
	import { Line, Bar } from 'svelte-chartjs';

	ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler, Tooltip, Legend);

	const isPatient = $authStore.user?.role === 'patient';

	// Patient dashboard state
	let summary: any = null;
	let weightData: any[] = [];
	let activityData: any[] = [];
	let notifications: any[] = [];
	let loading = true;

	let weightView: 'chart' | 'list' = 'chart';
	let activityView: 'chart' | 'list' = 'chart';

	// Professional dashboard state
	let proSummary: any = null;

	$: news = [
		{ title: $t('dashboard.newsHydration'), body: $t('dashboard.newsHydrationBody') },
		{ title: $t('dashboard.newsRest'), body: $t('dashboard.newsRestBody') },
		{ title: $t('dashboard.newsMealPrep'), body: $t('dashboard.newsMealPrepBody') },
	];

	function detectType(title: string): string | null {
		if (title === 'meal_comment') return 'meal_comment';
		if (title === 'professional_invitation') return 'professional_invitation';
		if (title === 'assignment_removed') return 'assignment_removed';
		if (title === 'goal_created') return 'goal_created';
		return null;
	}

	$: displayNotifications = notifications.map(notif => {
		const type = detectType(notif.title);
		const name = notif.author_name || '';
		let displayTitle = notif.title;
		let displayBody = notif.body;

		if (type === 'meal_comment') {
			displayTitle = $t('notifications.mealCommentTitle').replace('{name}', name);
			const preview = notif.body?.replace(/^Your professional has commented on your meal:\s*/, '') || '';
			displayBody = $t('notifications.mealCommentBody').replace('{name}', name).replace('{preview}', preview);
		} else if (type === 'professional_invitation') {
			displayTitle = $t('notifications.professionalInvitationTitle').replace('{name}', name);
			displayBody = $t('notifications.professionalInvitationBody').replace('{name}', name);
		} else if (type === 'assignment_removed') {
			displayTitle = $t('notifications.assignmentRemovedTitle');
			displayBody = $t('notifications.assignmentRemovedBody').replace('{name}', name);
		} else if (type === 'goal_created') {
			displayTitle = $t('notifications.goalCreatedTitle').replace('{name}', name);
			displayBody = $t('notifications.goalCreatedBody').replace('{name}', name).replace('{goal}', notif.body || '');
		}

		return { ...notif, displayTitle, displayBody };
	});

	$: welcomeKey = $authStore.user?.gender === 'male' ? 'dashboard.welcomeMale'
		: $authStore.user?.gender === 'female' ? 'dashboard.welcomeFemale'
		: $authStore.user?.gender === 'other' ? 'dashboard.welcomeOther'
		: 'dashboard.welcome';

	$: isDark = typeof document !== 'undefined' && document.documentElement.classList.contains('dark');

	$: weightChartData = {
		labels: weightData.map((p) => formatDate(p.date, $locale)),
		datasets: [
			{
				label: $t('dashboard.weightOverTime'),
				data: weightData.map((p) => displayWeight(p.weight_kg, $unitStore)),
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
					label: (ctx: any) => `${ctx.parsed.y} ${weightUnit($unitStore)}`
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
					callback: (v: any) => `${v} ${weightUnit($unitStore)}`,
					maxTicksLimit: 7
				},
				grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }
			}
		}
	};

	$: activityChartData = {
		labels: activityData.map((w) => w.week),
		datasets: [
			{
				label: $t('dashboard.weeklyActivity'),
				data: activityData.map((w) => w.count),
				backgroundColor: 'rgba(99, 102, 241, 0.7)',
				borderColor: '#6366f1',
				borderWidth: 1,
				borderRadius: 6
			}
		]
	};

	$: activityChartOptions = {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: { display: false }
		},
		scales: {
			x: {
				ticks: { color: isDark ? '#9ca3af' : '#6b7280', maxRotation: 45, font: { size: 10 } },
				grid: { display: false }
			},
			y: {
				beginAtZero: true,
				ticks: {
					color: isDark ? '#9ca3af' : '#6b7280',
					stepSize: 1
				},
				grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)' }
			}
		}
	};

	onMount(async () => {
		try {
			const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
			if (isPatient) {
				const params = { patient_id: $authStore.user!.id, tz };
				const [summaryRes, weightRes, activityRes, notifsRes] = await Promise.all([
					api.get('/dashboard/summary', params),
					api.get('/dashboard/weight-series', { ...params, days: '365' }),
					api.get('/dashboard/activity-series', { ...params, weeks: '12' }),
					api.get('/notifications', { limit: '5' }).catch(() => ({ data: [] })),
				]);
				summary = summaryRes;
				weightData = weightRes.data;
				activityData = activityRes.data;
				notifications = notifsRes.data;
			} else {
				const res = await api.get('/dashboard/professional-summary', { tz });
				proSummary = res;
			}
		} catch (err) {
			console.error('Dashboard load error:', err);
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>{$t('dashboard.title')} - {BRANDING.appName}</title>
</svelte:head>

<div class="space-y-6">
	<!-- Welcome -->
	<div>
		<h1 class="text-2xl font-bold text-[var(--text-primary)]">
			{$t(welcomeKey)}, {$authStore.user?.first_name}!
		</h1>
		<p class="text-sm text-[var(--text-secondary)]">
			{isPatient ? $t('app.description') : $t('dashboard.proDescription')}
		</p>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
		</div>
	{:else if isPatient}
		<!-- ============ PATIENT DASHBOARD ============ -->
		<!-- Summary Cards -->
		<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
			<div class="card flex items-center gap-3">
				<div class="rounded-lg bg-orange-100 dark:bg-orange-900 p-2.5">
					<UtensilsCrossed size={20} class="text-orange-600 dark:text-orange-400" />
				</div>
				<div>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{summary?.meals_this_month ?? 0}</p>
					<p class="text-xs text-[var(--text-secondary)]">{$t('dashboard.mealsThisMonth')}</p>
				</div>
			</div>

			<div class="card flex items-center gap-3">
				<div class="rounded-lg bg-blue-100 dark:bg-blue-900 p-2.5">
					<Dumbbell size={20} class="text-blue-600 dark:text-blue-400" />
				</div>
				<div>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{summary?.workouts_this_month ?? 0}</p>
					<p class="text-xs text-[var(--text-secondary)]">{$t('dashboard.workoutsThisMonth')}</p>
				</div>
			</div>

			<div class="card flex items-center gap-3">
				<div class="rounded-lg bg-green-100 dark:bg-green-900 p-2.5">
					<Target size={20} class="text-green-600 dark:text-green-400" />
				</div>
				<div>
					<p class="text-2xl font-bold text-[var(--text-primary)]">
						{summary?.goals_completed ?? 0}/{summary?.goals_total ?? 0}
					</p>
					<p class="text-xs text-[var(--text-secondary)]">{$t('dashboard.goalsCompleted')}</p>
				</div>
			</div>

			<div class="card flex items-center gap-3">
				<div class="rounded-lg bg-purple-100 dark:bg-purple-900 p-2.5">
					<Bell size={20} class="text-purple-600 dark:text-purple-400" />
				</div>
				<div>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{summary?.unread_notifications ?? 0}</p>
					<p class="text-xs text-[var(--text-secondary)]">{$t('nav.notifications')}</p>
				</div>
			</div>
		</div>

		<div class="grid gap-6 lg:grid-cols-2">
			<!-- Weight Chart -->
			<div class="card">
				<div class="mb-4 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<TrendingUp size={18} class="text-brand-600" />
						<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.weightOverTime')}</h3>
					</div>
					{#if weightData.length > 0}
						<div class="flex rounded-lg border border-[var(--border-color)] overflow-hidden">
							<button
								on:click={() => (weightView = 'chart')}
								class="p-1.5 transition-colors {weightView === 'chart'
									? 'bg-brand-600 text-white'
									: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
							>
								<BarChart3 size={14} />
							</button>
							<button
								on:click={() => (weightView = 'list')}
								class="p-1.5 transition-colors {weightView === 'list'
									? 'bg-brand-600 text-white'
									: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
							>
								<List size={14} />
							</button>
						</div>
					{/if}
				</div>
				{#if weightData.length > 0}
					{#if weightView === 'chart'}
						<div class="h-56">
							<Line data={weightChartData} options={weightChartOptions} />
						</div>
					{:else}
						<div class="space-y-2 max-h-56 overflow-y-auto">
							{#each [...weightData].reverse().slice(0, 10) as point}
								<div class="flex items-center justify-between text-sm">
									<span class="text-[var(--text-secondary)]">{formatDate(point.date, $locale)}</span>
									<span class="font-medium text-[var(--text-primary)]">{formatWeight(point.weight_kg, $unitStore)}</span>
								</div>
							{/each}
						</div>
					{/if}
				{:else}
					<p class="text-sm text-[var(--text-secondary)]">{$t('common.noData')}</p>
				{/if}
			</div>

			<!-- Activity Chart -->
			<div class="card">
				<div class="mb-4 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<Dumbbell size={18} class="text-brand-600" />
						<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.weeklyActivity')}</h3>
					</div>
					{#if activityData.length > 0}
						<div class="flex rounded-lg border border-[var(--border-color)] overflow-hidden">
							<button
								on:click={() => (activityView = 'chart')}
								class="p-1.5 transition-colors {activityView === 'chart'
									? 'bg-brand-600 text-white'
									: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
							>
								<BarChart3 size={14} />
							</button>
							<button
								on:click={() => (activityView = 'list')}
								class="p-1.5 transition-colors {activityView === 'list'
									? 'bg-brand-600 text-white'
									: 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'}"
							>
								<List size={14} />
							</button>
						</div>
					{/if}
				</div>
				{#if activityData.length > 0}
					{#if activityView === 'chart'}
						<div class="h-56">
							<Bar data={activityChartData} options={activityChartOptions} />
						</div>
					{:else}
						<div class="space-y-2 max-h-56 overflow-y-auto">
							{#each activityData as week}
								<div class="flex items-center gap-3">
									<span class="w-20 text-xs text-[var(--text-secondary)]">{week.week}</span>
									<div class="flex-1 h-5 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
										<div
											class="h-full bg-brand-500 rounded-full transition-all"
											style="width: {Math.min(100, week.count * 14)}%"
										></div>
									</div>
									<span class="text-sm font-medium text-[var(--text-primary)] w-8">{week.count}</span>
								</div>
							{/each}
						</div>
					{/if}
				{:else}
					<p class="text-sm text-[var(--text-secondary)]">{$t('common.noData')}</p>
				{/if}
			</div>

			<!-- Next Appointment -->
			<div class="card">
				<div class="mb-4 flex items-center gap-2">
					<Calendar size={18} class="text-brand-600" />
					<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.nextAppointment')}</h3>
				</div>
				{#if summary?.next_appointment}
					<div class="rounded-lg bg-brand-50 dark:bg-brand-950 p-4">
						<p class="font-medium text-[var(--text-primary)]">{summary.next_appointment.title}</p>
						<p class="text-sm text-[var(--text-secondary)]">
							{formatDateTime(summary.next_appointment.scheduled_at, $locale)}
						</p>
						{#if summary.next_appointment.professional_name}
							<p class="mt-1 text-sm text-brand-600 dark:text-brand-400">
								{summary.next_appointment.professional_name}
							</p>
						{/if}
					</div>
				{:else}
					<p class="text-sm text-[var(--text-secondary)]">{$t('dashboard.noAppointment')}</p>
				{/if}
			</div>

			<!-- Professional Notes -->
			<div class="card">
				<div class="mb-4 flex items-center gap-2">
					<Bell size={18} class="text-brand-600" />
					<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.professionalNotes')}</h3>
				</div>
				{#if displayNotifications.length > 0}
					<div class="space-y-3">
						{#each displayNotifications.slice(0, 3) as notif}
							<div class="rounded-lg border border-[var(--border-color)] p-3">
								<p class="text-sm font-medium text-[var(--text-primary)]">{notif.displayTitle}</p>
								<p class="mt-1 text-xs text-[var(--text-secondary)] line-clamp-2">{notif.displayBody}</p>
								<p class="mt-1 text-xs text-brand-500">{notif.author_name}</p>
							</div>
						{/each}
					</div>
				{:else}
					<p class="text-sm text-[var(--text-secondary)]">{$t('dashboard.noNotes')}</p>
				{/if}
			</div>
		</div>

		<!-- News Panel -->
		<div class="card">
			<div class="mb-4 flex items-center gap-2">
				<Newspaper size={18} class="text-brand-600" />
				<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.news')}</h3>
			</div>
			<div class="grid gap-4 sm:grid-cols-3">
				{#each news as item}
					<div class="rounded-lg bg-[var(--bg-secondary)] p-4">
						<h4 class="font-medium text-[var(--text-primary)]">{item.title}</h4>
						<p class="mt-1 text-sm text-[var(--text-secondary)]">{item.body}</p>
					</div>
				{/each}
			</div>
		</div>
	{:else}
		<!-- ============ PROFESSIONAL / ADMIN DASHBOARD ============ -->
		<!-- Summary Cards -->
		<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
			<div class="card flex items-center gap-3">
				<div class="rounded-lg bg-blue-100 dark:bg-blue-900 p-2.5">
					<Users size={20} class="text-blue-600 dark:text-blue-400" />
				</div>
				<div>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{proSummary?.patient_count ?? 0}</p>
					<p class="text-xs text-[var(--text-secondary)]">{$t('dashboard.patients')}</p>
				</div>
			</div>

			<div class="card flex items-center gap-3">
				<div class="rounded-lg bg-green-100 dark:bg-green-900 p-2.5">
					<Calendar size={20} class="text-green-600 dark:text-green-400" />
				</div>
				<div>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{proSummary?.todays_appointments?.length ?? 0}</p>
					<p class="text-xs text-[var(--text-secondary)]">{$t('dashboard.todaysAppointments')}</p>
				</div>
			</div>

			<div class="card flex items-center gap-3">
				<div class="rounded-lg bg-orange-100 dark:bg-orange-900 p-2.5">
					<Clock size={20} class="text-orange-600 dark:text-orange-400" />
				</div>
				<div>
					<p class="text-2xl font-bold text-[var(--text-primary)]">{proSummary?.upcoming_appointments_count ?? 0}</p>
					<p class="text-xs text-[var(--text-secondary)]">{$t('dashboard.upcomingThisWeek')}</p>
				</div>
			</div>

			{#if proSummary?.pending_invitations > 0}
				<div class="card flex items-center gap-3">
					<div class="rounded-lg bg-purple-100 dark:bg-purple-900 p-2.5">
						<Mail size={20} class="text-purple-600 dark:text-purple-400" />
					</div>
					<div>
						<p class="text-2xl font-bold text-[var(--text-primary)]">{proSummary.pending_invitations}</p>
						<p class="text-xs text-[var(--text-secondary)]">{$t('dashboard.pendingInvitations')}</p>
					</div>
				</div>
			{:else}
				<div class="card flex items-center gap-3">
					<div class="rounded-lg bg-purple-100 dark:bg-purple-900 p-2.5">
						<Bell size={20} class="text-purple-600 dark:text-purple-400" />
					</div>
					<div>
						<p class="text-2xl font-bold text-[var(--text-primary)]">{(proSummary?.recent_meals_7d ?? 0) + (proSummary?.recent_workouts_7d ?? 0)}</p>
						<p class="text-xs text-[var(--text-secondary)]">{$t('dashboard.recentActivity')}</p>
					</div>
				</div>
			{/if}
		</div>

		<div class="grid gap-6 lg:grid-cols-2">
			<!-- Today's Appointments -->
			<div class="card">
				<div class="mb-4 flex items-center gap-2">
					<Calendar size={18} class="text-brand-600" />
					<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.todaysAppointments')}</h3>
				</div>
				{#if proSummary?.todays_appointments?.length > 0}
					<div class="space-y-3">
						{#each proSummary.todays_appointments as appt}
							<div class="rounded-lg border border-[var(--border-color)] p-3">
								<div class="flex items-center justify-between">
									<p class="font-medium text-[var(--text-primary)]">{appt.title}</p>
									<span class="text-xs text-[var(--text-secondary)]">
										{new Date(appt.scheduled_at).toLocaleTimeString($locale === 'es' ? 'es-ES' : 'en-US', { hour: '2-digit', minute: '2-digit' })}
									</span>
								</div>
								<p class="mt-1 text-sm text-brand-600 dark:text-brand-400">{appt.patient_name}</p>
							</div>
						{/each}
					</div>
				{:else}
					<p class="text-sm text-[var(--text-secondary)]">{$t('dashboard.noAppointmentsToday')}</p>
				{/if}
			</div>

			<!-- Recent Patient Activity -->
			<div class="card">
				<div class="mb-4 flex items-center gap-2">
					<TrendingUp size={18} class="text-brand-600" />
					<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.recentActivity')}</h3>
				</div>
				<div class="space-y-3">
					<div class="flex items-center justify-between rounded-lg bg-[var(--bg-secondary)] p-3">
						<div class="flex items-center gap-2">
							<UtensilsCrossed size={16} class="text-orange-500" />
							<span class="text-sm text-[var(--text-primary)]">{$t('dashboard.mealsLast7d')}</span>
						</div>
						<span class="text-lg font-bold text-[var(--text-primary)]">{proSummary?.recent_meals_7d ?? 0}</span>
					</div>
					<div class="flex items-center justify-between rounded-lg bg-[var(--bg-secondary)] p-3">
						<div class="flex items-center gap-2">
							<Dumbbell size={16} class="text-blue-500" />
							<span class="text-sm text-[var(--text-primary)]">{$t('dashboard.workoutsLast7d')}</span>
						</div>
						<span class="text-lg font-bold text-[var(--text-primary)]">{proSummary?.recent_workouts_7d ?? 0}</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Quick Actions -->
		<div class="card">
			<div class="mb-4 flex items-center gap-2">
				<ArrowRight size={18} class="text-brand-600" />
				<h3 class="font-semibold text-[var(--text-primary)]">{$t('dashboard.quickActions')}</h3>
			</div>
			<div class="grid gap-3 sm:grid-cols-2">
				<a
					href={$authStore.user?.role === 'devadmin' ? '/app/admin' : '/app/professional'}
					class="flex items-center gap-3 rounded-lg border border-[var(--border-color)] p-4 hover:bg-[var(--bg-secondary)] transition-colors"
				>
					<Users size={20} class="text-brand-600" />
					<span class="font-medium text-[var(--text-primary)]">{$t('dashboard.viewPatients')}</span>
				</a>
				<a
					href="/app/professional/calendar"
					class="flex items-center gap-3 rounded-lg border border-[var(--border-color)] p-4 hover:bg-[var(--bg-secondary)] transition-colors"
				>
					<Calendar size={20} class="text-brand-600" />
					<span class="font-medium text-[var(--text-primary)]">{$t('dashboard.viewCalendar')}</span>
				</a>
			</div>
		</div>
	{/if}
</div>
