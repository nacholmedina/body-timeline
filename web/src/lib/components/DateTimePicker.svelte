<script lang="ts">
	export let value = '';
	export let required = false;
	export let id = '';

	// Split "2026-02-14T04:42" into date and time parts
	$: datePart = value ? value.slice(0, 10) : '';
	$: timePart = value ? value.slice(11, 16) : '';

	function updateValue(newDate: string, newTime: string) {
		if (newDate && newTime) {
			value = `${newDate}T${newTime}`;
		} else if (newDate) {
			value = `${newDate}T00:00`;
		} else {
			value = '';
		}
	}

	function onDateChange(e: Event) {
		const d = (e.target as HTMLInputElement).value;
		updateValue(d, timePart || '00:00');
	}

	function onTimeChange(e: Event) {
		const t = (e.target as HTMLInputElement).value;
		updateValue(datePart, t);
	}
</script>

<div class="grid grid-cols-2 gap-2">
	<input
		id={id ? `${id}-date` : undefined}
		type="date"
		value={datePart}
		on:input={onDateChange}
		class="datetime-input date-input"
		{required}
	/>
	<input
		id={id ? `${id}-time` : undefined}
		type="time"
		value={timePart}
		on:input={onTimeChange}
		class="datetime-input time-input"
	/>
</div>

<style>
	.datetime-input {
		font-family: inherit;
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text-primary);
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 0.5rem;
		padding: 0.625rem 0.75rem;
		transition: all 0.15s ease;
		cursor: pointer;
	}

	.datetime-input:hover {
		border-color: var(--brand-500);
	}

	.datetime-input:focus {
		outline: none;
		border-color: var(--brand-600);
		ring: 2px;
		ring-color: rgba(99, 102, 241, 0.1);
	}

	/* Calendar/clock icon styling */
	.datetime-input::-webkit-calendar-picker-indicator {
		cursor: pointer;
		opacity: 0.6;
		padding: 4px;
		border-radius: 4px;
		transition: all 0.15s ease;
	}

	.datetime-input::-webkit-calendar-picker-indicator:hover {
		opacity: 1;
		background: rgba(99, 102, 241, 0.1);
	}

	:global(.dark) .datetime-input::-webkit-calendar-picker-indicator {
		filter: invert(1);
		opacity: 0.7;
	}

	:global(.dark) .datetime-input::-webkit-calendar-picker-indicator:hover {
		opacity: 1;
	}

	/* Remove browser-specific styling */
	.datetime-input::-webkit-datetime-edit {
		padding: 0;
	}

	.datetime-input::-webkit-datetime-edit-fields-wrapper {
		padding: 0;
	}

	/* Mobile optimizations */
	@media (max-width: 640px) {
		.datetime-input {
			font-size: 1rem;
			padding: 0.75rem;
		}

		.datetime-input::-webkit-calendar-picker-indicator {
			width: 24px;
			height: 24px;
		}
	}
</style>
