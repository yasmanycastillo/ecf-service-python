"""Helper para auto-inyección de datos del Emisor desde CompanyProfile."""

from __future__ import annotations

from typing import Any

from ecfservice.models import CompanyProfile


def build_emisor(
    profile: CompanyProfile | dict[str, Any],
    **overrides: Any,
) -> dict[str, Any]:
    """Convierte un CompanyProfile o dict en la sección Emisor de un payload e-CF.

    Args:
        profile: CompanyProfile (de client.company()) o dict con datos de empresa.
        **overrides: Campos adicionales o reemplazos (ej. FechaEmision).

    Returns:
        Dict listo para pasar a ECFPayloadBuilder.emisor().
    """
    if isinstance(profile, dict):
        data = _from_dict(profile)
    else:
        data = _from_profile(profile)

    data.update(overrides)
    return data


def _from_profile(p: CompanyProfile) -> dict[str, Any]:
    emisor: dict[str, Any] = {
        "RNCEmisor": p.rnc,
        "RazonSocialEmisor": (p.name or "")[:150],
    }
    if p.trade_name:
        emisor["NombreComercial"] = p.trade_name[:150]
    if p.address:
        emisor["DireccionEmisor"] = p.address[:100]
    if p.email:
        emisor["CorreoEmisor"] = p.email[:80]
    if p.phone:
        emisor["TablaTelefonoEmisor"] = {"Telefono": [{"Telefono": p.phone}]}
    return emisor


def _from_dict(d: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "rnc": "RNCEmisor",
        "name": "RazonSocialEmisor",
        "trade_name": "NombreComercial",
        "address": "DireccionEmisor",
        "email": "CorreoEmisor",
    }
    emisor: dict[str, Any] = {}
    for src, dst in mapping.items():
        val = d.get(src)
        if val:
            emisor[dst] = val
    phone = d.get("phone")
    if phone:
        emisor["TablaTelefonoEmisor"] = {"Telefono": [{"Telefono": phone}]}
    return emisor
