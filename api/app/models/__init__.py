from app.models.user import User, Profile, ProfessionalPatient
from app.models.meal import Meal, MealPhoto
from app.models.weigh_in import WeighIn
from app.models.goal import Goal
# Old models - commenting out to avoid conflicts with new models
# from app.models.exercise import Exercise, ExerciseRequest as OldExerciseRequest
# from app.models.workout import Workout, WorkoutItem, WorkoutPhoto
from app.models.notification import Notification, NotificationRecipient
from app.models.appointment import Appointment
from app.models.availability import ProfessionalAvailability, AvailabilityOverride

# New exercise tracking models
from app.models.exercise_definition import ExerciseDefinition
from app.models.exercise_log import ExerciseLog, ExercisePhoto
from app.models.exercise_request import ExerciseRequest

__all__ = [
    "User", "Profile", "ProfessionalPatient",
    "Meal", "MealPhoto",
    "WeighIn",
    "Goal",
    # Old models (commented out - tables will be dropped in migration)
    # "Exercise", "OldExerciseRequest",
    # "Workout", "WorkoutItem", "WorkoutPhoto",
    "Notification", "NotificationRecipient",
    "Appointment",
    "ProfessionalAvailability", "AvailabilityOverride",
    # New exercise tracking models
    "ExerciseDefinition",
    "ExerciseLog", "ExercisePhoto",
    "ExerciseRequest",
]
