from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(UTC)


def generate_id() -> str:
    return str(uuid4())


def ensure_document(data: dict[str, Any], *, doc_id: str | None = None) -> dict[str, Any]:
    document = deepcopy(data)
    now = utc_now()
    document.setdefault("id", doc_id or generate_id())
    document.setdefault("created_at", now)
    document["updated_at"] = now
    return document


def prepare_update(data: dict[str, Any]) -> dict[str, Any]:
    update = deepcopy(data)
    update["updated_at"] = utc_now()
    return update


def normalize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, tuple):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_value(item) for key, item in value.items()}
    return value


def normalize_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {key: normalize_value(value) for key, value in data.items()}


def sort_documents(items: Iterable[dict[str, Any]], field: str, reverse: bool = False) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: item.get(field) or datetime.min.replace(tzinfo=UTC), reverse=reverse)
