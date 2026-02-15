import { writable } from 'svelte/store';

export const unreadCount = writable<number>(0);
