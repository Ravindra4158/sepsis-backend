import numpy as np
from typing import Dict, Any, List

NORMAL_RANGES = {
    "heart_rate":        (60, 100),
    "systolic_bp":       (90, 140),
    "temperature":       (36.1, 37.5),
    "respiratory_rate":  (12, 20),
    "spo2":              (95, 100),
    "wbc":               (4.5, 11.0),
    "lactate":           (0.5, 2.0),
    "creatinine":        (0.6, 1.2),
}

def compute_sirs_score(vitals: Dict[str, Any]) -> int:
    score = 0
    temp = vitals.get("temperature", 37)
    if temp is not None and (float(temp) > 38.3 or float(temp) < 36.0): score += 1
    hr = vitals.get("heart_rate", 75)
    if hr is not None and float(hr) > 90: score += 1
    rr = vitals.get("respiratory_rate", 14)
    if rr is not None and float(rr) > 20: score += 1
    wbc = vitals.get("wbc", 7)
    if wbc is not None and (float(wbc) > 12 or float(wbc) < 4): score += 1
    return score

def compute_sofa_score(vitals: Dict[str, Any]) -> int:
    score = 0
    sbp = vitals.get("systolic_bp", 120)
    if sbp is not None and float(sbp) < 90: score += 2
    spo2 = vitals.get("spo2", 98)
    if spo2 is not None and float(spo2) < 92: score += 2
    lactate = vitals.get("lactate", 1.0)
    if lactate is not None and float(lactate) > 2.0: score += 2
    creatinine = vitals.get("creatinine", 0.9)
    if creatinine is not None and float(creatinine) > 2.0: score += 2
    return score

def extract_features(vitals: Dict[str, Any]) -> np.ndarray:
    hr   = float(vitals.get("heart_rate", 75) or 75)
    sbp  = float(vitals.get("systolic_bp", 120) or 120)
    dbp  = float(vitals.get("diastolic_bp", 80) or 80)
    temp = float(vitals.get("temperature", 37.0) or 37.0)
    rr   = float(vitals.get("respiratory_rate", 14) or 14)
    spo2 = float(vitals.get("spo2", 98) or 98)
    wbc  = float(vitals.get("wbc", 7.0) or 7.0)
    lac  = float(vitals.get("lactate", 1.0) or 1.0)
    cr   = float(vitals.get("creatinine", 0.9) or 0.9)
    sirs = compute_sirs_score(vitals)
    sofa = compute_sofa_score(vitals)
    map_val = (sbp + 2 * dbp) / 3
    shock_index = hr / max(sbp, 1)
    features = [hr, sbp, dbp, temp, rr, spo2, wbc, lac, cr,
                sirs, sofa, map_val, shock_index,
                1 if hr > 100 else 0, 1 if sbp < 90 else 0,
                1 if temp > 38.3 else 0, 1 if rr > 20 else 0,
                1 if spo2 < 95 else 0, 1 if wbc > 12 else 0,
                1 if lac > 2 else 0, 1 if cr > 2 else 0]
    return np.array(features).reshape(1, -1)

def get_top_features(vitals: Dict[str, Any]) -> List[Dict[str, Any]]:
    flags = []
    if float(vitals.get("temperature", 37) or 37) > 38.3: flags.append({"name": "Fever", "value": vitals["temperature"], "threshold": 38.3})
    if float(vitals.get("heart_rate", 75) or 75) > 90: flags.append({"name": "Tachycardia", "value": vitals["heart_rate"], "threshold": 90})
    if float(vitals.get("respiratory_rate", 14) or 14) > 20: flags.append({"name": "Tachypnea", "value": vitals["respiratory_rate"], "threshold": 20})
    if float(vitals.get("systolic_bp", 120) or 120) < 90: flags.append({"name": "Hypotension", "value": vitals["systolic_bp"], "threshold": 90})
    if float(vitals.get("lactate", 1.0) or 1.0) > 2.0: flags.append({"name": "Elevated Lactate", "value": vitals["lactate"], "threshold": 2.0})
    if float(vitals.get("spo2", 98) or 98) < 95: flags.append({"name": "Low SpO2", "value": vitals["spo2"], "threshold": 95})
    if float(vitals.get("creatinine", 0.9) or 0.9) > 2.0: flags.append({"name": "Renal Dysfunction", "value": vitals["creatinine"], "threshold": 2.0})
    return flags[:5]
