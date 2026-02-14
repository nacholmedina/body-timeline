import { get } from 'svelte/store';
import { authStore } from '$stores/auth';
import { PUBLIC_API_URL } from '$env/static/public';

const BASE = PUBLIC_API_URL || 'http://localhost:5000/api/v1';

interface FetchOptions extends RequestInit {
	params?: Record<string, string>;
}

class ApiClient {
	private getHeaders(extra: HeadersInit = {}): HeadersInit {
		const auth = get(authStore);
		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...Object.fromEntries(
				extra instanceof Headers ? extra.entries() : Object.entries(extra as Record<string, string>)
			)
		};
		if (auth.accessToken) {
			headers['Authorization'] = `Bearer ${auth.accessToken}`;
		}
		return headers;
	}

	async fetch(path: string, options: FetchOptions = {}): Promise<any> {
		const { params, ...fetchOpts } = options;
		let url = `${BASE}${path}`;
		if (params) {
			const searchParams = new URLSearchParams(params);
			url += `?${searchParams.toString()}`;
		}

		const response = await fetch(url, {
			...fetchOpts,
			headers: this.getHeaders(fetchOpts.headers)
		});

		if (response.status === 401) {
			// Try refresh
			const refreshed = await this.refresh();
			if (refreshed) {
				const retryResponse = await fetch(url, {
					...fetchOpts,
					headers: this.getHeaders(fetchOpts.headers)
				});
				return this.handleResponse(retryResponse);
			}
			authStore.logout();
			if (typeof window !== 'undefined') {
				window.location.href = '/login';
			}
			throw new Error('Unauthorized');
		}

		return this.handleResponse(response);
	}

	private async handleResponse(response: Response) {
		const data = await response.json().catch(() => null);
		if (!response.ok) {
			const msg = data?.message || data?.error || `HTTP ${response.status}`;
			throw new ApiError(msg, response.status, data);
		}
		return data;
	}

	private async refresh(): Promise<boolean> {
		const auth = get(authStore);
		if (!auth.refreshToken) return false;

		try {
			const response = await fetch(`${BASE}/auth/refresh`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${auth.refreshToken}`
				}
			});
			if (response.ok) {
				const data = await response.json();
				authStore.setTokens(data.access_token, auth.refreshToken!);
				return true;
			}
		} catch {}
		return false;
	}

	get(path: string, params?: Record<string, string>) {
		return this.fetch(path, { method: 'GET', params });
	}

	post(path: string, body?: any) {
		return this.fetch(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined });
	}

	patch(path: string, body?: any) {
		return this.fetch(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined });
	}

	delete(path: string) {
		return this.fetch(path, { method: 'DELETE' });
	}

	async upload(path: string, file: File, extraFields?: Record<string, string>) {
		const auth = get(authStore);
		const formData = new FormData();
		formData.append('photo', file);
		if (extraFields) {
			for (const [key, value] of Object.entries(extraFields)) {
				formData.append(key, value);
			}
		}

		const response = await fetch(`${BASE}${path}`, {
			method: 'POST',
			headers: auth.accessToken ? { Authorization: `Bearer ${auth.accessToken}` } : {},
			body: formData
		});

		return this.handleResponse(response);
	}
}

export class ApiError extends Error {
	status: number;
	data: any;

	constructor(message: string, status: number, data?: any) {
		super(message);
		this.status = status;
		this.data = data;
	}
}

export const api = new ApiClient();

/**
 * Resolve a photo URL returned by the API.
 * Local storage returns relative paths like "/uploads/meals/abc.jpg";
 * S3/R2 returns full https:// presigned URLs.
 */
export function photoUrl(url: string): string {
	if (!url) return '';
	if (url.startsWith('http')) return url;
	// Relative path — prepend API server origin (or use current origin if BASE is relative)
	try {
		const origin = new URL(BASE).origin;
		return `${origin}${url}`;
	} catch {
		return url;
	}
}
