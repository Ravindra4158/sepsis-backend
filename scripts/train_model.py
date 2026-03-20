#!/usr/bin/env python3
"""
Train a sepsis risk prediction model on synthetic/MIMIC-like data.
Saves model to ai_models/sepsis_model.pkl
Usage: python scripts/train_model.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import joblib
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score, f1_score, classification_report

FEATURE_NAMES = [
    "heart_rate","systolic_bp","diastolic_bp","temperature","respiratory_rate",
    "spo2","wbc","lactate","creatinine","sirs_score","sofa_score","map",
    "shock_index","tachycardia_flag","hypotension_flag","fever_flag",
    "tachypnea_flag","low_spo2_flag","high_wbc_flag","high_lactate_flag","renal_flag",
]

np.random.seed(42)
N = 5000
# Sepsis patients (40%)
n_sepsis = int(N * 0.4)
n_normal = N - n_sepsis

def generate_patient(sepsis: bool):
    if sepsis:
        hr  = np.random.normal(110, 18)
        sbp = np.random.normal(85, 15)
        dbp = np.random.normal(55, 10)
        tmp = np.random.normal(38.8, 0.6)
        rr  = np.random.normal(24, 4)
        spo = np.random.normal(90, 4)
        wbc = np.random.normal(14, 3)
        lac = np.random.normal(3.5, 1.5)
        cre = np.random.normal(2.5, 1.0)
    else:
        hr  = np.random.normal(78, 12)
        sbp = np.random.normal(120, 15)
        dbp = np.random.normal(78, 10)
        tmp = np.random.normal(37.0, 0.4)
        rr  = np.random.normal(14, 2)
        spo = np.random.normal(98, 1)
        wbc = np.random.normal(7.5, 2)
        lac = np.random.normal(1.2, 0.4)
        cre = np.random.normal(0.9, 0.2)
    map_val = (sbp + 2*dbp)/3
    shock_i = hr / max(sbp, 1)
    sirs = sum([tmp>38.3 or tmp<36, hr>90, rr>20, wbc>12 or wbc<4])
    sofa = sum([sbp<90, spo<92, lac>2, cre>2]) * 2
    return [hr,sbp,dbp,tmp,rr,spo,wbc,lac,cre,sirs,sofa,map_val,shock_i,
            hr>100,sbp<90,tmp>38.3,rr>20,spo<95,wbc>12,lac>2,cre>2]

X_sep = np.array([generate_patient(True)  for _ in range(n_sepsis)])
X_nor = np.array([generate_patient(False) for _ in range(n_normal)])
X = np.vstack([X_sep, X_nor])
y = np.array([1]*n_sepsis + [0]*n_normal)
idx = np.random.permutation(N)
X, y = X[idx], y[idx]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.08, random_state=42)),
])
pipeline.fit(X_train, y_train)

y_proba = pipeline.predict_proba(X_test)[:,1]
y_pred  = (y_proba >= 0.5).astype(int)
auroc   = roc_auc_score(y_test, y_proba)
f1      = f1_score(y_test, y_pred)
cv_auc  = cross_val_score(pipeline, X, y, cv=5, scoring="roc_auc").mean()

print(f"\n=== SepsisShield Model Training Results ===")
print(f"  AUROC      : {auroc:.4f}")
print(f"  F1 Score   : {f1:.4f}")
print(f"  CV AUROC   : {cv_auc:.4f}")
print(f"\n{classification_report(y_test, y_pred, target_names=['Normal','Sepsis'])}")

os.makedirs("ai_models", exist_ok=True)
joblib.dump(pipeline, "ai_models/sepsis_model.pkl")
print("✅ Model saved to ai_models/sepsis_model.pkl")
