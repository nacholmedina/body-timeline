<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';

	onMount(() => {
		const code = $page.url.searchParams.get('code');
		const state = $page.url.searchParams.get('state');
		const error = $page.url.searchParams.get('error');

		if (window.opener) {
			window.opener.postMessage({
				type: 'google-auth-callback',
				code,
				state,
				error: error || undefined,
			}, window.location.origin);
			window.close();
		}
	});
</script>

<div class="flex min-h-screen items-center justify-center">
	<p class="text-[var(--text-secondary)]">Completing sign-in...</p>
</div>
