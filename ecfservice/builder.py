"""Builder fluido para payloads e-CF (solo estructura, sin validación de negocio)."""

from __future__ import annotations

from typing import Any, Self


class ECFPayloadBuilder:
    """Construye un dict de payload e-CF compatible con ECF Service.

    Uso:
        payload = (
            ECFPayloadBuilder(ecf_type="31")
            .id_doc(eNCF="E310000000001")
            .emisor(RNC="130478031", RazonSocial="Mi Empresa SRL")
            .comprador(RNC="123456789", RazonSocial="Cliente S.A.")
            .totales(MontoTotal=1000.00, TotalITBIS=180.00)
            .add_item({"NumeroLinea": 1, "Descripcion": "Servicio", "MontoItem": 1000.00})
            .build()
        )
    """

    def __init__(self, ecf_type: str | None = None, *, version: str = "1.0"):
        self._version = version
        self._ecf_type = ecf_type
        self._id_doc: dict[str, Any] = {}
        self._emisor: dict[str, Any] = {}
        self._comprador: dict[str, Any] | None = None
        self._totales: dict[str, Any] = {}
        self._items: list[dict[str, Any]] = []
        self._referencia: dict[str, Any] | None = None
        self._descuentos: dict[str, Any] | None = None
        self._otra_moneda: dict[str, Any] | None = None

    def id_doc(self, **fields: Any) -> Self:
        self._id_doc.update(fields)
        if self._ecf_type and "TipoEcf" not in self._id_doc:
            self._id_doc["TipoEcf"] = self._ecf_type
        return self

    def emisor(self, **fields: Any) -> Self:
        self._emisor.update(fields)
        return self

    def comprador(self, **fields: Any) -> Self:
        if self._comprador is None:
            self._comprador = {}
        self._comprador.update(fields)
        return self

    def totales(self, **fields: Any) -> Self:
        self._totales.update(fields)
        return self

    def add_item(self, item: dict[str, Any]) -> Self:
        self._items.append(item)
        return self

    def informacion_referencia(self, **fields: Any) -> Self:
        if self._referencia is None:
            self._referencia = {}
        self._referencia.update(fields)
        return self

    def descuentos_recargos(self, data: dict[str, Any]) -> Self:
        self._descuentos = data
        return self

    def otra_moneda(self, data: dict[str, Any]) -> Self:
        self._otra_moneda = data
        return self

    def build(self) -> dict[str, Any]:
        encabezado: dict[str, Any] = {
            "Version": self._version,
            "IdDoc": self._id_doc,
            "Emisor": self._emisor,
            "Totales": self._totales,
        }
        if self._comprador is not None:
            encabezado["Comprador"] = self._comprador
        if self._otra_moneda is not None:
            encabezado["OtraMoneda"] = self._otra_moneda

        result: dict[str, Any] = {
            "Encabezado": encabezado,
            "DetallesItems": {"Item": self._items},
        }
        if self._referencia is not None:
            result["InformacionReferencia"] = self._referencia
        if self._descuentos is not None:
            result["DescuentosORecargos"] = self._descuentos
        return result
