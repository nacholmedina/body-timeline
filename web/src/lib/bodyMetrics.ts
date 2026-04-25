// Shared client-side config for body composition / measurement metrics.
// Backend storage is always metric (kg, cm, %); the frontend converts to/from
// the user's chosen unit system at the input/display boundaries.
// Source of truth for canonical ranges: api/app/services/body_metrics.py.

import type { UnitSystem } from '$stores/units';
import { cmToInches, inchesToCm, kgToLbs, lbsToKg } from './utils';

export type BodyMetricKey = 'body_fat_pct' | 'muscle_mass_kg' | 'waist_cm' | 'hips_cm' | 'neck_cm';
export type BodyMetricFamily = 'percent' | 'mass' | 'length';

export type BodyMetricConfig = {
	key: BodyMetricKey;
	endpoint: string;
	labelKey: string;
	family: BodyMetricFamily;
	// Canonical (metric) range — what the backend enforces.
	minMetric: number;
	maxMetric: number;
};

export const BODY_METRICS: BodyMetricConfig[] = [
	{ key: 'body_fat_pct', endpoint: '/body-fat-logs', labelKey: 'profile.bodyComposition.bodyFat', family: 'percent', minMetric: 3, maxMetric: 75 },
	{ key: 'muscle_mass_kg', endpoint: '/muscle-mass-logs', labelKey: 'profile.bodyComposition.muscleMass', family: 'mass', minMetric: 10, maxMetric: 120 },
	{ key: 'waist_cm', endpoint: '/waist-measurements', labelKey: 'profile.bodyComposition.waist', family: 'length', minMetric: 40, maxMetric: 200 },
	{ key: 'hips_cm', endpoint: '/hips-measurements', labelKey: 'profile.bodyComposition.hips', family: 'length', minMetric: 50, maxMetric: 200 },
	{ key: 'neck_cm', endpoint: '/neck-measurements', labelKey: 'profile.bodyComposition.neck', family: 'length', minMetric: 20, maxMetric: 70 }
];

export function unitFor(family: BodyMetricFamily, system: UnitSystem): string {
	if (family === 'percent') return '%';
	if (family === 'mass') return system === 'imperial' ? 'lbs' : 'kg';
	return system === 'imperial' ? 'in' : 'cm';
}

export function metricToDisplay(family: BodyMetricFamily, system: UnitSystem, metricValue: number): number {
	if (family === 'percent') return metricValue;
	if (family === 'mass') return system === 'imperial' ? kgToLbs(metricValue) : metricValue;
	return system === 'imperial' ? cmToInches(metricValue) : metricValue;
}

export function displayToMetric(family: BodyMetricFamily, system: UnitSystem, displayValue: number): number {
	if (family === 'percent') return displayValue;
	if (family === 'mass') return system === 'imperial' ? lbsToKg(displayValue) : displayValue;
	return system === 'imperial' ? inchesToCm(displayValue) : displayValue;
}

export function displayRange(metric: BodyMetricConfig, system: UnitSystem): { min: number; max: number } {
	const min = metricToDisplay(metric.family, system, metric.minMetric);
	const max = metricToDisplay(metric.family, system, metric.maxMetric);
	return {
		min: parseFloat(min.toFixed(1)),
		max: parseFloat(max.toFixed(1))
	};
}

export function isOutOfRangeMetric(metric: BodyMetricConfig, metricValue: number): boolean {
	return !Number.isFinite(metricValue) || metricValue < metric.minMetric || metricValue > metric.maxMetric;
}
