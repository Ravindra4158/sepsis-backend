from __future__ import annotations

import random
from typing import Any


CRITICAL_RATE = 0.3

RANGES = {
    "normal": {
        "heart_rate": (60, 90),
        "systolic_bp": (90, 120),
        "diastolic_bp": (60, 80),
        "temperature": (36.5, 37.5),
        "respiratory_rate": (12, 20),
        "spo2": (95, 100),
        "wbc": (4.5, 11.0),
        "lactate": (0.5, 1.5),
        "creatinine": (0.6, 1.2),
    },
    "critical": {
        "heart_rate": (110, 150),
        "systolic_bp": (70, 89),
        "diastolic_bp": (40, 59),
        "temperature": (38.5, 41.0),
        "respiratory_rate": (22, 35),
        "spo2": (80, 90),
        "wbc": (12.0, 25.0),
        "lactate": (2.1, 8.0),
        "creatinine": (1.5, 5.0),
    },
}


class MockVitalsService:
    def generate(self, *, critical: bool | None = None, source: str = "mock_backend") -> dict[str, Any]:
        if critical is None:
            critical = random.random() < CRITICAL_RATE
        ranges = RANGES["critical" if critical else "normal"]
        return {
            "heart_rate": random.randint(*ranges["heart_rate"]),
            "systolic_bp": random.randint(*ranges["systolic_bp"]),
            "diastolic_bp": random.randint(*ranges["diastolic_bp"]),
            "temperature": round(random.uniform(*ranges["temperature"]), 1),
            "respiratory_rate": random.randint(*ranges["respiratory_rate"]),
            "spo2": random.randint(*ranges["spo2"]),
            "wbc": round(random.uniform(*ranges["wbc"]), 1),
            "lactate": round(random.uniform(*ranges["lactate"]), 1),
            "creatinine": round(random.uniform(*ranges["creatinine"]), 1),
            "source": source,
            "notes": "Generated from backend mock vitals dataset",
        }


mock_vitals_service = MockVitalsService()
