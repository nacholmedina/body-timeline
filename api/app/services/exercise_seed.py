"""Exercise catalog seed data."""

from app.extensions import db
from app.models.exercise_definition import ExerciseDefinition


def seed_exercise_catalog():
    """Seed the exercise catalog with common exercises."""

    exercises = [
        # ═══════════════════════════════════════════════════════════
        # CARDIO - exercises that elevate heart rate
        # ═══════════════════════════════════════════════════════════
        {
            "name": "Running",
            "category": "cardio",
            "description": "Outdoor or treadmill running",
            "allowed_measurements": ["distance", "duration"],
        },
        {
            "name": "Walking",
            "category": "cardio",
            "description": "Walking for exercise",
            "allowed_measurements": ["distance", "duration"],
        },
        {
            "name": "Cycling",
            "category": "cardio",
            "description": "Bicycle riding, outdoor or stationary",
            "allowed_measurements": ["distance", "duration"],
        },
        {
            "name": "Swimming",
            "category": "cardio",
            "description": "Swimming laps or recreational",
            "allowed_measurements": ["distance", "duration"],
        },
        {
            "name": "Jump Rope",
            "category": "cardio",
            "description": "Skipping rope",
            "allowed_measurements": ["jumps", "duration"],
        },
        {
            "name": "Rowing",
            "category": "cardio",
            "description": "Rowing machine or boat",
            "allowed_measurements": ["distance", "duration"],
        },
        {
            "name": "Elliptical",
            "category": "cardio",
            "description": "Elliptical machine workout",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Stair Climbing",
            "category": "cardio",
            "description": "Climbing stairs or stair machine",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Dancing",
            "category": "cardio",
            "description": "Dance for exercise or recreation",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Hiking",
            "category": "cardio",
            "description": "Trail hiking",
            "allowed_measurements": ["distance", "duration"],
        },

        # ═══════════════════════════════════════════════════════════
        # STRENGTH - resistance and bodyweight exercises
        # ═══════════════════════════════════════════════════════════
        {
            "name": "Push-ups",
            "category": "strength",
            "description": "Standard push-ups",
            "allowed_measurements": ["reps", "sets"],
        },
        {
            "name": "Pull-ups",
            "category": "strength",
            "description": "Pull-up bar exercise",
            "allowed_measurements": ["reps", "sets"],
        },
        {
            "name": "Sit-ups",
            "category": "strength",
            "description": "Abdominal sit-ups",
            "allowed_measurements": ["reps", "sets"],
        },
        {
            "name": "Crunches",
            "category": "strength",
            "description": "Abdominal crunches",
            "allowed_measurements": ["reps", "sets"],
        },
        {
            "name": "Squats",
            "category": "strength",
            "description": "Bodyweight or weighted squats",
            "allowed_measurements": ["reps", "sets", "weight"],
        },
        {
            "name": "Lunges",
            "category": "strength",
            "description": "Forward, reverse, or walking lunges",
            "allowed_measurements": ["reps", "sets", "weight"],
        },
        {
            "name": "Plank",
            "category": "strength",
            "description": "Core plank hold",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Deadlift",
            "category": "strength",
            "description": "Barbell or dumbbell deadlift",
            "allowed_measurements": ["reps", "sets", "weight"],
        },
        {
            "name": "Bench Press",
            "category": "strength",
            "description": "Barbell or dumbbell bench press",
            "allowed_measurements": ["reps", "sets", "weight"],
        },
        {
            "name": "Shoulder Press",
            "category": "strength",
            "description": "Overhead press",
            "allowed_measurements": ["reps", "sets", "weight"],
        },
        {
            "name": "Bicep Curls",
            "category": "strength",
            "description": "Dumbbell or barbell curls",
            "allowed_measurements": ["reps", "sets", "weight"],
        },
        {
            "name": "Tricep Dips",
            "category": "strength",
            "description": "Parallel bar or bench dips",
            "allowed_measurements": ["reps", "sets"],
        },
        {
            "name": "Leg Press",
            "category": "strength",
            "description": "Machine leg press",
            "allowed_measurements": ["reps", "sets", "weight"],
        },
        {
            "name": "Lat Pulldown",
            "category": "strength",
            "description": "Cable lat pulldown",
            "allowed_measurements": ["reps", "sets", "weight"],
        },
        {
            "name": "Cable Rows",
            "category": "strength",
            "description": "Seated cable row",
            "allowed_measurements": ["reps", "sets", "weight"],
        },

        # ═══════════════════════════════════════════════════════════
        # SPORTS - competitive and recreational sports
        # ═══════════════════════════════════════════════════════════
        {
            "name": "Basketball",
            "category": "sports",
            "description": "Basketball game or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Soccer",
            "category": "sports",
            "description": "Soccer game or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Football",
            "category": "sports",
            "description": "American football",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Tennis",
            "category": "sports",
            "description": "Tennis match or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Volleyball",
            "category": "sports",
            "description": "Volleyball game or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Golf",
            "category": "sports",
            "description": "Golf round or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Baseball",
            "category": "sports",
            "description": "Baseball game or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Badminton",
            "category": "sports",
            "description": "Badminton match or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Table Tennis",
            "category": "sports",
            "description": "Ping pong match or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Boxing",
            "category": "sports",
            "description": "Boxing training or sparring",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Martial Arts",
            "category": "sports",
            "description": "Karate, Taekwondo, Judo, etc.",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Racquetball",
            "category": "sports",
            "description": "Racquetball match or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Squash",
            "category": "sports",
            "description": "Squash match or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Cricket",
            "category": "sports",
            "description": "Cricket match or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Rugby",
            "category": "sports",
            "description": "Rugby game or practice",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Hockey",
            "category": "sports",
            "description": "Ice or field hockey",
            "allowed_measurements": ["duration"],
        },

        # ═══════════════════════════════════════════════════════════
        # FLEXIBILITY - stretching and flexibility exercises
        # ═══════════════════════════════════════════════════════════
        {
            "name": "Yoga",
            "category": "flexibility",
            "description": "Yoga session",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Stretching",
            "category": "flexibility",
            "description": "General stretching routine",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Pilates",
            "category": "flexibility",
            "description": "Pilates session",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Tai Chi",
            "category": "flexibility",
            "description": "Tai Chi practice",
            "allowed_measurements": ["duration"],
        },

        # ═══════════════════════════════════════════════════════════
        # GENERAL - general activities and workouts
        # ═══════════════════════════════════════════════════════════
        {
            "name": "Gym Session",
            "category": "general",
            "description": "General gym workout",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Calisthenics",
            "category": "general",
            "description": "Bodyweight exercise routine",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "CrossFit",
            "category": "general",
            "description": "CrossFit WOD",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "HIIT",
            "category": "general",
            "description": "High-Intensity Interval Training",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Circuit Training",
            "category": "general",
            "description": "Circuit workout",
            "allowed_measurements": ["duration"],
        },
        {
            "name": "Other",
            "category": "general",
            "description": "Custom exercise activity",
            "allowed_measurements": ["duration", "reps", "sets", "weight", "distance", "jumps"],
        },
    ]

    created_count = 0
    for exercise_data in exercises:
        # Check if exercise already exists
        existing = ExerciseDefinition.query.filter_by(name=exercise_data["name"]).first()
        if existing:
            continue

        exercise = ExerciseDefinition(
            name=exercise_data["name"],
            category=exercise_data["category"],
            description=exercise_data["description"],
            is_system=True,
            is_active=True,
        )
        exercise.set_allowed_measurements(exercise_data["allowed_measurements"])
        db.session.add(exercise)
        created_count += 1

    db.session.commit()
    return created_count
