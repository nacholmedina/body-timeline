<script lang="ts">
	import { X } from 'lucide-svelte';
	import { t } from '$i18n/index';

	export let show = false;
	export let title = '';
	export let message = '';
	export let confirmText = $t('common.yes');
	export let cancelText = $t('common.no');
	export let onConfirm: () => void = () => {};
	export let loading = false;

	function handleConfirm() {
		onConfirm();
	}

	function handleCancel() {
		show = false;
	}

	function handleBackdropClick() {
		if (!loading) {
			show = false;
		}
	}
</script>

{#if show}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
		on:click={handleBackdropClick}
		role="dialog"
		aria-modal="true"
	>
		<div
			class="w-full max-w-sm rounded-lg bg-white dark:bg-gray-800 p-6 shadow-xl"
			on:click|stopPropagation
			role="document"
		>
			<!-- Header -->
			<div class="flex items-center justify-between mb-3">
				<h2 class="text-lg font-bold text-[var(--text-primary)]">{title}</h2>
				{#if !loading}
					<button
						on:click={handleCancel}
						class="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
						aria-label="Close"
					>
						<X size={20} />
					</button>
				{/if}
			</div>

			<!-- Message -->
			<p class="text-sm text-[var(--text-secondary)] mb-6">{message}</p>

			<!-- Actions -->
			<div class="flex gap-3">
				<button
					on:click={handleCancel}
					class="btn-secondary flex-1"
					disabled={loading}
					type="button"
				>
					{cancelText}
				</button>
				<button
					on:click={handleConfirm}
					class="btn-danger flex-1"
					disabled={loading}
					type="button"
				>
					{confirmText}
				</button>
			</div>
		</div>
	</div>
{/if}
