import Foundation

/// Serves the SPEC §2.4 seed data as raw JSON when `Config.useMock` is true, so the iOS app
/// runs (and exercises the real decoders) before the backend is up.
/// ponytail: static fixtures; mutations return plausible JSON but don't change later GETs.
enum MockAPIClient {
    static func respond(_ method: String, _ path: String, _ body: Data?) throws -> Data {
        let route = path.split(separator: "?").first.map(String.init) ?? path
        let json: String
        switch (method, route) {
        case ("GET", "/profile"), ("POST", "/profile"): json = profile
        case ("GET", "/today"): json = today
        case ("GET", "/workouts"): json = "[\(doneWorkouts), \(upperB)]"
        case ("GET", _) where route.hasPrefix("/workouts/"): json = upperB
        case ("POST", _) where route.hasPrefix("/workouts/"): json = upperB
        case ("POST", _) where route.hasPrefix("/exercises/"),
             ("PATCH", _) where route.hasPrefix("/sets/"):
            json = #"{"id": 99, "exercise_id": 1, "set_index": 5, "kg": 75.0, "reps": 8, "is_warmup": false, "done": true}"#
        case ("GET", "/food"): json = food
        case ("POST", "/food"):
            json = #"{"id": 99, "date": "2026-10-03", "meal": "dinner", "name": "Salmon, rice & broccoli", "quantity": "1 plate", "kcal": 780.0, "protein_g": 48.0, "carbs_g": 80.0, "fat_g": 26.0, "source": "coach"}"#
        case ("DELETE", _): json = #"{"ok": true}"#
        case ("GET", "/goals"): json = goals
        case ("GET", "/diet-plans"): json = "[]"
        case ("GET", "/chat/history"): json = history
        case ("POST", "/chat"):
            json = #"{"reply": "Mock mode is on, so I can't think yet. Set Config.useMock = false and start the backend.", "cards": []}"#
        default: throw APIError(status: 404, body: "mock: no route for \(method) \(path)")
        }
        return Data(json.utf8)
    }

