import type { Config } from 'tailwindcss';

export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			colors: {
				brand: {
					50: '#eef9ff',
					100: '#d9f1ff',
					200: '#bce8ff',
					300: '#8edaff',
					400: '#59c3ff',
					500: '#33a5ff',
					600: '#1b87f5',
					700: '#146fe1',
					800: '#175ab6',
					900: '#194d8f',
					950: '#143057'
				},
				accent: {
					50: '#f0fdf4',
					100: '#dcfce7',
					200: '#bbf7d0',
					300: '#86efac',
					400: '#4ade80',
					500: '#22c55e',
					600: '#16a34a',
					700: '#15803d',
					800: '#166534',
					900: '#14532d',
					950: '#052e16'
				}
			},
			fontFamily: {
				sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif']
			}
		}
	},
	plugins: []
} satisfies Config;
