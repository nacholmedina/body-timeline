<script lang="ts">
	import { toastStore } from '$stores/toast';
	import { CheckCircle, XCircle, Info, X } from 'lucide-svelte';
	import { fly, fade } from 'svelte/transition';
</script>

<div class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
	{#each $toastStore as toast (toast.id)}
		<div
			class="pointer-events-auto flex items-center gap-3 rounded-lg shadow-lg px-4 py-3 min-w-[300px] max-w-md border"
			class:bg-green-50={toast.type === 'success'}
			class:border-green-200={toast.type === 'success'}
			class:bg-red-50={toast.type === 'error'}
			class:border-red-200={toast.type === 'error'}
			class:bg-blue-50={toast.type === 'info'}
			class:border-blue-200={toast.type === 'info'}
			class:dark:bg-green-950={toast.type === 'success'}
			class:dark:border-green-800={toast.type === 'success'}
			class:dark:bg-red-950={toast.type === 'error'}
			class:dark:border-red-800={toast.type === 'error'}
			class:dark:bg-blue-950={toast.type === 'info'}
			class:dark:border-blue-800={toast.type === 'info'}
			in:fly={{ y: -20, duration: 300 }}
			out:fade={{ duration: 200 }}
		>
			{#if toast.type === 'success'}
				<CheckCircle size={20} class="text-green-600 dark:text-green-400 flex-shrink-0" />
			{:else if toast.type === 'error'}
				<XCircle size={20} class="text-red-600 dark:text-red-400 flex-shrink-0" />
			{:else}
				<Info size={20} class="text-blue-600 dark:text-blue-400 flex-shrink-0" />
			{/if}

			<p
				class="flex-1 text-sm font-medium"
				class:text-green-800={toast.type === 'success'}
				class:dark:text-green-200={toast.type === 'success'}
				class:text-red-800={toast.type === 'error'}
				class:dark:text-red-200={toast.type === 'error'}
				class:text-blue-800={toast.type === 'info'}
				class:dark:text-blue-200={toast.type === 'info'}
			>
				{toast.message}
			</p>

			<button
				on:click={() => toastStore.dismiss(toast.id)}
				class="flex-shrink-0 p-1 rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
				class:text-green-600={toast.type === 'success'}
				class:dark:text-green-400={toast.type === 'success'}
				class:text-red-600={toast.type === 'error'}
				class:dark:text-red-400={toast.type === 'error'}
				class:text-blue-600={toast.type === 'info'}
				class:dark:text-blue-400={toast.type === 'info'}
			>
				<X size={16} />
			</button>
		</div>
	{/each}
</div>
