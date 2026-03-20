import argparse
import asyncio
import random
from dataclasses import dataclass

import httpx


BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "nurse@sepsis.ai"
PASSWORD = "Nurse@123"


@dataclass
class MonitorState:
    patient: dict
    mode: str
    cycle: int = 0


def clamp(value, low, high):
    return max(low, min(high, value))


def jitter_int(base: int, spread: int) -> int:
    return int(round(base + random.randint(-spread, spread)))


def jitter_float(base: float, spread: float, digits: int = 1) -> float:
    return round(base + random.uniform(-spread, spread), digits)


def stable_payload() -> dict:
    return {
        "heart_rate": clamp(jitter_int(78, 6), 55, 110),
        "systolic_bp": clamp(jitter_int(116, 7), 85, 150),
        "diastolic_bp": clamp(jitter_int(74, 5), 45, 100),
        "temperature": clamp(jitter_float(36.9, 0.3), 35.5, 39.5),
        "respiratory_rate": clamp(jitter_int(17, 2), 10, 28),
        "spo2": clamp(jitter_int(98, 1), 88, 100),
        "wbc": clamp(jitter_float(7.6, 1.2), 3.0, 20.0),
        "lactate": clamp(jitter_float(1.1, 0.2), 0.3, 8.0),
        "creatinine": clamp(jitter_float(0.9, 0.1), 0.4, 4.0),
        "source": "monitor_stream",
        "notes": "Continuous bedside monitor simulation",
    }


def worsening_payload(cycle: int) -> dict:
    severity = min(cycle, 12)
    return {
        "heart_rate": clamp(jitter_int(88 + severity * 3, 5), 60, 155),
        "systolic_bp": clamp(jitter_int(118 - severity * 3, 6), 70, 150),
        "diastolic_bp": clamp(jitter_int(76 - severity * 2, 4), 40, 95),
        "temperature": clamp(jitter_float(37.1 + severity * 0.12, 0.25), 36.0, 41.0),
        "respiratory_rate": clamp(jitter_int(18 + severity, 2), 12, 36),
        "spo2": clamp(jitter_int(97 - severity, 1), 82, 100),
        "wbc": clamp(jitter_float(8.8 + severity * 0.7, 0.8), 4.0, 30.0),
        "lactate": clamp(jitter_float(1.2 + severity * 0.22, 0.15), 0.4, 9.0),
        "creatinine": clamp(jitter_float(0.9 + severity * 0.11, 0.08), 0.5, 5.0),
        "source": "monitor_stream",
        "notes": f"Worsening patient simulation cycle {cycle}",
    }


def critical_payload(cycle: int) -> dict:
    spike = cycle % 4 == 0
    return {
        "heart_rate": clamp(jitter_int(128 if spike else 118, 8), 90, 170),
        "systolic_bp": clamp(jitter_int(82 if spike else 88, 6), 60, 110),
        "diastolic_bp": clamp(jitter_int(52 if spike else 58, 4), 35, 75),
        "temperature": clamp(jitter_float(39.4 if spike else 38.8, 0.35), 37.8, 41.5),
        "respiratory_rate": clamp(jitter_int(29 if spike else 25, 3), 18, 40),
        "spo2": clamp(jitter_int(86 if spike else 90, 2), 75, 95),
        "wbc": clamp(jitter_float(16.5 if spike else 14.5, 1.4), 8.0, 30.0),
        "lactate": clamp(jitter_float(4.8 if spike else 3.6, 0.5), 1.5, 10.0),
        "creatinine": clamp(jitter_float(2.1 if spike else 1.8, 0.2), 0.8, 6.0),
        "source": "monitor_stream",
        "notes": f"Critical bedside simulation cycle {cycle}",
    }


def generate_payload(state: MonitorState, forced_mode: str | None = None) -> dict:
    state.cycle += 1
    mode = forced_mode or state.mode
    if mode == "stable":
        return stable_payload()
    if mode == "worsening":
        return worsening_payload(state.cycle)
    return critical_payload(state.cycle)


