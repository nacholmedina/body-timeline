import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { UnitSystem } from '$stores/units';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

/** Returns current local datetime as "YYYY-MM-DDTHH:mm" for datetime inputs. */
export function localNow(): string {
	const d = new Date();
	const pad = (n: number) => String(n).padStart(2, '0');
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Returns current local date as "YYYY-MM-DD" for date inputs. */
export function localToday(): string {
	return localNow().slice(0, 10);
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

// ── Unit conversion ──

const KG_TO_LBS = 2.20462;
const CM_TO_INCH = 0.393701;

export function kgToLbs(kg: number): number {
	return kg * KG_TO_LBS;
}

export function lbsToKg(lbs: number): number {
	return lbs / KG_TO_LBS;
}

export function cmToFeetInches(cm: number): { feet: number; inches: number } {
	const totalInches = cm * CM_TO_INCH;
	let feet = Math.floor(totalInches / 12);
	let inches = Math.round(totalInches % 12);
	if (inches === 12) {
		feet += 1;
		inches = 0;
	}
	return { feet, inches };
}

export function feetInchesToCm(feet: number, inches: number): number {
	return (feet * 12 + inches) / CM_TO_INCH;
}

export function formatWeight(kg: number | null | undefined, system: UnitSystem): string {
	if (kg == null) return '—';
	if (system === 'imperial') {
		return `${kgToLbs(kg).toFixed(1)} lbs`;
	}
	return `${Number(kg).toFixed(1)} kg`;
}

export function formatHeight(cm: number | null | undefined, system: UnitSystem): string {
	if (cm == null) return '—';
	if (system === 'imperial') {
		const { feet, inches } = cmToFeetInches(cm);
		return `${feet}'${inches}"`;
	}
	return `${Number(cm).toFixed(1)} cm`;
}

export function weightUnit(system: UnitSystem): string {
	return system === 'imperial' ? 'lbs' : 'kg';
}

export function displayWeight(kg: number, system: UnitSystem): number {
	if (system === 'imperial') return parseFloat(kgToLbs(kg).toFixed(1));
	return parseFloat(Number(kg).toFixed(1));
}
