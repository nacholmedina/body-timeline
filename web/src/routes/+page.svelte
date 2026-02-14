<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { authStore } from '$stores/auth';

	if (browser) {
		if ($authStore.isAuthenticated) {
			goto('/app/dashboard', { replaceState: true });
		} else {
			goto('/login', { replaceState: true });
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-[var(--bg-secondary)]">
	<div class="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600"></div>
</div>
