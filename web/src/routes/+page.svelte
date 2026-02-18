<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { authStore } from '$stores/auth';
	import { t } from '$i18n/index';
	import { BRANDING } from '$lib/config/branding';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import LanguageToggle from '$components/LanguageToggle.svelte';
	import {
		UtensilsCrossed, Dumbbell, Target, Calendar,
		Scale, UserCheck, Stethoscope,
		Monitor, Smartphone, Download, ChevronDown,
		ArrowRight, Heart
	} from 'lucide-svelte';

	// Redirect authenticated users to dashboard
	$: if (browser && $authStore.isAuthenticated) {
		goto('/app/dashboard', { replaceState: true });
	}

	let scrolled = false;
	let openFaq: number | null = null;

	function toggleFaq(index: number) {
		openFaq = openFaq === index ? null : index;
	}

	function handleScroll() {
		scrolled = window.scrollY > 20;
	}

	$: features = [
		{ icon: UtensilsCrossed, title: $t('landing.featureMeals'), desc: $t('landing.featureMealsDesc'), color: 'orange' },
		{ icon: Dumbbell, title: $t('landing.featureExercises'), desc: $t('landing.featureExercisesDesc'), color: 'blue' },
		{ icon: Scale, title: $t('landing.featureWeighIns'), desc: $t('landing.featureWeighInsDesc'), color: 'purple' },
		{ icon: Target, title: $t('landing.featureGoals'), desc: $t('landing.featureGoalsDesc'), color: 'green' },
		{ icon: Calendar, title: $t('landing.featureAppointments'), desc: $t('landing.featureAppointmentsDesc'), color: 'pink' },
		{ icon: Stethoscope, title: $t('landing.featureProfessional'), desc: $t('landing.featureProfessionalDesc'), color: 'cyan' },
	];

	$: faqs = [
		{ q: $t('landing.faq1Q'), a: $t('landing.faq1A') },
		{ q: $t('landing.faq2Q'), a: $t('landing.faq2A') },
		{ q: $t('landing.faq3Q'), a: $t('landing.faq3A') },
		{ q: $t('landing.faq4Q'), a: $t('landing.faq4A') },
	];

	const colorMap: Record<string, { bg: string; text: string; darkBg: string; darkText: string }> = {
		orange: { bg: 'bg-orange-100', text: 'text-orange-600', darkBg: 'dark:bg-orange-950', darkText: 'dark:text-orange-400' },
		blue:   { bg: 'bg-blue-100',   text: 'text-blue-600',   darkBg: 'dark:bg-blue-950',   darkText: 'dark:text-blue-400' },
		green:  { bg: 'bg-green-100',  text: 'text-green-600',  darkBg: 'dark:bg-green-950',  darkText: 'dark:text-green-400' },
		purple: { bg: 'bg-purple-100', text: 'text-purple-600', darkBg: 'dark:bg-purple-950', darkText: 'dark:text-purple-400' },
		pink:   { bg: 'bg-pink-100',   text: 'text-pink-600',   darkBg: 'dark:bg-pink-950',   darkText: 'dark:text-pink-400' },
		cyan:   { bg: 'bg-cyan-100',   text: 'text-cyan-600',   darkBg: 'dark:bg-cyan-950',   darkText: 'dark:text-cyan-400' },
	};
</script>

<svelte:head>
	<title>{BRANDING.appName} — {$t('app.tagline')}</title>
</svelte:head>

<svelte:window on:scroll={handleScroll} />

