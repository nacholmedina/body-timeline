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
	<title>{$locale === 'es' ? 'Términos del Servicio' : 'Terms of Service'} — {BRANDING.appName}</title>
	<meta
		name="description"
		content={$locale === 'es'
			? 'Términos del servicio de Wellvio: condiciones de uso, responsabilidades y limitaciones.'
			: 'Wellvio terms of service: conditions of use, responsibilities and limitations.'}
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
			<h1 class="text-3xl font-bold mb-2">Términos del Servicio</h1>
			<p class="text-sm text-[var(--text-secondary)] mb-8">
				Última actualización: {EFFECTIVE_DATE}
			</p>

			<section class="mb-6">
				<p>
					Estos Términos del Servicio (los "Términos") regulan el uso de {BRANDING.appName} (la
					"Aplicación", "nosotros" o "el Servicio"). Al crear una cuenta o utilizar el Servicio,
					aceptás estos Términos. Si no estás de acuerdo, por favor no uses la Aplicación.
				</p>
			</section>

			<h2 class="text-xl font-semibold mt-8 mb-3">1. Descripción del Servicio</h2>
			<p>
				{BRANDING.appName} es una herramienta digital que permite a profesionales de la salud
				gestionar pacientes, turnos y planes; y a los pacientes registrar comidas, pesajes,
				ejercicios, objetivos, mediciones y notas. La Aplicación facilita la comunicación entre
				profesional y paciente y la reserva de turnos. {BRANDING.appName} es un proveedor de
				software; no presta servicios de salud.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">2. Aviso médico importante</h2>
			<p>
				{BRANDING.appName} no brinda diagnósticos, tratamientos ni consejos médicos. Cualquier
				información mostrada en la Aplicación, incluidos planes, recomendaciones nutricionales,
				rutinas o notas, proviene del profesional asignado al paciente o del propio paciente, y
				debe entenderse en el contexto de la relación profesional-paciente correspondiente. Ante
				cualquier emergencia médica, comunicate con los servicios de emergencia locales. No
				demores la consulta con un profesional habilitado por confiar en información proveniente
				de la Aplicación.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">3. Cuentas de usuario</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>
					Para usar la mayoría de las funciones tenés que crear una cuenta. Sos responsable de
					mantener la confidencialidad de tus credenciales.
				</li>
				<li>
					La información que provees al registrarte debe ser veraz, exacta y mantenerse
					actualizada.
				</li>
				<li>
					Tenés que tener al menos 13 años para crear una cuenta. Los menores deberán contar con
					el consentimiento de su padre, madre o tutor.
				</li>
				<li>
					Sos responsable de toda la actividad realizada bajo tu cuenta. Notificanos
					inmediatamente si detectás un uso no autorizado.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">4. Uso aceptable</h2>
			<p class="mb-3">No podés utilizar el Servicio para:</p>
			<ul class="list-disc pl-6 space-y-2">
				<li>Violar leyes aplicables o derechos de terceros.</li>
				<li>Subir contenido ilegal, ofensivo, difamatorio o que infrinja derechos de autor.</li>
				<li>
					Intentar acceder sin autorización a cuentas, sistemas o datos de otros usuarios.
				</li>
				<li>
					Ejecutar pruebas de seguridad, escaneos automatizados o ingeniería inversa sin nuestro
					permiso explícito.
				</li>
				<li>
					Usar la Aplicación para enviar spam, distribuir malware o realizar actividades
					fraudulentas.
				</li>
				<li>
					Interferir con el funcionamiento del Servicio, los servidores o la infraestructura
					subyacente.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">5. Reservas y turnos</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>
					Los profesionales son responsables de configurar correctamente su disponibilidad,
					incluida la modalidad (presencial u online) y la duración de los turnos.
				</li>
				<li>
					Los pacientes son responsables de presentarse al turno reservado o de cancelarlo con
					antelación cuando corresponda. Las políticas de cancelación las define cada
					profesional.
				</li>
				<li>
					{BRANDING.appName} no garantiza la disponibilidad de profesionales y no es responsable
					de cancelaciones o ausencias.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">6. Integración con Google Calendar</h2>
			<p>
				La conexión con Google Calendar es opcional. Si la activás, autorizás a {BRANDING.appName}
				a crear, actualizar y eliminar eventos en tu calendario que correspondan a turnos
				gestionados desde la Aplicación. Podés revocar esta autorización en cualquier momento
				desde tu configuración o desde tu cuenta de Google. Eliminar la conexión deshabilita la
				sincronización futura, pero no elimina los eventos ya creados.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">7. Contenido del usuario</h2>
			<p>
				Conservás los derechos sobre la información que cargás en la Aplicación (notas, fotos,
				mediciones, planes, etc.). Al cargar contenido nos otorgás una licencia limitada,
				gratuita y no exclusiva para almacenarlo, procesarlo y mostrarlo a quienes corresponda
				(por ejemplo, tu profesional asignado o tus pacientes asignados) con el único fin de
				prestarte el Servicio. Sos responsable del contenido que cargás y de tener los derechos
				necesarios para hacerlo.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">8. Propiedad intelectual</h2>
			<p>
				El software, el diseño, los logos y cualquier otro material de {BRANDING.appName} son
				propiedad de {BRANDING.appName} o de sus licenciantes y están protegidos por leyes de
				propiedad intelectual. No te otorgamos ninguna licencia ni derecho sobre estos elementos
				salvo el necesario para usar la Aplicación según estos Términos.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">9. Disponibilidad del Servicio</h2>
			<p>
				Trabajamos para que el Servicio esté disponible las 24 horas, pero no garantizamos un
				funcionamiento ininterrumpido o libre de errores. Podemos suspender o modificar el
				Servicio para realizar mantenimiento, actualizaciones o por razones de seguridad.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">10. Suspensión y terminación</h2>
			<p>
				Podemos suspender o cancelar tu cuenta si incumplís estos Términos, si realizás un uso
				abusivo de la Aplicación, o si lo exige la ley. Vos podés cancelar tu cuenta en cualquier
				momento solicitando la eliminación a
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">11. Renuncia de garantías</h2>
			<p>
				En la máxima medida permitida por la ley, el Servicio se ofrece "tal cual" y "según
				disponibilidad", sin garantías de ningún tipo, expresas o implícitas, incluidas las
				garantías de comerciabilidad, idoneidad para un fin particular, exactitud o no
				infracción.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">12. Limitación de responsabilidad</h2>
			<p>
				En la máxima medida permitida por la ley, {BRANDING.appName} y sus titulares no serán
				responsables por daños indirectos, incidentales, especiales, punitivos o consecuentes,
				ni por la pérdida de datos, beneficios o reputación derivados del uso o la imposibilidad
				de uso del Servicio. Nuestra responsabilidad agregada por cualquier reclamo relacionado
				con el Servicio no superará el monto que hayas pagado a {BRANDING.appName} en los doce
				(12) meses anteriores al hecho que originó el reclamo, o cien (100) dólares
				estadounidenses, lo que sea mayor.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">13. Indemnidad</h2>
			<p>
				Aceptás indemnizar y mantener indemne a {BRANDING.appName} de cualquier reclamo, daño o
				gasto (incluidos honorarios de abogados) que surja de tu uso de la Aplicación, del
				incumplimiento de estos Términos o de la violación de derechos de terceros.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">14. Modificaciones</h2>
			<p>
				Podemos modificar estos Términos en cualquier momento. Los cambios materiales serán
				notificados por correo electrónico o dentro de la Aplicación con anticipación razonable.
				Si seguís usando el Servicio luego de la entrada en vigencia de los nuevos Términos, se
				considerará que los aceptás.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">15. Ley aplicable y jurisdicción</h2>
			<p>
				Estos Términos se rigen por las leyes de la República Argentina. Cualquier controversia
				derivada de estos Términos o del uso del Servicio se someterá a los tribunales
				competentes de {JURISDICTION_ES}.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">16. Contacto</h2>
			<p>
				Para consultas sobre estos Términos podés escribirnos a
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>.
			</p>

			<div class="mt-12 pt-6 border-t border-[var(--border-color)] text-sm text-[var(--text-secondary)]">
				<a class="text-brand-600 dark:text-brand-400 hover:underline" href="/privacy">
					Política de Privacidad
				</a>
				·
				<a class="text-brand-600 dark:text-brand-400 hover:underline" href="/">Inicio</a>
			</div>
		{:else}
			<h1 class="text-3xl font-bold mb-2">Terms of Service</h1>
			<p class="text-sm text-[var(--text-secondary)] mb-8">
				Last updated: {EFFECTIVE_DATE}
			</p>

			<section class="mb-6">
				<p>
					These Terms of Service (the "Terms") govern the use of {BRANDING.appName} (the "App",
					"we", or "the Service"). By creating an account or using the Service, you accept
					these Terms. If you do not agree, please do not use the App.
				</p>
			</section>

			<h2 class="text-xl font-semibold mt-8 mb-3">1. Description of the Service</h2>
			<p>
				{BRANDING.appName} is a digital tool that lets health professionals manage patients,
				appointments and plans, and lets patients log meals, weigh-ins, exercises, goals,
				measurements and notes. The App facilitates communication between professional and
				patient and appointment booking. {BRANDING.appName} is a software provider; it does not
				provide healthcare services.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">2. Important medical notice</h2>
			<p>
				{BRANDING.appName} does not provide diagnoses, treatment or medical advice. Any
				information shown in the App, including plans, nutritional recommendations, routines or
				notes, comes from the professional assigned to the patient or from the patient
				themselves, and must be understood within the scope of that professional-patient
				relationship. In a medical emergency, contact local emergency services. Do not delay
				seeking advice from a licensed professional based on information from the App.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">3. User accounts</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>
					Most features require an account. You are responsible for keeping your credentials
					confidential.
				</li>
				<li>The information you provide on registration must be true, accurate and kept up to date.</li>
				<li>
					You must be at least 13 years old to create an account. Minors must have consent from
					a parent or legal guardian.
				</li>
				<li>
					You are responsible for all activity carried out under your account. Notify us
					immediately if you detect unauthorized use.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">4. Acceptable use</h2>
			<p class="mb-3">You may not use the Service to:</p>
			<ul class="list-disc pl-6 space-y-2">
				<li>Violate applicable laws or third-party rights.</li>
				<li>Upload illegal, offensive, defamatory or copyright-infringing content.</li>
				<li>Attempt unauthorized access to other users' accounts, systems or data.</li>
				<li>Run security tests, automated scans or reverse engineering without our explicit consent.</li>
				<li>Use the App to send spam, distribute malware or carry out fraudulent activity.</li>
				<li>Interfere with the operation of the Service, servers or underlying infrastructure.</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">5. Bookings and appointments</h2>
			<ul class="list-disc pl-6 space-y-2">
				<li>
					Professionals are responsible for correctly configuring their availability, including
					modality (in-person or online) and appointment duration.
				</li>
				<li>
					Patients are responsible for showing up to booked appointments or cancelling them in
					advance where applicable. Cancellation policies are defined by each professional.
				</li>
				<li>
					{BRANDING.appName} does not guarantee professional availability and is not responsible
					for cancellations or no-shows.
				</li>
			</ul>

			<h2 class="text-xl font-semibold mt-8 mb-3">6. Google Calendar integration</h2>
			<p>
				Connecting Google Calendar is optional. If you enable it, you authorize {BRANDING.appName}
				to create, update and delete events on your calendar that correspond to appointments
				managed in the App. You can revoke this authorization at any time from your settings or
				from your Google account. Removing the connection disables future syncing but does not
				delete events that have already been created.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">7. User content</h2>
			<p>
				You retain rights to the information you upload to the App (notes, photos, measurements,
				plans, etc.). By uploading content you grant us a limited, royalty-free, non-exclusive
				license to store, process and display it to those who need to see it (for example, your
				assigned professional or your assigned patients) for the sole purpose of providing the
				Service. You are responsible for the content you upload and for having the necessary
				rights to do so.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">8. Intellectual property</h2>
			<p>
				The software, design, logos and any other material of {BRANDING.appName} are owned by
				{BRANDING.appName} or its licensors and are protected by intellectual property laws. We
				grant you no license or right over these elements other than what is necessary to use
				the App according to these Terms.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">9. Service availability</h2>
			<p>
				We work to keep the Service available 24/7 but do not guarantee uninterrupted or
				error-free operation. We may suspend or modify the Service to perform maintenance,
				updates or for security reasons.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">10. Suspension and termination</h2>
			<p>
				We may suspend or cancel your account if you breach these Terms, abuse the App, or where
				required by law. You may cancel your account at any time by requesting deletion at
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">11. Disclaimer of warranties</h2>
			<p>
				To the maximum extent permitted by law, the Service is provided "as is" and "as
				available", without warranties of any kind, express or implied, including warranties of
				merchantability, fitness for a particular purpose, accuracy or non-infringement.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">12. Limitation of liability</h2>
			<p>
				To the maximum extent permitted by law, {BRANDING.appName} and its owners shall not be
				liable for indirect, incidental, special, punitive or consequential damages, nor for
				loss of data, profits or reputation arising from use or inability to use the Service.
				Our aggregate liability for any claim related to the Service shall not exceed the
				amount you have paid {BRANDING.appName} in the twelve (12) months preceding the event
				giving rise to the claim, or one hundred (100) US dollars, whichever is greater.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">13. Indemnification</h2>
			<p>
				You agree to indemnify and hold harmless {BRANDING.appName} from any claim, damage or
				expense (including legal fees) arising from your use of the App, your breach of these
				Terms or your violation of third-party rights.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">14. Modifications</h2>
			<p>
				We may modify these Terms at any time. Material changes will be communicated by email or
				inside the App with reasonable advance notice. Continuing to use the Service after the
				new Terms take effect constitutes acceptance.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">15. Governing law and jurisdiction</h2>
			<p>
				These Terms are governed by the laws of Argentina. Any controversy arising from these
				Terms or the use of the Service shall be submitted to the competent courts of {JURISDICTION_EN}.
			</p>

			<h2 class="text-xl font-semibold mt-8 mb-3">16. Contact</h2>
			<p>
				For questions about these Terms, contact us at
				<a class="text-brand-600 dark:text-brand-400 underline" href="mailto:{CONTACT_EMAIL}"
					>{CONTACT_EMAIL}</a
				>.
			</p>

			<div class="mt-12 pt-6 border-t border-[var(--border-color)] text-sm text-[var(--text-secondary)]">
				<a class="text-brand-600 dark:text-brand-400 hover:underline" href="/privacy">
					Privacy Policy
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
</style>
