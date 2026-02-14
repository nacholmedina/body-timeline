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
		class="input"
		{required}
	/>
	<input
		id={id ? `${id}-time` : undefined}
		type="time"
		value={timePart}
		on:input={onTimeChange}
		class="input"
	/>
</div>
