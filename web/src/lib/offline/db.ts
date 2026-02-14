import { openDB, type DBSchema, type IDBPDatabase } from 'idb';

interface BodyTimelineDB extends DBSchema {
	syncQueue: {
		key: number;
		value: {
			id?: number;
			type: 'meal' | 'weighIn' | 'workout' | 'goal';
			action: 'create' | 'update' | 'delete';
			payload: any;
			createdAt: string;
			retries: number;
		};
		indexes: { 'by-type': string };
	};
	cache: {
		key: string;
		value: {
			key: string;
			data: any;
			updatedAt: string;
		};
	};
}

let dbInstance: IDBPDatabase<BodyTimelineDB> | null = null;

export async function getDB(): Promise<IDBPDatabase<BodyTimelineDB>> {
	if (dbInstance) return dbInstance;

	dbInstance = await openDB<BodyTimelineDB>('body-timeline', 1, {
		upgrade(db) {
			const syncStore = db.createObjectStore('syncQueue', {
				keyPath: 'id',
				autoIncrement: true
			});
			syncStore.createIndex('by-type', 'type');

			db.createObjectStore('cache', { keyPath: 'key' });
		}
	});

	return dbInstance;
}

// ── Sync queue operations ────────────────────────────────

export async function addToSyncQueue(item: Omit<BodyTimelineDB['syncQueue']['value'], 'id' | 'createdAt' | 'retries'>) {
	const db = await getDB();
	await db.add('syncQueue', {
		...item,
		createdAt: new Date().toISOString(),
		retries: 0
	});
}

export async function getSyncQueue() {
	const db = await getDB();
	return db.getAll('syncQueue');
}

export async function removeSyncItem(id: number) {
	const db = await getDB();
	await db.delete('syncQueue', id);
}

export async function incrementRetry(id: number) {
	const db = await getDB();
	const tx = db.transaction('syncQueue', 'readwrite');
	const item = await tx.store.get(id);
	if (item) {
		item.retries += 1;
		await tx.store.put(item);
	}
	await tx.done;
}

export async function getSyncQueueCount(): Promise<number> {
	const db = await getDB();
	return db.count('syncQueue');
}

// ── Cache operations ─────────────────────────────────────

export async function getCached<T>(key: string): Promise<T | null> {
	const db = await getDB();
	const entry = await db.get('cache', key);
	return entry ? entry.data : null;
}

export async function setCache(key: string, data: any) {
	const db = await getDB();
	await db.put('cache', { key, data, updatedAt: new Date().toISOString() });
}

export async function clearCache() {
	const db = await getDB();
	await db.clear('cache');
}
