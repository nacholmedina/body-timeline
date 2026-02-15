import { writable, get } from 'svelte/store';
import { getSyncQueue, removeSyncItem, incrementRetry } from './db';
import { api } from '$lib/api/client';
import { onlineStore } from '$stores/online';

export type SyncStatus = 'idle' | 'syncing' | 'error' | 'complete';

export const syncStatus = writable<SyncStatus>('idle');
export const syncPending = writable<number>(0);

const MAX_RETRIES = 5;

const ACTION_MAP: Record<string, Record<string, { method: string; path: (p: any) => string }>> = {
	meal: {
		create: { method: 'post', path: () => '/meals' },
		update: { method: 'patch', path: (p) => `/meals/${p.id}` },
		delete: { method: 'delete', path: (p) => `/meals/${p.id}` }
	},
	weighIn: {
		create: { method: 'post', path: () => '/weigh-ins' },
		update: { method: 'patch', path: (p) => `/weigh-ins/${p.id}` },
		delete: { method: 'delete', path: (p) => `/weigh-ins/${p.id}` }
	},
	workout: {
		create: { method: 'post', path: () => '/workouts' },
		update: { method: 'patch', path: (p) => `/workouts/${p.id}` },
		delete: { method: 'delete', path: (p) => `/workouts/${p.id}` }
	},
	goal: {
		create: { method: 'post', path: () => '/goals' },
		update: { method: 'patch', path: (p) => `/goals/${p.id}` },
		delete: { method: 'delete', path: (p) => `/goals/${p.id}` }
	},
	exercise: {
		create: { method: 'post', path: () => '/exercise-logs' },
		update: { method: 'patch', path: (p) => `/exercise-logs/${p.id}` },
		delete: { method: 'delete', path: (p) => `/exercise-logs/${p.id}` }
	}
};

export async function syncAll(): Promise<void> {
	if (!get(onlineStore)) return;

	const queue = await getSyncQueue();
	if (queue.length === 0) {
		syncStatus.set('idle');
		syncPending.set(0);
		return;
	}

	syncStatus.set('syncing');
	syncPending.set(queue.length);

	for (const item of queue) {
		if (item.retries >= MAX_RETRIES) {
			await removeSyncItem(item.id!);
			continue;
		}

		const config = ACTION_MAP[item.type]?.[item.action];
		if (!config) {
			await removeSyncItem(item.id!);
			continue;
		}

		try {
			const method = config.method as 'get' | 'post' | 'patch' | 'delete';
			const path = config.path(item.payload);

			if (method === 'delete') {
				await api.delete(path);
			} else if (method === 'post') {
				await api.post(path, item.payload);
			} else if (method === 'patch') {
				await api.patch(path, item.payload);
			}

			await removeSyncItem(item.id!);
			syncPending.update((n) => Math.max(0, n - 1));
		} catch (err) {
			await incrementRetry(item.id!);
		}
	}

	const remaining = await getSyncQueue();
	syncPending.set(remaining.length);
	syncStatus.set(remaining.length > 0 ? 'error' : 'complete');

	// Reset to idle after a delay
	setTimeout(() => syncStatus.set('idle'), 3000);
}

// Auto-sync when coming back online
if (typeof window !== 'undefined') {
	window.addEventListener('online', () => {
		setTimeout(syncAll, 1000);
	});
}