def assign_modes(patients: list[dict], mode: str) -> list[MonitorState]:
    if mode != "demo":
        return [MonitorState(patient=patient, mode=mode) for patient in patients]

    pattern = ["stable", "worsening", "critical"]
    states = []
    for index, patient in enumerate(patients):
        states.append(MonitorState(patient=patient, mode=pattern[index % len(pattern)]))
    return states


async def login(client: httpx.AsyncClient) -> dict | None:
    print("Logging in...")
    login_res = await client.post(
        f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return None
    print("Logged in successfully.")
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}


async def fetch_patients(client: httpx.AsyncClient, headers: dict) -> list[dict]:
    patients_res = await client.get(f"{BASE_URL}/patients/", headers=headers)
    if patients_res.status_code != 200:
        print(f"Failed to fetch patients: {patients_res.text}")
        return []
    patients = patients_res.json().get("patients", [])
    print(f"Found {len(patients)} patients.")
    return patients


async def push_reading(client: httpx.AsyncClient, headers: dict, state: MonitorState, forced_mode: str | None = None) -> None:
    patient = state.patient
    payload = generate_payload(state, forced_mode=forced_mode)
    patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
    print(f"Sending {state.mode.upper()} vitals for {patient.get('mrn')} ({patient_name})...")

    vital_res = await client.post(
        f"{BASE_URL}/patients/{patient['id']}/vitals/",
        headers=headers,
        json=payload,
    )
    if vital_res.status_code != 201:
        print(f"  -> Vitals failed: {vital_res.text}")
        return

    vital_id = vital_res.json()["vital"]["id"]
    print(
        "  -> Vitals recorded:"
        f" {vital_id} | HR {payload['heart_rate']} | BP {payload['systolic_bp']}/{payload['diastolic_bp']}"
        f" | Temp {payload['temperature']} | SpO2 {payload['spo2']}"
    )

    pred_res = await client.post(
        f"{BASE_URL}/patients/{patient['id']}/predictions/",
        headers=headers,
    )
    if pred_res.status_code not in (200, 201):
        print(f"  -> Prediction failed: {pred_res.text}")
        return

    pred_payload = pred_res.json()
    prediction = pred_payload.get("prediction", pred_payload)
    risk_score = prediction.get("risk_score", 0)
    risk_level = prediction.get("risk_level", "UNKNOWN")
    alert_created = pred_payload.get("alert_created", False)
    print(f"  -> Prediction OK: {risk_level} ({risk_score}/100), alert_created={alert_created}")


async def generate_vitals(interval_seconds: float, cycles: int | None, mode: str) -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = await login(client)
        if not headers:
            return

        patients = await fetch_patients(client, headers)
        if not patients:
            print("No patients available for mock streaming.")
            return

        states = assign_modes(patients, mode)
        print("Stream profiles:")
        for state in states:
            patient = state.patient
            print(f"  - {patient.get('mrn')}: {state.mode}")

        cycle = 0
        while True:
            cycle += 1
            print(f"\n--- Monitor cycle {cycle} ---")
            for state in states:
                await push_reading(client, headers, state)
                await asyncio.sleep(0.35)

            if cycles is not None and cycle >= cycles:
                break

            print(f"Sleeping {interval_seconds} seconds before next cycle...")
            await asyncio.sleep(interval_seconds)

        print("Monitor stream complete.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Continuously stream realistic bedside vitals into the backend.")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between cycles. Default: 5")
    parser.add_argument("--cycles", type=int, default=0, help="Number of cycles to run. Use 0 for continuous mode.")
    parser.add_argument(
        "--mode",
        choices=["demo", "stable", "worsening", "critical"],
        default="demo",
        help="Streaming profile. 'demo' rotates patients across stable, worsening, and critical patterns.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cycle_count = None if args.cycles == 0 else args.cycles
    asyncio.run(generate_vitals(args.interval, cycle_count, args.mode))