<div class="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">

	<!-- ═══ NAVBAR ═══ -->
	<nav
		class="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
		class:bg-[var(--bg-card)]={scrolled}
		class:shadow-md={scrolled}
		class:bg-transparent={!scrolled}
	>
		<div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
			<div class="flex items-center gap-2">
				<img src="/brand-icon-64.png" alt="{BRANDING.appName}" class="h-9 w-9 rounded-xl" />
				<span class="text-xl font-bold text-[var(--text-primary)]">{BRANDING.appName}</span>
			</div>

			<div class="flex items-center gap-1 sm:gap-2">
				<LanguageToggle />
				<ThemeToggle />
				<a
					href="/login"
					class="ml-2 hidden sm:inline-flex items-center rounded-lg px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
				>
					{$t('auth.login')}
				</a>
				<a
					href="/register"
					class="ml-1 inline-flex items-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition-colors shadow-sm"
				>
					{$t('auth.register')}
				</a>
			</div>
		</div>
	</nav>

	<!-- ═══ HERO ═══ -->
	<section class="relative overflow-hidden pt-28 pb-20 sm:pt-36 sm:pb-28 lg:pt-44 lg:pb-36">
		<!-- Background blobs -->
		<div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
			<div class="mist-blob-1 absolute -top-40 -left-40 h-[600px] w-[600px] rounded-full bg-brand-400/20 dark:bg-brand-500/10 blur-[150px]"></div>
			<div class="mist-blob-2 absolute top-20 -right-40 h-[500px] w-[500px] rounded-full bg-brand-300/15 dark:bg-indigo-500/8 blur-[150px]"></div>
			<div class="mist-blob-3 absolute -bottom-40 left-1/3 h-[500px] w-[500px] rounded-full bg-accent-400/15 dark:bg-accent-500/8 blur-[150px]"></div>
		</div>

		<div class="relative mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
			<h1 class="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
				{$t('landing.heroTitle')}
				<span class="bg-gradient-to-r from-brand-500 to-brand-700 dark:from-brand-400 dark:to-brand-600 bg-clip-text text-transparent">
					{$t('landing.heroTitleHighlight')}
				</span>
			</h1>

			<p class="mx-auto mt-6 max-w-2xl text-lg text-[var(--text-secondary)] sm:text-xl leading-relaxed">
				{$t('landing.heroDescription')}
			</p>

			<div class="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
				<a
					href="/register"
					class="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-8 py-3.5 text-base font-semibold text-white hover:bg-brand-700 transition-all shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 hover:-translate-y-0.5"
				>
					{$t('landing.heroCta')}
					<ArrowRight size={18} />
				</a>
				<a
					href="/login"
					class="inline-flex items-center gap-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] px-8 py-3.5 text-base font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-all"
				>
					{$t('landing.heroLogin')}
				</a>
			</div>

			<!-- Desktop & Mobile badge -->
			<div class="mt-10 inline-flex items-center gap-2 rounded-full border border-[var(--border-color)] bg-[var(--bg-card)]/80 backdrop-blur-sm px-5 py-2.5 text-sm text-[var(--text-secondary)]">
				<Monitor size={16} class="text-brand-500" />
				<span class="text-[var(--text-secondary)]">+</span>
				<Smartphone size={16} class="text-brand-500" />
				<span>{$t('landing.heroDesktopMobile')}</span>
			</div>
		</div>
	</section>

	<!-- ═══ FEATURES ═══ -->
	<section class="py-20 sm:py-28">
		<div class="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
			<div class="text-center">
				<h2 class="text-3xl font-bold sm:text-4xl">
					{$t('landing.featuresTitle')}
					<span class="bg-gradient-to-r from-brand-500 to-brand-700 dark:from-brand-400 dark:to-brand-600 bg-clip-text text-transparent">
						{$t('landing.featuresTitleHighlight')}
					</span>
				</h2>
				<p class="mx-auto mt-4 max-w-2xl text-[var(--text-secondary)] text-lg">
					{$t('landing.featuresSubtitle')}
				</p>
			</div>

			<div class="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
				{#each features as feature}
					{@const colors = colorMap[feature.color]}
					<div class="group card hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
						<div class="mb-4 inline-flex rounded-xl p-3 {colors.bg} {colors.darkBg}">
							<svelte:component this={feature.icon} size={24} class="{colors.text} {colors.darkText}" />
						</div>
						<h3 class="text-lg font-semibold text-[var(--text-primary)]">{feature.title}</h3>
						<p class="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">{feature.desc}</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- ═══ MISSION ═══ -->
	<section class="relative py-20 sm:py-28 bg-[var(--bg-secondary)]">
		<div class="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
			<div class="text-center">
				<h2 class="text-3xl font-bold sm:text-4xl">
					{$t('landing.missionTitle')}
					<span class="bg-gradient-to-r from-brand-500 to-brand-700 dark:from-brand-400 dark:to-brand-600 bg-clip-text text-transparent">
						{$t('landing.missionTitleHighlight')}
					</span>
				</h2>
				<p class="mx-auto mt-4 max-w-3xl text-[var(--text-secondary)] text-lg leading-relaxed">
					{$t('landing.missionDescription')}
				</p>
			</div>

			<div class="mt-16 grid gap-8 sm:grid-cols-2 max-w-3xl mx-auto">
				<!-- Patient -->
				<div class="relative rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] p-6 text-center">
					<div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-green-100 dark:bg-green-950">
						<Heart size={28} class="text-green-600 dark:text-green-400" />
					</div>
					<h3 class="text-lg font-semibold text-[var(--text-primary)]">{$t('landing.missionPatient')}</h3>
					<p class="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed">{$t('landing.missionPatientDesc')}</p>
				</div>

				<!-- Professional -->
				<div class="relative rounded-2xl border border-brand-200 dark:border-brand-800 bg-[var(--bg-card)] p-6 text-center ring-1 ring-brand-100 dark:ring-brand-900">
					<div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-100 dark:bg-brand-950">
						<UserCheck size={28} class="text-brand-600 dark:text-brand-400" />
					</div>
					<h3 class="text-lg font-semibold text-[var(--text-primary)]">{$t('landing.missionProfessional')}</h3>
					<p class="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed">{$t('landing.missionProfessionalDesc')}</p>
				</div>

			</div>
		</div>
	</section>

	<!-- ═══ PLATFORM ═══ -->
	<section class="py-20 sm:py-28">
		<div class="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
			<div class="text-center">
				<h2 class="text-3xl font-bold sm:text-4xl">
					{$t('landing.platformTitle')}
					<span class="bg-gradient-to-r from-brand-500 to-brand-700 dark:from-brand-400 dark:to-brand-600 bg-clip-text text-transparent">
						{$t('landing.platformTitleHighlight')}
					</span>
				</h2>
				<p class="mx-auto mt-4 max-w-3xl text-[var(--text-secondary)] text-lg leading-relaxed">
					{$t('landing.platformDescription')}
				</p>
			</div>

			<div class="mt-16 grid gap-6 sm:grid-cols-3">
				<div class="card text-center hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
					<div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-100 dark:bg-brand-950">
						<Monitor size={24} class="text-brand-600 dark:text-brand-400" />
					</div>
					<h3 class="font-semibold text-[var(--text-primary)]">{$t('landing.platformDesktop')}</h3>
					<p class="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">{$t('landing.platformDesktopDesc')}</p>
				</div>

				<div class="card text-center hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
					<div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-100 dark:bg-brand-950">
						<Smartphone size={24} class="text-brand-600 dark:text-brand-400" />
					</div>
					<h3 class="font-semibold text-[var(--text-primary)]">{$t('landing.platformMobile')}</h3>
					<p class="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">{$t('landing.platformMobileDesc')}</p>
				</div>

				<div class="card text-center hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
					<div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-100 dark:bg-brand-950">
						<Download size={24} class="text-brand-600 dark:text-brand-400" />
					</div>
					<h3 class="font-semibold text-[var(--text-primary)]">{$t('landing.platformPwa')}</h3>
					<p class="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">{$t('landing.platformPwaDesc')}</p>
				</div>
			</div>
		</div>
	</section>

	<!-- ═══ FAQ ═══ -->
	<section class="py-20 sm:py-28 bg-[var(--bg-secondary)]">
		<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
			<div class="text-center">
				<h2 class="text-3xl font-bold sm:text-4xl">
					{$t('landing.faqTitle')}
					<span class="bg-gradient-to-r from-brand-500 to-brand-700 dark:from-brand-400 dark:to-brand-600 bg-clip-text text-transparent">
						{$t('landing.faqTitleHighlight')}
					</span>
				</h2>
			</div>

			<div class="mt-12 space-y-3">
				{#each faqs as faq, i}
					<div class="rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden">
						<button
							on:click={() => toggleFaq(i)}
							class="flex w-full items-center justify-between px-6 py-4 text-left font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]/50 transition-colors"
						>
							<span>{faq.q}</span>
							<ChevronDown
								size={20}
								class="shrink-0 ml-4 text-[var(--text-secondary)] transition-transform duration-200 {openFaq === i ? 'rotate-180' : ''}"
							/>
						</button>
						{#if openFaq === i}
							<div class="px-6 pb-4 text-sm text-[var(--text-secondary)] leading-relaxed">
								{@html faq.a}
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- ═══ BOTTOM CTA ═══ -->
	<section class="relative overflow-hidden py-20 sm:py-28">
		<div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
			<div class="mist-blob-1 absolute -top-20 -right-40 h-[400px] w-[400px] rounded-full bg-brand-400/15 dark:bg-brand-500/8 blur-[120px]"></div>
			<div class="mist-blob-2 absolute -bottom-20 -left-40 h-[400px] w-[400px] rounded-full bg-accent-400/15 dark:bg-accent-500/8 blur-[120px]"></div>
		</div>

		<div class="relative mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
			<h2 class="text-3xl font-bold sm:text-4xl">
				{$t('landing.ctaTitle')}
				<span class="bg-gradient-to-r from-brand-500 to-brand-700 dark:from-brand-400 dark:to-brand-600 bg-clip-text text-transparent">
					{$t('landing.ctaTitleHighlight')}
				</span>
			</h2>
			<p class="mx-auto mt-4 max-w-xl text-[var(--text-secondary)] text-lg leading-relaxed">
				{$t('landing.ctaDescription')}
			</p>
			<div class="mt-10">
				<a
					href="/register"
					class="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-8 py-3.5 text-base font-semibold text-white hover:bg-brand-700 transition-all shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 hover:-translate-y-0.5"
				>
					{$t('landing.ctaButton')}
					<ArrowRight size={18} />
				</a>
			</div>
		</div>
	</section>

	<!-- ═══ FOOTER ═══ -->
	<footer class="border-t border-[var(--border-color)] py-8">
		<div class="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
			<div class="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
				<div class="flex items-center gap-2 sm:w-1/3">
					<img src="/brand-icon-64.png" alt="{BRANDING.appName}" class="h-7 w-7 rounded-lg" />
					<span class="font-semibold text-[var(--text-primary)]">{BRANDING.appName}</span>
				</div>

				<div class="sm:w-1/3 sm:text-center">
					<a
						href="https://wa.me/5493585416034?text={encodeURIComponent($t('landing.whatsappMessage'))}"
						target="_blank"
						rel="noopener noreferrer"
						class="inline-flex items-center gap-2 rounded-full bg-[#25D366] px-4 py-2 text-white text-sm font-medium hover:bg-[#20BD5A] transition-colors"
					>
						<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
							<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
						</svg>
						{$t('landing.whatsappLabel')}
					</a>
				</div>

				<p class="text-sm text-[var(--text-secondary)] sm:w-1/3 sm:text-right">
					&copy; {new Date().getFullYear()} {BRANDING.appName}. {$t('landing.footerRights')}
				</p>
			</div>
		</div>
	</footer>
</div>
