import logging
import os

import httpx

log = logging.getLogger("fitcoach.bmi")


def category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def bmi_formula(height_cm: float, weight_kg: float) -> float:
    return round(weight_kg / (height_cm / 100) ** 2, 1)


async def compute_bmi(height_cm: float, weight_kg: float) -> tuple[float, str, str]:
    key, url = os.getenv("VISUALIZE_API_KEY"), os.getenv("VISUALIZE_API_URL")
    if key and url:
        try:
            # TODO(visualize): replace endpoint, auth header and request/response
            # mapping with the real ones from Visualize AI's docs. Best guess below.
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    json={"height_cm": height_cm, "weight_kg": weight_kg},
                )
                r.raise_for_status()
                data = r.json()
                value = round(float(data["bmi"]), 1)
                log.info("BMI source: visualize")
                return value, data.get("category") or category(value), "visualize"
        except Exception as e:
            log.warning("Visualize AI failed (%s), using formula", e)
    value = bmi_formula(height_cm, weight_kg)
    log.info("BMI source: formula")
    return value, category(value), "formula"
