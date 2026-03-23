const GOOGLE_CLIENT_ID = '195898924440-jmhmuef02mb8afdioumnhj40bbrgms01.apps.googleusercontent.com';

/**
 * Opens Google OAuth in a popup window and returns the authorization code.
 * This bypasses One Tap cooldown issues entirely.
 */
export function googleSignIn(): Promise<string> {
	return new Promise((resolve, reject) => {
		const width = 500;
		const height = 600;
		const left = window.screenX + (window.outerWidth - width) / 2;
		const top = window.screenY + (window.outerHeight - height) / 2;

		const redirectUri = window.location.origin + '/auth/google/callback';
		const scope = 'openid email profile';
		const state = crypto.randomUUID();

		// Store state for CSRF verification
		sessionStorage.setItem('google_oauth_state', state);

		const params = new URLSearchParams({
			client_id: GOOGLE_CLIENT_ID,
			redirect_uri: redirectUri,
			response_type: 'code',
			scope,
			state,
			access_type: 'online',
			prompt: 'select_account',
		});

		const url = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;

		const popup = window.open(
			url,
			'google-auth',
			`width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no`
		);

		if (!popup) {
			reject(new Error('Popup blocked'));
			return;
		}

		// Listen for the callback message from the popup
		const handleMessage = (event: MessageEvent) => {
			if (event.origin !== window.location.origin) return;
			if (event.data?.type !== 'google-auth-callback') return;

			window.removeEventListener('message', handleMessage);
			clearInterval(pollTimer);

			if (event.data.error) {
				reject(new Error(event.data.error));
			} else if (event.data.code) {
				const savedState = sessionStorage.getItem('google_oauth_state');
				if (event.data.state !== savedState) {
					reject(new Error('State mismatch'));
				} else {
					resolve(event.data.code);
				}
			}
			sessionStorage.removeItem('google_oauth_state');
		};

		window.addEventListener('message', handleMessage);

		// Poll to detect if popup was closed without completing
		const pollTimer = setInterval(() => {
			if (popup.closed) {
				clearInterval(pollTimer);
				window.removeEventListener('message', handleMessage);
				sessionStorage.removeItem('google_oauth_state');
				reject(new Error('Popup closed'));
			}
		}, 500);
	});
}
