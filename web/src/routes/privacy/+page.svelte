<script lang="ts">
	import { locale } from '$i18n/index';
	import { BRANDING } from '$lib/config/branding';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import LanguageToggle from '$components/LanguageToggle.svelte';

	const CONTACT_EMAIL = 'help@wellvio.com.ar';
	const EFFECTIVE_DATE = '2026-04-25';
	const JURISDICTION_ES = 'Río Cuarto, Provincia de Córdoba, Argentina';
	const JURISDICTION_EN = 'Río Cuarto, Province of Córdoba, Argentina';
</script>

<svelte:head>
	<title>{$locale === 'es' ? 'Política de Privacidad' : 'Privacy Policy'} — {BRANDING.appName}</title>
	<meta
		name="description"
		content={$locale === 'es'
			? 'Política de privacidad de Wellvio: qué datos recopilamos, cómo los usamos y los derechos de los usuarios.'
			: 'Wellvio privacy policy: what data we collect, how we use it, and user rights.'}
	/>
</svelte:head>

<div class="min-h-screen bg-[var(--bg-primary)]">
	<div class="border-b border-[var(--border-color)] bg-[var(--bg-secondary)]">
		<div class="mx-auto max-w-3xl flex items-center justify-between px-4 py-3">
			<a href="/" class="text-lg font-bold text-[var(--text-primary)]">{BRANDING.appName}</a>
			<div class="flex items-center gap-2">
				<LanguageToggle />
				<ThemeToggle />
			</div>
		</div>
	</div>

	<article class="mx-auto max-w-3xl px-4 py-10 text-[var(--text-primary)]">
		{#if $locale === 'es'}
			<h1 class="text-3xl font-bold mb-2">Política de Privacidad</h1>
			<p class="text-sm text-[var(--text-secondary)] mb-8">
				Última actualización: {EFFECTIVE_DATE}
			</p>

			<section class="mb-6">
				<p>
					Esta Política de Privacidad describe cómo {BRANDING.appName} ("nosotros", "nuestro" o "la
					aplicación") recopila, utiliza y protege la información personal de las personas que
					utilizan nuestros servicios (los "Usuarios"). Al usar {BRANDING.appName} aceptás las
					prácticas descritas en esta política.
				</p>
			</section>

			<h2 class="text-xl font-semibold mt-8 mb-3">1. Quiénes somos</h2>
			<p>
				{BRANDING.appName} es una aplicación de seguimiento de salud y bienestar que permite a
				profesionales de la salud (nutricionistas, entrenadores y similares) gestionar pacientes,
				turnos y planes; y a los pacientes registrar comidas, pesajes, ejercicios, objetivos y
				notas. El responsable del tratamiento es la persona física o jurídica que opera {BRANDING.appName}.
				Para consultas sobre privacidad podés escribirnos a
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">2. Información que recopilamos</h2>
			<p class="mb-3">Recopilamos las siguientes categorías de información:</p>
			<ul class="list-disc pl-6 space-y-2">
				<li>
					<strong>Información de la cuenta:</strong> nombre, apellido, correo electrónico,
					contraseña (almacenada en forma de hash), género, fecha de nacimiento opcional,
					teléfono opcional y avatar opcional.
				</li>
				<li>
					<strong>Datos de salud y actividad:</strong> registros de comidas, pesajes, ejercicios,
					rutinas, mediciones corporales, objetivos y notas que vos o tu profesional ingresan en
					la aplicación.
				</li>
				<li>
					<strong>Información de turnos:</strong> fechas, horarios, modalidad (presencial u
					online), notas de turno y estado.
				</li>
				<li>
					<strong>Datos de inicio de sesión con Google:</strong> identificador de Google,
					dirección de correo, nombre y foto de perfil cuando elegís iniciar sesión con Google.
				</li>
				<li>
					<strong>Datos de Google Calendar:</strong> si conectás tu cuenta de Google Calendar, almacenamos
					un token de acceso, un token de actualización (refresh token), tu identificador de calendario
					y los identificadores de los eventos que creamos en tu nombre. Solo usamos estos datos para
					crear, actualizar o eliminar eventos correspondientes a tus turnos en {BRANDING.appName}.
					No leemos eventos que no hayan sido creados por la aplicación.
				</li>
				<li>
					<strong>Datos técnicos:</strong> dirección IP, agente de usuario, identificadores de
					dispositivo y registros de actividad básicos para fines de seguridad y diagnóstico.
				</li>
				<li>
					<strong>Almacenamiento local en tu dispositivo:</strong> tokens de sesión, preferencias
					(idioma, tema), y caché de datos para el modo offline.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">3. Cómo utilizamos tu información</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>Para crear y administrar tu cuenta, autenticarte y mantener tu sesión.</li>
				<li>
					Para proveer las funcionalidades del producto: registro de comidas, ejercicios,
					pesajes, gestión de turnos, comunicación entre profesional y paciente, y demás
					funciones.
				</li>
				<li>
					Para sincronizar tus turnos con Google Calendar cuando lo conectes voluntariamente.
				</li>
				<li>Para enviarte notificaciones sobre tus turnos, mensajes y actividad de tu cuenta.</li>
				<li>
					Para mejorar el producto, detectar errores, prevenir fraudes y mantener la seguridad de
					la plataforma.
				</li>
				<li>Para cumplir con obligaciones legales aplicables.</li>
			</ul>
			<p class="mt-3">
				No utilizamos tu información para publicidad de terceros, ni la vendemos, ni la entregamos
				a terceros con fines comerciales.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">4. Uso del scope de Google Calendar</h2>
			<p class="mb-3">
				Cuando conectás Google Calendar, {BRANDING.appName} solicita el permiso
				<code>https://www.googleapis.com/auth/calendar.events</code>. Lo usamos exclusivamente
				para:
			</p>
			<ul class="list-disc pl-6 space-y-2">
				<li>Crear un evento en tu calendario cuando un turno es reservado en {BRANDING.appName}.</li>
				<li>Actualizar el evento si el turno se modifica.</li>
				<li>Eliminar el evento si el turno se cancela.</li>
			</ul>
			<p class="mt-3">
				No leemos, modificamos ni eliminamos eventos que no hayan sido creados por
				{BRANDING.appName}. No transferimos los datos de Google a terceros, no los usamos para
				publicidad, no los usamos para entrenar modelos de inteligencia artificial, ni los
				utilizamos para ninguna finalidad distinta a la sincronización de turnos. El uso que
				{BRANDING.appName} hace de la información recibida de las APIs de Google cumple con la
				<a
					class="text-brand-600 dark:text-brand-400 underline"
					href="https://developers.google.com/terms/api-services-user-data-policy"
					target="_blank"
					rel="noopener noreferrer">Política de Datos del Usuario de los Servicios de API de Google</a
				>, incluidos los requisitos de Uso Limitado.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">5. Cómo compartimos tu información</h2>
			<p class="mb-3">Solo compartimos tu información en los siguientes casos:</p>
			<ul class="list-disc pl-6 space-y-2">
				<li>
					<strong>Con tu profesional asignado o con pacientes asignados:</strong> los datos
					necesarios para que la relación profesional-paciente funcione.
				</li>
				<li>
					<strong>Con proveedores que prestan servicios para nosotros:</strong> hosting, base de
					datos, envío de correos, infraestructura en la nube, y procesamiento de autenticación
					(Google). Estos proveedores actúan como encargados de tratamiento bajo nuestras
					instrucciones.
				</li>
				<li>
					<strong>Cuando lo exija la ley:</strong> en respuesta a requerimientos legales válidos
					emitidos por autoridades competentes.
				</li>
				<li>
					<strong>Para proteger derechos:</strong> cuando sea necesario para investigar, prevenir
					o tomar acción frente a actividades ilegales, fraude o problemas técnicos.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">6. Conservación de datos</h2>
			<p>
				Conservamos tus datos mientras tu cuenta esté activa y mientras sean necesarios para
				prestar el servicio. Podés solicitar la eliminación de tu cuenta en cualquier momento
				escribiendo a <a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>. Algunos datos pueden conservarse por períodos adicionales para cumplir obligaciones
				legales, resolver disputas o hacer cumplir nuestros acuerdos.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">7. Tus derechos</h2>
			<p class="mb-3">Tenés derecho a:</p>
			<ul class="list-disc pl-6 space-y-2">
				<li>Acceder a la información personal que tenemos sobre vos.</li>
				<li>Solicitar la corrección o actualización de información incorrecta.</li>
				<li>Solicitar la eliminación de tu cuenta y de los datos asociados.</li>
				<li>Solicitar una copia de tus datos en un formato portable.</li>
				<li>
					Revocar el consentimiento de la integración con Google Calendar en cualquier momento
					desde tu configuración o desde tu cuenta de Google.
				</li>
				<li>
					Presentar una denuncia ante la Agencia de Acceso a la Información Pública de la
					República Argentina si considerás que se vulneraron tus derechos.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">8. Seguridad</h2>
			<p>
				Aplicamos medidas técnicas y organizativas razonables para proteger tu información:
				cifrado en tránsito (HTTPS), almacenamiento de contraseñas con hash, control de accesos,
				registros de actividad y respaldos periódicos. Ningún sistema es 100% seguro; en caso de
				detectar una vulneración relevante notificaremos a los Usuarios afectados conforme exige
				la ley.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">9. Transferencias internacionales</h2>
			<p>
				Algunos de nuestros proveedores (por ejemplo, Google) operan servidores fuera de la
				República Argentina. Al usar {BRANDING.appName} entendés que tus datos pueden ser
				procesados en otros países que pueden tener regímenes distintos de protección de datos.
				Tomamos las medidas razonables para que cualquier transferencia se realice con garantías
				adecuadas.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">10. Menores de edad</h2>
			<p>
				{BRANDING.appName} no está dirigida a menores de 13 años. Si sos un padre, madre o tutor y
				considerás que un menor a tu cargo nos ha provisto información, escribinos a
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				> y la eliminaremos.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">11. Cookies y almacenamiento local</h2>
			<p>
				Usamos almacenamiento local del navegador (localStorage / IndexedDB) para guardar tu
				sesión, preferencias e información en caché para el modo offline. No usamos cookies de
				seguimiento de terceros con fines publicitarios.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">12. Cambios en esta política</h2>
			<p>
				Podemos actualizar esta política. Si los cambios son materiales, te lo notificaremos por
				correo electrónico o dentro de la aplicación. La fecha de "última actualización" indica
				cuándo entró en vigencia la versión actual.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">13. Contacto</h2>
			<p>
				Para cualquier consulta sobre esta política o sobre tus datos, escribinos a
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>. {BRANDING.appName} opera desde {JURISDICTION_ES}.
			</p>

			<div class="mt-12 pt-6 border-t border-[var(--border-color)] text-sm text-[var(--text-secondary)]">
				<a class="text-brand-600 dark:text-brand-400 hover:underline" href="/terms">
					Términos del Servicio
				</a>
				·
				<a class="text-brand-600 dark:text-brand-400 hover:underline" href="/">Inicio</a>
			</div>
		{:else}
			<h1 class="text-3xl font-bold mb-2">Privacy Policy</h1>
			<p class="text-sm text-[var(--text-secondary)] mb-8">
				Last updated: {EFFECTIVE_DATE}
			</p>

			<section class="mb-6">
				<p>
					This Privacy Policy describes how {BRANDING.appName} ("we", "us", or "the app")
					collects, uses, and protects the personal information of people who use our services
					("Users"). By using {BRANDING.appName} you agree to the practices described here.
				</p>
			</section>

			<h2 class="text-xl font-semibold mt-8 mb-3">1. Who we are</h2>
			<p>
				{BRANDING.appName} is a health and wellness tracking application that lets health
				professionals (nutritionists, trainers, and similar) manage patients, appointments and
				plans; and lets patients log meals, weigh-ins, exercises, goals and notes. Privacy
				questions can be sent to
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">2. Information we collect</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>
					<strong>Account information:</strong> first and last name, email, password (stored as
					a hash), gender, optional date of birth, optional phone number and optional avatar.
				</li>
				<li>
					<strong>Health and activity data:</strong> meal logs, weigh-ins, exercises, routines,
					body measurements, goals and notes that you or your professional enter into the app.
				</li>
				<li>
					<strong>Appointment information:</strong> dates, times, modality (in-person or
					online), appointment notes and status.
				</li>
				<li>
					<strong>Google Sign-In data:</strong> Google identifier, email, name and profile
					picture when you choose to sign in with Google.
				</li>
				<li>
					<strong>Google Calendar data:</strong> if you connect your Google Calendar, we store
					an access token, a refresh token, your calendar identifier, and the IDs of events we
					create on your behalf. We use this data only to create, update, or delete events that
					correspond to your {BRANDING.appName} appointments. We do not read events we did not
					create.
				</li>
				<li>
					<strong>Technical data:</strong> IP address, user agent, device identifiers and basic
					activity logs for security and diagnostics.
				</li>
				<li>
					<strong>Local storage on your device:</strong> session tokens, preferences (language,
					theme), and a data cache for offline mode.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">3. How we use your information</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>To create and administer your account, authenticate you, and keep your session.</li>
				<li>
					To provide product features: meal logging, exercise tracking, weigh-ins, appointment
					management, professional-patient communication, and so on.
				</li>
				<li>To sync your appointments with Google Calendar when you voluntarily connect it.</li>
				<li>To send notifications about your appointments, messages and account activity.</li>
				<li>To improve the product, detect errors, prevent fraud and keep the platform secure.</li>
				<li>To comply with applicable legal obligations.</li>
			</ul>
			<p class="mt-3">
				We do not use your information for third-party advertising, we do not sell it, and we do
				not share it with third parties for commercial purposes.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">4. Use of the Google Calendar scope</h2>
			<p class="mb-3">
				When you connect Google Calendar, {BRANDING.appName} requests the
				<code>https://www.googleapis.com/auth/calendar.events</code> scope. We use it exclusively
				to:
			</p>
			<ul class="list-disc pl-6 space-y-2">
				<li>Create an event in your calendar when an appointment is booked in {BRANDING.appName}.</li>
				<li>Update the event if the appointment changes.</li>
				<li>Delete the event if the appointment is cancelled.</li>
			</ul>
			<p class="mt-3">
				We do not read, modify or delete events that were not created by {BRANDING.appName}. We
				do not transfer Google data to third parties, do not use it for advertising, do not use
				it to train AI models, and do not use it for any purpose other than syncing
				appointments. {BRANDING.appName}'s use of information received from Google APIs adheres
				to the
				<a
					class="text-brand-600 dark:text-brand-400 underline"
					href="https://developers.google.com/terms/api-services-user-data-policy"
					target="_blank"
					rel="noopener noreferrer">Google API Services User Data Policy</a
				>, including the Limited Use requirements.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">5. How we share your information</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>
					<strong>With your assigned professional or assigned patients:</strong> the data needed
					for the professional-patient relationship to function.
				</li>
				<li>
					<strong>With service providers:</strong> hosting, database, email delivery, cloud
					infrastructure and authentication (Google). These providers act as data processors
					under our instructions.
				</li>
				<li><strong>When required by law:</strong> in response to valid legal process.</li>
				<li>
					<strong>To protect rights:</strong> when necessary to investigate, prevent or take
					action against illegal activity, fraud or technical issues.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">6. Data retention</h2>
			<p>
				We keep your data for as long as your account is active and as long as it is necessary to
				provide the service. You can request deletion of your account at any time by writing to
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>. Some data may be retained for additional periods to comply with legal obligations,
				resolve disputes or enforce our agreements.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">7. Your rights</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>Access the personal information we hold about you.</li>
				<li>Request correction or update of incorrect information.</li>
				<li>Request deletion of your account and associated data.</li>
				<li>Request a copy of your data in a portable format.</li>
				<li>
					Revoke the Google Calendar integration at any time, either from your settings or from
					your Google account.
				</li>
				<li>File a complaint with the data protection authority of your jurisdiction.</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">8. Security</h2>
			<p>
				We apply reasonable technical and organizational measures to protect your information:
				encryption in transit (HTTPS), password hashing, access controls, activity logs and
				periodic backups. No system is 100% secure; if we detect a material breach we will notify
				affected Users as required by law.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">9. International transfers</h2>
			<p>
				Some of our providers (for example, Google) operate servers outside Argentina. By using
				{BRANDING.appName} you understand that your data may be processed in other countries that
				may have different data-protection regimes. We take reasonable steps to ensure transfers
				are made with adequate safeguards.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">10. Minors</h2>
			<p>
				{BRANDING.appName} is not directed to children under 13. If you are a parent or legal
				guardian and believe a child in your care has provided us information, please write to
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				> and we will delete it.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">11. Cookies and local storage</h2>
			<p>
				We use browser local storage (localStorage / IndexedDB) to keep your session,
				preferences, and a data cache for offline mode. We do not use third-party tracking
				cookies for advertising.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">12. Changes to this policy</h2>
			<p>
				We may update this policy. If changes are material, we will notify you by email or in the
				app. The "last updated" date at the top indicates when the current version became
				effective.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">13. Contact</h2>
			<p>
				For any question about this policy or about your data, contact us at
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>. {BRANDING.appName} operates from {JURISDICTION_EN}.
			</p>

			<div class="mt-12 pt-6 border-t border-[var(--border-color)] text-sm text-[var(--text-secondary)]">
				<a class="text-brand-600 dark:text-brand-400 hover:underline" href="/terms">
					Terms of Service
				</a>
				·
				<a class="text-brand-600 dark:text-brand-400 hover:underline" href="/">Home</a>
			</div>
		{/if}
	</article>
</div>

<style>
	article :global(p) {
		margin-bottom: 0.75rem;
		line-height: 1.7;
	}
	article :global(li) {
		line-height: 1.6;
	}
	article :global(code) {
		font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
		font-size: 0.85em;
		padding: 0.1em 0.3em;
		border-radius: 4px;
		background: var(--bg-secondary);
	}
</style>
