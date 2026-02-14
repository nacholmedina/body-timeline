export const es = {
	app: {
		name: 'Body Timeline',
		tagline: 'Seguí tu progreso físico',
		description: 'Seguí tu progreso físico, comidas, pesajes, metas, entrenamientos y notas profesionales.'
	},
	nav: {
		dashboard: 'Panel',
		meals: 'Comidas',
		weighIns: 'Pesajes',
		goals: 'Metas',
		workouts: 'Entrenamientos',
		notifications: 'Notificaciones',
		appointments: 'Turnos',
		profile: 'Perfil',
		settings: 'Configuración',
		logout: 'Cerrar sesión'
	},
	auth: {
		login: 'Iniciar sesión',
		register: 'Registrarse',
		email: 'Email',
		password: 'Contraseña',
		firstName: 'Nombre',
		lastName: 'Apellido',
		loginTitle: 'Bienvenido',
		loginSubtitle: 'Iniciá sesión en tu cuenta',
		registerTitle: 'Crear cuenta',
		registerSubtitle: 'Comenzá a seguir tu progreso',
		noAccount: '¿No tenés cuenta?',
		hasAccount: '¿Ya tenés cuenta?',
		forgotPassword: '¿Olvidaste tu contraseña?'
	},
	dashboard: {
		title: 'Panel',
		welcome: 'Bienvenido',
		mealsThisMonth: 'Comidas este mes',
		workoutsThisMonth: 'Entrenamientos este mes',
		goalsCompleted: 'Metas completadas',
		nextAppointment: 'Próximo turno',
		noAppointment: 'Sin turnos próximos',
		weightOverTime: 'Peso a lo largo del tiempo',
		weeklyActivity: 'Actividad semanal',
		professionalNotes: 'Notas del profesional',
		news: 'Noticias y consejos',
		noNotes: 'Sin notas nuevas',
		newsHydration: 'Mantenete hidratado',
		newsHydrationBody: 'Tomá al menos 8 vasos de agua al día para un rendimiento óptimo.',
		newsRest: 'Los días de descanso importan',
		newsRestBody: 'La recuperación es tan importante como el entrenamiento. Dale tiempo a tu cuerpo para sanar.',
		newsMealPrep: 'Consejos de meal prep',
		newsMealPrepBody: 'Preparar las comidas con anticipación ayuda a mantener la consistencia con los objetivos nutricionales.'
	},
	meals: {
		title: 'Comidas',
		addMeal: 'Agregar comida',
		description: 'Descripción',
		eatenAt: 'Comido a las',
		notes: 'Notas',
		photos: 'Fotos',
		noMeals: 'Aún no se registraron comidas',
		draftOffline: 'Borrador (sin conexión)',
		addPhoto: 'Agregar foto',
		removePhoto: 'Quitar'
	},
	weighIns: {
		title: 'Pesajes',
		addWeighIn: 'Agregar pesaje',
		weight: 'Peso (kg)',
		recordedAt: 'Registrado el',
		noWeighIns: 'Aún no hay pesajes'
	},
	goals: {
		title: 'Metas',
		addGoal: 'Agregar meta',
		goalTitle: 'Título de la meta',
		period: 'Período',
		weekly: 'Semanal',
		monthly: 'Mensual',
		yearly: 'Anual',
		targetDate: 'Fecha objetivo',
		completed: 'Completada',
		pending: 'Pendiente',
		noGoals: 'Aún no se definieron metas'
	},
	workouts: {
		title: 'Entrenamientos',
		addWorkout: 'Agregar entrenamiento',
		startTime: 'Hora de inicio',
		endTime: 'Hora de fin',
		exercises: 'Ejercicios',
		noWorkouts: 'Aún no se registraron entrenamientos',
		exercise: 'Ejercicio'
	},
	notifications: {
		title: 'Notificaciones',
		markRead: 'Marcar como leída',
		noNotifications: 'Sin notificaciones',
		createNote: 'Crear nota',
		noteTitle: 'Título',
		noteMessage: 'Mensaje',
		patientIds: 'IDs de pacientes (separados por coma)',
		send: 'Enviar'
	},
	appointments: {
		title: 'Turnos',
		noAppointments: 'Sin turnos agendados',
		scheduled: 'Agendado',
		completed: 'Completado',
		cancelled: 'Cancelado',
		new: 'Nuevo',
		upcoming: 'Próximos',
		patientId: 'ID del paciente',
		appointmentTitle: 'Título',
		dateTime: 'Fecha y hora',
		duration: 'Duración (min)'
	},
	roles: {
		patient: 'Paciente',
		professional: 'Profesional',
		devadmin: 'Admin'
	},
	profile: {
		title: 'Perfil',
		editProfile: 'Editar perfil',
		bio: 'Bio',
		phone: 'Teléfono',
		dateOfBirth: 'Fecha de nacimiento',
		height: 'Altura (cm)'
	},
	settings: {
		title: 'Configuración',
		theme: 'Tema',
		language: 'Idioma',
		dark: 'Oscuro',
		light: 'Claro'
	},
	common: {
		save: 'Guardar',
		cancel: 'Cancelar',
		delete: 'Eliminar',
		edit: 'Editar',
		loading: 'Cargando...',
		error: 'Ocurrió un error',
		success: 'Éxito',
		confirm: 'Confirmar',
		back: 'Volver',
		noData: 'No hay datos disponibles',
		offline: 'Estás sin conexión',
		syncing: 'Sincronizando...',
		syncComplete: 'Sincronización completa',
		filter: 'Filtrar',
		all: 'Todo',
		day: 'Día',
		week: 'Semana',
		month: 'Mes',
		year: 'Año'
	}
} as const;
