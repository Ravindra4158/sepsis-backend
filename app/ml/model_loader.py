from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import joblib

from app.config.settings import settings
from app.utils.logger import logger


REQUIRED_FEATURES = {
    "heart_rate",
    "systolic_bp",
    "diastolic_bp",
    "temperature",
    "respiratory_rate",
    "spo2",
    "wbc",
    "lactate",
    "creatinine",
}


@dataclass
class ModelMetadata:
    provider: str
    version: str = "v1.0"
    required_features: set[str] = field(default_factory=lambda: set(REQUIRED_FEATURES))
    source: str = ""


class BaseModelAdapter:
    def __init__(self, provider: str, metadata: ModelMetadata) -> None:
        self.provider = provider
        self._metadata = metadata

    def load(self) -> "BaseModelAdapter":
        return self

    def predict_proba(self, features: Any) -> Any:
        raise NotImplementedError

    def health(self) -> dict[str, Any]:
        return {"status": "ready", "provider": self.provider, "model_version": self._metadata.version}

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": self._metadata.provider,
            "version": self._metadata.version,
            "required_features": sorted(self._metadata.required_features),
            "source": self._metadata.source,
        }

    def supports(self, feature_names: set[str]) -> bool:
        return self._metadata.required_features.issubset(feature_names)


class JoblibModelAdapter(BaseModelAdapter):
    def __init__(self, model: Any, metadata: ModelMetadata) -> None:
        super().__init__("joblib", metadata)
        self.model = model

    def predict_proba(self, features: Any) -> Any:
        return self.model.predict_proba(features)


class ModelManager:
    def __init__(self) -> None:
        self.adapter: BaseModelAdapter | None = None

    def load(self) -> BaseModelAdapter | None:
        if self.adapter is not None:
            return self.adapter

        if not os.path.exists(settings.MODEL_PATH):
            logger.warning(f"Model file not found at {settings.MODEL_PATH}. Falling back to rule-based scoring.")
            return None

        try:
            raw_model = joblib.load(settings.MODEL_PATH)
            metadata = self._load_metadata()
            self.adapter = JoblibModelAdapter(raw_model, metadata).load()
            logger.info(f"Local model adapter ready from {settings.MODEL_PATH}")
            return self.adapter
        except Exception as exc:
            logger.warning(f"Could not load model adapter: {exc}. Falling back to rule-based scoring.")
            self.adapter = None
            return None

    def get(self) -> BaseModelAdapter | None:
        if self.adapter is None:
            return self.load()
        return self.adapter

    def _load_metadata(self) -> ModelMetadata:
        required_features = set(REQUIRED_FEATURES)
        version = "v1.0"
        source = settings.MODEL_PATH

        if settings.MODEL_METADATA_PATH and os.path.exists(settings.MODEL_METADATA_PATH):
            try:
                with open(settings.MODEL_METADATA_PATH, "r", encoding="utf-8") as handle:
                    metadata = json.load(handle)
                required_features = set(metadata.get("required_features") or REQUIRED_FEATURES)
                version = metadata.get("version", version)
                source = metadata.get("source", source)
            except Exception as exc:
                logger.warning(f"Model metadata load failed: {exc}. Continuing with defaults.")

        return ModelMetadata(
            provider=settings.MODEL_PROVIDER,
            version=version,
            required_features=required_features,
            source=source,
        )


model_manager = ModelManager()


def load_model() -> BaseModelAdapter | None:
    return model_manager.load()


def get_model() -> BaseModelAdapter | None:
    return model_manager.get()
