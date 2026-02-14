import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date, locale = 'en'): string {
	const d = typeof date === 'string' ? new Date(date) : date;
	return d.toLocaleDateString(locale === 'es' ? 'es-ES' : 'en-US', {
		year: 'numeric',
		month: 'short',
		day: 'numeric'
	});
}

export function formatDateTime(date: string | Date, locale = 'en'): string {
	const d = typeof date === 'string' ? new Date(date) : date;
	return d.toLocaleString(locale === 'es' ? 'es-ES' : 'en-US', {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	});
}

export function timeAgo(date: string | Date, locale = 'en'): string {
	const d = typeof date === 'string' ? new Date(date) : date;
	const seconds = Math.floor((Date.now() - d.getTime()) / 1000);

	const intervals = [
		{ label: locale === 'es' ? 'año' : 'year', seconds: 31536000 },
		{ label: locale === 'es' ? 'mes' : 'month', seconds: 2592000 },
		{ label: locale === 'es' ? 'día' : 'day', seconds: 86400 },
		{ label: locale === 'es' ? 'hora' : 'hour', seconds: 3600 },
		{ label: locale === 'es' ? 'minuto' : 'minute', seconds: 60 }
	];

	for (const interval of intervals) {
		const count = Math.floor(seconds / interval.seconds);
		if (count >= 1) {
			return locale === 'es'
				? `hace ${count} ${interval.label}${count > 1 ? 's' : ''}`
				: `${count} ${interval.label}${count > 1 ? 's' : ''} ago`;
		}
	}
	return locale === 'es' ? 'justo ahora' : 'just now';
}
