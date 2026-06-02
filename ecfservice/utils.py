"""Utilidades generales del SDK ECF Service."""

from __future__ import annotations

import re
import uuid

from stdnum.do import cedula, rnc


def generate_idempotency_key() -> str:
    return str(uuid.uuid4())


def format_rnc(value: str) -> str:
    return re.sub(r"\D", "", value)


def validate_rnc(value: str) -> bool:
    clean = format_rnc(value)
    if not clean or not clean.isdigit():
        return False
    if len(clean) == 11:
        return rnc.is_valid(clean)
    if len(clean) == 9:
        return cedula.is_valid(clean) or rnc.is_valid(clean)
    if len(clean) == 13:
        return cedula.is_valid(clean)
    return False
