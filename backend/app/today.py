from fastapi import HTTPException
from app.models import Goal
from app import services as svc

food_totals = svc.food_totals

def build_today(s, day=None):
    u = svc.profile(s)
    if any(getattr(u, k) is None for k in ("kcal_target", "protein_g", "carbs_g", "fat_g")):
        raise HTTPException(409, "profile_incomplete")
    day = day or svc.local_day(u)
    totals = svc.food_totals(s, day)
    completed = svc.week_sessions(s, day)
    days = [False]*7
    for session in completed:
        days[svc.local_day(u, svc.aware(session.finished_at)).weekday()] = True
    goals = s.exec(svc.owned(Goal).where(Goal.status == "active", Goal.progress_source == "weekly_sessions").order_by(Goal.id.desc())).all()
    target = round(goals[0].target_value) if goals else len(set(u.available_days))
    workouts = svc.list_workouts(s)
    nxt = next((w for w in workouts if w["status"] == "active"), None)
    if nxt is None:
        labels = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
        workouts.sort(key=lambda w: ((labels.index(w["day_label"])-day.weekday()) % 7, w["id"]))
        nxt = next((w for w in workouts if w["status"] == "planned"), None)
        nxt = nxt or (workouts[0] if workouts else None)
    next_out = None
    if nxt:
        next_out = {"id": nxt["id"], "name": nxt["name"], "exercise_count": len(nxt["exercises"]),
                    "est_minutes": round(sum(e["target_sets"] for e in nxt["exercises"])*4.25)}
    left = u.kcal_target-totals["kcal"]
    protein_left = u.protein_g-totals["protein_g"]
    tip = (f"Your intake is {abs(left)} kcal above the saved target today." if left < 0 else
           f"{left} kcal and {max(0, protein_left)} g protein remain against your saved targets.")
    scan = svc.scans(s)
    return {
        "date": day.isoformat(), "kcal": {"target": u.kcal_target, "eaten": totals["kcal"], "left": left},
        "macros": {key: {"eaten": totals[field], "target": getattr(u, field)} for key, field in
                   (("protein", "protein_g"), ("carbs", "carbs_g"), ("fat", "fat_g"))},
        "bmi": {"value": svc.public(u)["bmi"], "category": svc.public(u)["bmi_category"]}, "weight_kg": u.weight_kg,
        "week": {"sessions_done": len(completed), "sessions_target": target, "days": days},
        "next_workout": next_out, "coach_tip": tip, "targets_source": u.targets_source,
        "latest_scan": scan[0] if scan else None,
    }
