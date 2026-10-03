import math

def category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"

def bmi_formula(height_cm: float, weight_kg: float) -> float:
    if not all(math.isfinite(v) and v > 0 for v in (height_cm, weight_kg)):
        raise ValueError("Height and weight must be finite and positive")
    return round(weight_kg / (height_cm / 100) ** 2, 1)

async def compute_bmi(height_cm, weight_kg):
    if height_cm is None or weight_kg is None:
        return None, None, "formula"
    value = bmi_formula(height_cm, weight_kg)
    return value, category(value), "formula"
