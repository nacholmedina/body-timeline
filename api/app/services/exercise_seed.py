"""Exercise catalog seed data — inspired by Mi Fitness (Xiaomi) exercise list."""

from app.extensions import db
from app.models.exercise_definition import ExerciseDefinition


def seed_exercise_catalog():
    """Seed the exercise catalog with a comprehensive list of exercises."""

    exercises = [
        # ═══════════════════════════════════════════════════════════
        # CARDIO — running, walking, cycling, swimming, and more
        # ═══════════════════════════════════════════════════════════
        {"name": "Outdoor Running", "category": "cardio", "description": "Running outdoors", "allowed_measurements": ["distance", "duration"]},
        {"name": "Treadmill Running", "category": "cardio", "description": "Running on a treadmill", "allowed_measurements": ["distance", "duration"]},
        {"name": "Trail Running", "category": "cardio", "description": "Running on trails and uneven terrain", "allowed_measurements": ["distance", "duration"]},
        {"name": "Interval Running", "category": "cardio", "description": "Alternating between sprinting and jogging", "allowed_measurements": ["distance", "duration"]},
        {"name": "Outdoor Walking", "category": "cardio", "description": "Walking outdoors", "allowed_measurements": ["distance", "duration"]},
        {"name": "Indoor Walking", "category": "cardio", "description": "Walking on treadmill or indoor track", "allowed_measurements": ["distance", "duration"]},
        {"name": "Power Walking", "category": "cardio", "description": "Brisk walking for fitness", "allowed_measurements": ["distance", "duration"]},
        {"name": "Nordic Walking", "category": "cardio", "description": "Walking with trekking poles", "allowed_measurements": ["distance", "duration"]},
        {"name": "Outdoor Cycling", "category": "cardio", "description": "Cycling outdoors on roads or paths", "allowed_measurements": ["distance", "duration"]},
        {"name": "Indoor Cycling", "category": "cardio", "description": "Stationary bike or spin class", "allowed_measurements": ["distance", "duration"]},
        {"name": "Mountain Biking", "category": "cardio", "description": "Off-road cycling on trails", "allowed_measurements": ["distance", "duration"]},
        {"name": "Pool Swimming", "category": "cardio", "description": "Swimming laps in a pool", "allowed_measurements": ["distance", "duration"]},
        {"name": "Open Water Swimming", "category": "cardio", "description": "Swimming in lakes, rivers, or the ocean", "allowed_measurements": ["distance", "duration"]},
        {"name": "Hiking", "category": "cardio", "description": "Hiking on trails and mountains", "allowed_measurements": ["distance", "duration"]},
        {"name": "Climbing Stairs", "category": "cardio", "description": "Climbing stairs or stair machine", "allowed_measurements": ["duration"]},
        {"name": "Rowing Machine", "category": "cardio", "description": "Indoor rowing machine workout", "allowed_measurements": ["distance", "duration"]},
        {"name": "Outdoor Rowing", "category": "cardio", "description": "Rowing on water", "allowed_measurements": ["distance", "duration"]},
        {"name": "Elliptical", "category": "cardio", "description": "Elliptical trainer machine", "allowed_measurements": ["duration"]},
        {"name": "Jump Rope", "category": "cardio", "description": "Skipping rope", "allowed_measurements": ["jumps", "duration"]},
        {"name": "Dancing", "category": "cardio", "description": "Dance-based exercise", "allowed_measurements": ["duration"]},
        {"name": "Aerobics", "category": "cardio", "description": "Aerobic exercise class", "allowed_measurements": ["duration"]},
        {"name": "Step Aerobics", "category": "cardio", "description": "Step platform aerobic workout", "allowed_measurements": ["duration"]},
        {"name": "Kickboxing", "category": "cardio", "description": "Cardio kickboxing class", "allowed_measurements": ["duration"]},
        {"name": "Zumba", "category": "cardio", "description": "Zumba dance fitness class", "allowed_measurements": ["duration"]},
        {"name": "Spinning", "category": "cardio", "description": "Indoor cycling class", "allowed_measurements": ["duration"]},
        {"name": "Roller Skating", "category": "cardio", "description": "Inline or quad roller skating", "allowed_measurements": ["distance", "duration"]},
        {"name": "Ice Skating", "category": "cardio", "description": "Skating on ice", "allowed_measurements": ["duration"]},
        {"name": "Cross-Country Skiing", "category": "cardio", "description": "Skiing across flat terrain", "allowed_measurements": ["distance", "duration"]},
        {"name": "Snowshoeing", "category": "cardio", "description": "Walking on snow with snowshoes", "allowed_measurements": ["distance", "duration"]},
        {"name": "Kayaking", "category": "cardio", "description": "Paddling a kayak", "allowed_measurements": ["distance", "duration"]},
        {"name": "Canoeing", "category": "cardio", "description": "Paddling a canoe", "allowed_measurements": ["distance", "duration"]},
        {"name": "Stand-Up Paddleboarding", "category": "cardio", "description": "Paddleboarding while standing", "allowed_measurements": ["distance", "duration"]},
        {"name": "Sprinting", "category": "cardio", "description": "Short burst high-speed running", "allowed_measurements": ["distance", "duration"]},

        # ═══════════════════════════════════════════════════════════
        # STRENGTH — weightlifting, bodyweight, and resistance
        # ═══════════════════════════════════════════════════════════
        # Chest
        {"name": "Bench Press", "category": "strength", "description": "Barbell bench press", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Incline Bench Press", "category": "strength", "description": "Incline barbell or dumbbell press", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Dumbbell Chest Press", "category": "strength", "description": "Flat dumbbell chest press", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Push-ups", "category": "strength", "description": "Standard push-ups", "allowed_measurements": ["reps", "sets"]},
        {"name": "Chest Fly", "category": "strength", "description": "Dumbbell or cable chest fly", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Dips", "category": "strength", "description": "Parallel bar dips for chest/triceps", "allowed_measurements": ["reps", "sets", "weight"]},
        # Back
        {"name": "Pull-ups", "category": "strength", "description": "Bodyweight pull-ups", "allowed_measurements": ["reps", "sets"]},
        {"name": "Chin-ups", "category": "strength", "description": "Underhand grip pull-ups", "allowed_measurements": ["reps", "sets"]},
        {"name": "Lat Pulldown", "category": "strength", "description": "Cable lat pulldown machine", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Barbell Row", "category": "strength", "description": "Bent-over barbell row", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Dumbbell Row", "category": "strength", "description": "Single-arm dumbbell row", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Cable Row", "category": "strength", "description": "Seated cable row", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Deadlift", "category": "strength", "description": "Conventional deadlift", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Romanian Deadlift", "category": "strength", "description": "Stiff-leg Romanian deadlift", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Back Extension", "category": "strength", "description": "Lower back hyperextension", "allowed_measurements": ["reps", "sets"]},
        # Shoulders
        {"name": "Overhead Press", "category": "strength", "description": "Standing or seated barbell/dumbbell press", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Lateral Raise", "category": "strength", "description": "Dumbbell side lateral raise", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Front Raise", "category": "strength", "description": "Dumbbell front raise", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Face Pull", "category": "strength", "description": "Cable face pull for rear delts", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Shrugs", "category": "strength", "description": "Barbell or dumbbell shrugs", "allowed_measurements": ["reps", "sets", "weight"]},
        # Arms
        {"name": "Bicep Curls", "category": "strength", "description": "Dumbbell or barbell curls", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Hammer Curls", "category": "strength", "description": "Neutral grip dumbbell curls", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Tricep Pushdown", "category": "strength", "description": "Cable tricep pushdown", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Skull Crushers", "category": "strength", "description": "Lying tricep extension", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Tricep Kickback", "category": "strength", "description": "Dumbbell tricep kickback", "allowed_measurements": ["reps", "sets", "weight"]},
        # Legs
        {"name": "Squats", "category": "strength", "description": "Barbell or bodyweight squats", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Front Squats", "category": "strength", "description": "Barbell front squats", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Leg Press", "category": "strength", "description": "Machine leg press", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Lunges", "category": "strength", "description": "Forward, reverse, or walking lunges", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Bulgarian Split Squat", "category": "strength", "description": "Rear foot elevated split squat", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Leg Extension", "category": "strength", "description": "Machine leg extension", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Leg Curl", "category": "strength", "description": "Machine hamstring curl", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Calf Raise", "category": "strength", "description": "Standing or seated calf raise", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Hip Thrust", "category": "strength", "description": "Barbell hip thrust for glutes", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Step-ups", "category": "strength", "description": "Weighted step-ups on a bench or box", "allowed_measurements": ["reps", "sets", "weight"]},
        # Core
        {"name": "Crunches", "category": "strength", "description": "Abdominal crunches", "allowed_measurements": ["reps", "sets"]},
        {"name": "Sit-ups", "category": "strength", "description": "Full sit-ups", "allowed_measurements": ["reps", "sets"]},
        {"name": "Plank", "category": "strength", "description": "Isometric core plank hold", "allowed_measurements": ["duration"]},
        {"name": "Side Plank", "category": "strength", "description": "Lateral plank hold", "allowed_measurements": ["duration"]},
        {"name": "Russian Twist", "category": "strength", "description": "Seated rotational core exercise", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Leg Raise", "category": "strength", "description": "Hanging or lying leg raise", "allowed_measurements": ["reps", "sets"]},
        {"name": "Mountain Climbers", "category": "strength", "description": "Dynamic plank with knee drives", "allowed_measurements": ["reps", "duration"]},
        {"name": "Ab Wheel Rollout", "category": "strength", "description": "Ab wheel rollout exercise", "allowed_measurements": ["reps", "sets"]},
        # Compound / Olympic
        {"name": "Clean and Jerk", "category": "strength", "description": "Olympic weightlifting clean and jerk", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Snatch", "category": "strength", "description": "Olympic weightlifting snatch", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Kettlebell Swing", "category": "strength", "description": "Two-hand kettlebell swing", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Turkish Get-up", "category": "strength", "description": "Full Turkish get-up with kettlebell", "allowed_measurements": ["reps", "sets", "weight"]},
        {"name": "Farmer's Walk", "category": "strength", "description": "Carrying heavy weights while walking", "allowed_measurements": ["distance", "duration", "weight"]},
        {"name": "Battle Ropes", "category": "strength", "description": "Heavy rope wave exercise", "allowed_measurements": ["duration"]},

        # ═══════════════════════════════════════════════════════════
        # SPORTS — competitive and recreational sports
        # ═══════════════════════════════════════════════════════════
        # Ball sports
        {"name": "Soccer", "category": "sports", "description": "Association football match or practice", "allowed_measurements": ["duration"]},
        {"name": "Basketball", "category": "sports", "description": "Basketball game or practice", "allowed_measurements": ["duration"]},
        {"name": "Volleyball", "category": "sports", "description": "Indoor or beach volleyball", "allowed_measurements": ["duration"]},
        {"name": "Tennis", "category": "sports", "description": "Tennis match or practice", "allowed_measurements": ["duration"]},
        {"name": "Badminton", "category": "sports", "description": "Badminton match or practice", "allowed_measurements": ["duration"]},
        {"name": "Table Tennis", "category": "sports", "description": "Table tennis / ping pong", "allowed_measurements": ["duration"]},
        {"name": "Padel", "category": "sports", "description": "Padel tennis match or practice", "allowed_measurements": ["duration"]},
        {"name": "Squash", "category": "sports", "description": "Squash match or practice", "allowed_measurements": ["duration"]},
        {"name": "Racquetball", "category": "sports", "description": "Racquetball match or practice", "allowed_measurements": ["duration"]},
        {"name": "Handball", "category": "sports", "description": "Handball game or practice", "allowed_measurements": ["duration"]},
        {"name": "Baseball", "category": "sports", "description": "Baseball game or practice", "allowed_measurements": ["duration"]},
        {"name": "Softball", "category": "sports", "description": "Softball game or practice", "allowed_measurements": ["duration"]},
        {"name": "Cricket", "category": "sports", "description": "Cricket match or practice", "allowed_measurements": ["duration"]},
        {"name": "Rugby", "category": "sports", "description": "Rugby game or practice", "allowed_measurements": ["duration"]},
        {"name": "American Football", "category": "sports", "description": "American football game or practice", "allowed_measurements": ["duration"]},
        {"name": "Golf", "category": "sports", "description": "Golf round or practice", "allowed_measurements": ["duration"]},
        {"name": "Field Hockey", "category": "sports", "description": "Field hockey game or practice", "allowed_measurements": ["duration"]},
        {"name": "Ice Hockey", "category": "sports", "description": "Ice hockey game or practice", "allowed_measurements": ["duration"]},
        {"name": "Lacrosse", "category": "sports", "description": "Lacrosse game or practice", "allowed_measurements": ["duration"]},
        {"name": "Water Polo", "category": "sports", "description": "Water polo match or practice", "allowed_measurements": ["duration"]},
        # Combat sports
        {"name": "Boxing", "category": "sports", "description": "Boxing training or sparring", "allowed_measurements": ["duration"]},
        {"name": "Muay Thai", "category": "sports", "description": "Thai boxing training", "allowed_measurements": ["duration"]},
        {"name": "MMA", "category": "sports", "description": "Mixed martial arts training", "allowed_measurements": ["duration"]},
        {"name": "Judo", "category": "sports", "description": "Judo practice or competition", "allowed_measurements": ["duration"]},
        {"name": "Karate", "category": "sports", "description": "Karate practice or competition", "allowed_measurements": ["duration"]},
        {"name": "Taekwondo", "category": "sports", "description": "Taekwondo practice or competition", "allowed_measurements": ["duration"]},
        {"name": "Brazilian Jiu-Jitsu", "category": "sports", "description": "BJJ training or rolling", "allowed_measurements": ["duration"]},
        {"name": "Wrestling", "category": "sports", "description": "Wrestling practice or competition", "allowed_measurements": ["duration"]},
        {"name": "Fencing", "category": "sports", "description": "Fencing practice or competition", "allowed_measurements": ["duration"]},
        # Adventure / outdoor
        {"name": "Rock Climbing", "category": "sports", "description": "Indoor or outdoor rock climbing", "allowed_measurements": ["duration"]},
        {"name": "Bouldering", "category": "sports", "description": "Low-wall climbing without ropes", "allowed_measurements": ["duration"]},
        {"name": "Surfing", "category": "sports", "description": "Ocean surfing", "allowed_measurements": ["duration"]},
        {"name": "Skateboarding", "category": "sports", "description": "Skateboarding session", "allowed_measurements": ["duration"]},
        {"name": "Downhill Skiing", "category": "sports", "description": "Alpine skiing", "allowed_measurements": ["duration"]},
        {"name": "Snowboarding", "category": "sports", "description": "Snowboarding on slopes", "allowed_measurements": ["duration"]},
        {"name": "Horseback Riding", "category": "sports", "description": "Equestrian riding", "allowed_measurements": ["duration"]},
        {"name": "Archery", "category": "sports", "description": "Archery practice or competition", "allowed_measurements": ["duration"]},
        {"name": "Triathlon", "category": "sports", "description": "Swim-bike-run competition", "allowed_measurements": ["distance", "duration"]},
        {"name": "Sailing", "category": "sports", "description": "Sailing a boat", "allowed_measurements": ["duration"]},
        {"name": "Scuba Diving", "category": "sports", "description": "Scuba diving session", "allowed_measurements": ["duration"]},
        {"name": "Snorkeling", "category": "sports", "description": "Snorkeling session", "allowed_measurements": ["duration"]},
        # Other sports
        {"name": "Bowling", "category": "sports", "description": "Ten-pin bowling", "allowed_measurements": ["duration"]},
        {"name": "Frisbee", "category": "sports", "description": "Disc sports / ultimate frisbee", "allowed_measurements": ["duration"]},
        {"name": "Dodgeball", "category": "sports", "description": "Dodgeball game", "allowed_measurements": ["duration"]},
        {"name": "Cheerleading", "category": "sports", "description": "Cheerleading practice or performance", "allowed_measurements": ["duration"]},
        {"name": "Gymnastics", "category": "sports", "description": "Artistic or rhythmic gymnastics", "allowed_measurements": ["duration"]},
        {"name": "Trampoline", "category": "sports", "description": "Trampoline jumping", "allowed_measurements": ["duration"]},
        {"name": "Parkour", "category": "sports", "description": "Freerunning and parkour", "allowed_measurements": ["duration"]},

        # ═══════════════════════════════════════════════════════════
        # FLEXIBILITY — stretching, yoga, mobility
        # ═══════════════════════════════════════════════════════════
        {"name": "Yoga", "category": "flexibility", "description": "Yoga session", "allowed_measurements": ["duration"]},
        {"name": "Vinyasa Yoga", "category": "flexibility", "description": "Flow-based dynamic yoga", "allowed_measurements": ["duration"]},
        {"name": "Hot Yoga", "category": "flexibility", "description": "Yoga in a heated room (Bikram-style)", "allowed_measurements": ["duration"]},
        {"name": "Yin Yoga", "category": "flexibility", "description": "Slow-paced deep stretch yoga", "allowed_measurements": ["duration"]},
        {"name": "Stretching", "category": "flexibility", "description": "General stretching routine", "allowed_measurements": ["duration"]},
        {"name": "Dynamic Stretching", "category": "flexibility", "description": "Active movement-based stretching", "allowed_measurements": ["duration"]},
        {"name": "Static Stretching", "category": "flexibility", "description": "Holding stretch positions", "allowed_measurements": ["duration"]},
        {"name": "Pilates", "category": "flexibility", "description": "Pilates mat or reformer workout", "allowed_measurements": ["duration"]},
        {"name": "Tai Chi", "category": "flexibility", "description": "Tai Chi practice", "allowed_measurements": ["duration"]},
        {"name": "Foam Rolling", "category": "flexibility", "description": "Self-myofascial release with foam roller", "allowed_measurements": ["duration"]},
        {"name": "Mobility Work", "category": "flexibility", "description": "Joint mobility and movement drills", "allowed_measurements": ["duration"]},
        {"name": "Barre", "category": "flexibility", "description": "Ballet-inspired fitness class", "allowed_measurements": ["duration"]},
        {"name": "Qigong", "category": "flexibility", "description": "Breathing and movement meditation practice", "allowed_measurements": ["duration"]},

        # ═══════════════════════════════════════════════════════════
        # GENERAL — mixed training, classes, and other activities
        # ═══════════════════════════════════════════════════════════
        {"name": "Gym Session", "category": "general", "description": "General gym workout", "allowed_measurements": ["duration"]},
        {"name": "HIIT", "category": "general", "description": "High-Intensity Interval Training", "allowed_measurements": ["duration"]},
        {"name": "CrossFit", "category": "general", "description": "CrossFit WOD", "allowed_measurements": ["duration"]},
        {"name": "Calisthenics", "category": "general", "description": "Bodyweight exercise routine", "allowed_measurements": ["duration"]},
        {"name": "Circuit Training", "category": "general", "description": "Station-based circuit workout", "allowed_measurements": ["duration"]},
        {"name": "Functional Training", "category": "general", "description": "Functional movement-based workout", "allowed_measurements": ["duration"]},
        {"name": "Boot Camp", "category": "general", "description": "Military-style group fitness class", "allowed_measurements": ["duration"]},
        {"name": "TRX / Suspension", "category": "general", "description": "Suspension trainer workout", "allowed_measurements": ["duration"]},
        {"name": "Resistance Band Workout", "category": "general", "description": "Exercise with elastic resistance bands", "allowed_measurements": ["duration"]},
        {"name": "Tabata", "category": "general", "description": "20 sec work / 10 sec rest intervals", "allowed_measurements": ["duration"]},
        {"name": "Plyometrics", "category": "general", "description": "Explosive jump training", "allowed_measurements": ["duration", "reps"]},
        {"name": "Warm-up", "category": "general", "description": "Pre-workout warm-up routine", "allowed_measurements": ["duration"]},
        {"name": "Cool-down", "category": "general", "description": "Post-workout cool-down routine", "allowed_measurements": ["duration"]},
        {"name": "Active Recovery", "category": "general", "description": "Light activity on rest days", "allowed_measurements": ["duration"]},
        {"name": "Physical Therapy", "category": "general", "description": "Rehabilitation exercises", "allowed_measurements": ["duration"]},
        {"name": "Meditation", "category": "general", "description": "Mindfulness or guided meditation", "allowed_measurements": ["duration"]},
        {"name": "Breathing Exercises", "category": "general", "description": "Focused breathing and relaxation", "allowed_measurements": ["duration"]},
        {"name": "Other", "category": "general", "description": "Custom exercise activity", "allowed_measurements": ["duration", "reps", "sets", "weight", "distance", "jumps"]},
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
