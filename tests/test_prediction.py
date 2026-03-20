import pytest
from app.ml.predict import predict_sepsis_risk
from app.ml.feature_processor import compute_sirs_score, compute_sofa_score

def test_sirs_score_normal():
    vitals = {"heart_rate":75,"temperature":37.0,"respiratory_rate":14,"wbc":7.5}
    assert compute_sirs_score(vitals) == 0

def test_sirs_score_sepsis():
    vitals = {"heart_rate":115,"temperature":39.2,"respiratory_rate":26,"wbc":14}
    assert compute_sirs_score(vitals) == 4

def test_sofa_score_normal():
    vitals = {"systolic_bp":120,"spo2":98,"lactate":1.0,"creatinine":0.9}
    assert compute_sofa_score(vitals) == 0

def test_predict_critical():
    vitals = {"heart_rate":130,"systolic_bp":75,"temperature":39.5,
              "respiratory_rate":30,"spo2":87,"wbc":16,"lactate":4.5,"creatinine":3.2}
    result = predict_sepsis_risk(vitals)
    assert result["risk_score"] >= 65
    assert result["risk_level"] == "CRITICAL"
    assert len(result["top_features"]) > 0

def test_predict_low():
    vitals = {"heart_rate":72,"systolic_bp":118,"temperature":36.8,
              "respiratory_rate":14,"spo2":99,"wbc":7,"lactate":1.0,"creatinine":0.8}
    result = predict_sepsis_risk(vitals)
    assert result["risk_level"] in ("LOW", "MODERATE")