    static let profile = #"""
    {"id": 1, "name": "Agam", "height_cm": 180.0, "weight_kg": 74.6, "age": 21, "sex": "male",
     "kcal_target": 2450, "protein_g": 160, "carbs_g": 260, "fat_g": 75, "bmi": 23.0, "bmi_category": "Normal"}
    """#

    static let today = #"""
    {"date": "2026-10-03",
     "kcal": {"target": 2450, "eaten": 1620, "left": 830},
     "macros": {"protein": {"eaten": 124, "target": 160}, "carbs": {"eaten": 172, "target": 260}, "fat": {"eaten": 48, "target": 75}},
     "bmi": {"value": 23.0, "category": "Normal"},
     "weight_kg": 74.6,
     "week": {"sessions_done": 3, "sessions_target": 4, "days": [true, true, false, true, false, false, false]},
     "next_workout": {"id": 4, "name": "Upper B — Volume", "exercise_count": 4, "est_minutes": 55},
     "coach_tip": "36 g protein to go. A salmon rice bowl for dinner closes it at 780 kcal."}
    """#

    static let doneWorkouts = #"""
    {"id": 1, "name": "Upper A — Strength", "day_label": "MON", "notes": null, "status": "done", "started_at": "2026-09-28T18:30:00", "finished_at": "2026-09-28T19:30:00", "plan_id": 1, "exercises": []},
    {"id": 2, "name": "Lower A", "day_label": "TUE", "notes": null, "status": "done", "started_at": "2026-09-29T18:30:00", "finished_at": "2026-09-29T19:25:00", "plan_id": 1, "exercises": []},
    {"id": 3, "name": "Lower B", "day_label": "THU", "notes": null, "status": "done", "started_at": "2026-10-01T18:30:00", "finished_at": "2026-10-01T19:20:00", "plan_id": 1, "exercises": []}
    """#

    static let upperB = #"""
    {"id": 4, "name": "Upper B — Volume", "day_label": "SAT", "notes": null, "status": "planned", "started_at": null, "finished_at": null, "plan_id": 1,
     "exercises": [
      {"id": 1, "workout_id": 4, "name": "Bench Press", "position": 0, "target_sets": 4, "target_reps": 8, "target_kg": 75.0, "sets": [
        {"id": 1, "exercise_id": 1, "set_index": 0, "kg": 75.0, "reps": 8, "is_warmup": false, "done": false},
        {"id": 2, "exercise_id": 1, "set_index": 1, "kg": 75.0, "reps": 8, "is_warmup": false, "done": false},
        {"id": 3, "exercise_id": 1, "set_index": 2, "kg": 75.0, "reps": 8, "is_warmup": false, "done": false},
        {"id": 4, "exercise_id": 1, "set_index": 3, "kg": 75.0, "reps": 8, "is_warmup": false, "done": false}]},
      {"id": 2, "workout_id": 4, "name": "Incline DB Press", "position": 1, "target_sets": 3, "target_reps": 10, "target_kg": 30.0, "sets": []},
      {"id": 3, "workout_id": 4, "name": "Cable Fly", "position": 2, "target_sets": 3, "target_reps": 12, "target_kg": 17.5, "sets": []},
      {"id": 4, "workout_id": 4, "name": "Lateral Raise", "position": 3, "target_sets": 3, "target_reps": 15, "target_kg": 10.0, "sets": []}]}
    """#

    static let food = #"""
    {"date": "2026-10-03",
     "meals": {
      "breakfast": [
       {"id": 1, "date": "2026-10-03", "meal": "breakfast", "name": "Greek yogurt 2%", "quantity": "250 g", "kcal": 183.0, "protein_g": 27.0, "carbs_g": 10.0, "fat_g": 4.0, "source": "manual"},
       {"id": 2, "date": "2026-10-03", "meal": "breakfast", "name": "Granola", "quantity": "45 g", "kcal": 205.0, "protein_g": 5.0, "carbs_g": 28.0, "fat_g": 7.0, "source": "manual"},
       {"id": 3, "date": "2026-10-03", "meal": "breakfast", "name": "Blueberries", "quantity": "1 cup", "kcal": 84.0, "protein_g": 1.0, "carbs_g": 21.0, "fat_g": 0.0, "source": "manual"},
       {"id": 4, "date": "2026-10-03", "meal": "breakfast", "name": "Latte", "quantity": "12 oz", "kcal": 58.0, "protein_g": 4.0, "carbs_g": 6.0, "fat_g": 2.0, "source": "manual"}],
      "lunch": [
       {"id": 5, "date": "2026-10-03", "meal": "lunch", "name": "Chicken burrito bowl, guacamole", "quantity": "1 bowl", "kcal": 680.0, "protein_g": 42.0, "carbs_g": 71.0, "fat_g": 24.0, "source": "coach"}],
      "dinner": [],
      "snack": [
       {"id": 6, "date": "2026-10-03", "meal": "snack", "name": "Protein shake", "quantity": "1 scoop", "kcal": 210.0, "protein_g": 40.0, "carbs_g": 6.0, "fat_g": 3.0, "source": "manual"},
       {"id": 7, "date": "2026-10-03", "meal": "snack", "name": "Banana", "quantity": "1 medium", "kcal": 105.0, "protein_g": 1.0, "carbs_g": 27.0, "fat_g": 0.0, "source": "manual"},
       {"id": 8, "date": "2026-10-03", "meal": "snack", "name": "Peanut butter", "quantity": "1 tbsp", "kcal": 95.0, "protein_g": 4.0, "carbs_g": 3.0, "fat_g": 8.0, "source": "manual"}]},
     "totals": {"kcal": 1620.0, "protein_g": 124.0, "carbs_g": 172.0, "fat_g": 48.0}}
    """#

    static let goals = #"""
    [{"id": 1, "title": "Bench press 100 kg", "kind": "strength", "unit": "kg", "start_value": 85.0, "current_value": 95.0, "target_value": 100.0, "deadline": "2026-12-15", "status": "active"},
     {"id": 2, "title": "Reach 72 kg", "kind": "body", "unit": "kg", "start_value": 76.8, "current_value": 74.6, "target_value": 72.0, "deadline": "2027-01-31", "status": "active"},
     {"id": 3, "title": "160 g protein daily", "kind": "nutrition", "unit": "g", "start_value": 0.0, "current_value": 124.0, "target_value": 160.0, "deadline": null, "status": "active"},
     {"id": 4, "title": "Train 4× a week", "kind": "habit", "unit": "sessions", "start_value": 0.0, "current_value": 3.0, "target_value": 4.0, "deadline": null, "status": "active"}]
    """#

    static let history = #"""
    [{"id": 1, "role": "user", "content": "I train 4 days a week and want a 100 kg bench by December. Build me a plan.", "cards": [], "created_at": "2026-10-03T09:00:00"},
     {"id": 2, "role": "assistant", "content": "Here’s an upper/lower split with two bench days: heavy on Monday, volume on Saturday. Bench goes up 2.5 kg whenever you hit every rep.", "created_at": "2026-10-03T09:00:05",
      "cards": [{"type": "workout_plan", "data": {"plan_name": "Upper / Lower · 4 days", "weeks": 8, "workouts": [
        {"id": 1, "day_label": "MON", "name": "Upper A — Strength", "summary": "Bench 5×5 · Row · Overhead press · Pull-up"},
        {"id": 2, "day_label": "TUE", "name": "Lower A", "summary": "Squat 5×5 · RDL · Walking lunge"},
        {"id": 3, "day_label": "THU", "name": "Lower B", "summary": "Deadlift 3×5 · Front squat · Leg curl"},
        {"id": 4, "day_label": "SAT", "name": "Upper B — Volume", "summary": "Bench 4×8 · Incline DB · Cable fly · Lateral raise"}]}}]},
     {"id": 3, "role": "user", "content": "Lunch was a chicken burrito bowl with guac", "cards": null, "created_at": "2026-10-03T13:00:00"},
     {"id": 4, "role": "assistant", "content": "You have 830 kcal and 36 g protein left today.", "created_at": "2026-10-03T13:00:04",
      "cards": [{"type": "food_logged", "data": {"id": 5, "meal": "lunch", "name": "Chicken burrito bowl, guacamole", "kcal": 680, "protein_g": 42, "carbs_g": 71, "fat_g": 24}}]}]
    """#
}
