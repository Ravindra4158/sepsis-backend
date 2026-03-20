from typing import Dict, Any

from app.ml.model_loader import get_model
from app.ml.feature_processor import extract_features, compute_sirs_score, compute_sofa_score, get_top_features
from app.config.settings import settings

def score_to_level(score: int) -> str:
    if score >= settings.MODEL_THRESHOLD_CRITICAL: return "CRITICAL"
    if score >= settings.MODEL_THRESHOLD_HIGH:     return "HIGH"
    if score >= settings.MODEL_THRESHOLD_MODERATE: return "MODERATE"
    return "LOW"

def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def _above_range_ratio(value: float, normal_high: float, severe_high: float) -> float:
    if value <= normal_high:
        return 0.0
    if severe_high <= normal_high:
        return 1.0
    return _clamp((value - normal_high) / (severe_high - normal_high), 0.0, 1.0)

def _below_range_ratio(value: float, normal_low: float, severe_low: float) -> float:
    if value >= normal_low:
        return 0.0
    if severe_low >= normal_low:
        return 1.0
    return _clamp((normal_low - value) / (normal_low - severe_low), 0.0, 1.0)

def _range_ratio(
    value: float,
    normal_low: float,
    normal_high: float,
    *,
    severe_low: float | None = None,
    severe_high: float | None = None,
) -> float:
    low_ratio = _below_range_ratio(value, normal_low, severe_low) if severe_low is not None else 0.0
    high_ratio = _above_range_ratio(value, normal_high, severe_high) if severe_high is not None else 0.0
    return max(low_ratio, high_ratio)

def rule_based_score(vitals: Dict[str, Any]) -> float:
    """Continuous clinical severity score used as fallback and calibration anchor."""
    temp = float(vitals.get("temperature", 37) or 37)
    hr   = float(vitals.get("heart_rate", 75) or 75)
    rr   = float(vitals.get("respiratory_rate", 14) or 14)
    sbp  = float(vitals.get("systolic_bp", 120) or 120)
    spo2 = float(vitals.get("spo2", 98) or 98)
    lac  = float(vitals.get("lactate", 1.0) or 1.0)
    wbc  = float(vitals.get("wbc", 7.0) or 7.0)
    cr   = float(vitals.get("creatinine", 0.9) or 0.9)
    sirs = compute_sirs_score(vitals)
    sofa = compute_sofa_score(vitals)

    score = 0.0
    score += 14.0 * _range_ratio(temp, 36.1, 37.5, severe_low=35.0, severe_high=40.5)
    score += 16.0 * _range_ratio(hr, 60.0, 100.0, severe_low=45.0, severe_high=150.0)
    score += 14.0 * _range_ratio(rr, 12.0, 20.0, severe_low=8.0, severe_high=34.0)
    score += 18.0 * _below_range_ratio(sbp, 95.0, 70.0)
    score += 14.0 * _below_range_ratio(spo2, 95.0, 82.0)
    score += 12.0 * _above_range_ratio(lac, 2.0, 5.0)
    score += 8.0 * _range_ratio(wbc, 4.5, 11.0, severe_low=2.0, severe_high=20.0)
    score += 10.0 * _above_range_ratio(cr, 1.2, 4.0)
    score += 8.0 * (sirs / 4.0)
    score += 10.0 * (sofa / 8.0)
    return round(min(100.0, score), 1)

def calibrate_probability(raw_prob: float, rule_score: float) -> float:
    rule_prob = _clamp(rule_score / 100.0, 0.0, 1.0)
    raw_prob = _clamp(raw_prob, 0.0, 1.0)

    # Blend the raw model output with a continuous clinical severity anchor so
    # extremely confident model probabilities still land on a useful 0-100 range.
    blended = (raw_prob * 0.35) + (rule_prob * 0.65)

    # Pull the score slightly away from hard 0/100 unless the clinical score is
    # truly at the floor or ceiling. This keeps the UI responsive for demos.
    if 0.0 < blended < 1.0:
        blended = 0.02 + (blended * 0.96)

    return round(_clamp(blended, 0.0, 1.0), 4)

def predict_sepsis_risk(vitals: Dict[str, Any]) -> Dict[str, Any]:
    model = get_model()
    lstm_prob = xgb_prob = ensemble_prob = None
    rule_score = rule_based_score(vitals)
    if model is not None:
        try:
            feature_names = {key for key, value in vitals.items() if value is not None}
            if not model.supports(feature_names):
                raise ValueError("Model feature requirements not satisfied")
            features = extract_features(vitals)
            raw_prob = float(model.predict_proba(features)[0][1])
            calibrated_prob = calibrate_probability(raw_prob, rule_score)
            ensemble_prob = calibrated_prob
            # Current runtime uses a single local model adapter, not separate LSTM/XGBoost models.
            # Mirror the same calibrated probability into both fields so the UI reflects
            # the active inference score rather than saturated binary outputs.
            lstm_prob = calibrated_prob
            xgb_prob = calibrated_prob
            risk_score = int(round(calibrated_prob * 100))
            model_version = model.metadata()["version"]
        except Exception:
            risk_score = int(round(rule_score))
            lstm_prob = risk_score / 100.0
            xgb_prob = risk_score / 100.0
            ensemble_prob = risk_score / 100.0
            model_version = "rule-fallback"
    else:
        risk_score = int(round(rule_score))
        lstm_prob = risk_score / 100.0
        xgb_prob = risk_score / 100.0
        ensemble_prob = risk_score / 100.0
        model_version = "rule-fallback"
    risk_level = score_to_level(risk_score)
    top_features = get_top_features(vitals)
    sirs = compute_sirs_score(vitals)
    sofa = compute_sofa_score(vitals)
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "lstm_probability": lstm_prob,
        "xgb_probability": xgb_prob,
        "ensemble_probability": ensemble_prob,
        "sirs_score": sirs,
        "sofa_score": sofa,
        "top_features": top_features,
        "model_version": model_version,
    }
