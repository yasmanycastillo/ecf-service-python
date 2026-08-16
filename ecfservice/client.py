"""Cliente HTTP para ECF Service."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ecfservice.exceptions import (
    ECFAuthError,
    ECFConflictError,
    ECFError,
    ECFNotFoundError,
    ECFValidationError,
)
from ecfservice.models import (
    AcecfResponse,
    AnecfResponse,
    ArtifactType,
    CertificateInfo,
    ClientDocument,
    ClientDocumentListResponse,
    CompanyProfile,
    DGIIContributor,
    ECFDocument,
    EcfListResponse,
    HealthStatus,
    InboxAckResponse,
    InboxListResponse,
    SequenceListResponse,
    SubmissionMode,
    WebhookCreateResponse,
    WebhookDelivery,
    WebhookDeliveryListResponse,
    WebhookEndpoint,
    WebhookRotateSecretResponse,
)

_BASE_URL = "https://api.emite.do/api/v1"
_DEFAULT_TIMEOUT = 30.0
_DOWNLOAD_TIMEOUT = 120.0


class ECFClient:
    """Cliente síncrono para la API de ECF Service.

    Uso:
        client = ECFClient(api_key="ecf_...")
        doc = client.ecf.create(
            idempotency_key="INV-001",
            ecf_type="31",
            payload={...},
        )
        print(doc.status)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = _BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        """Crea el cliente.

        Args:
            api_key: Valor de ``X-API-Key``. Opcional para ``health()`` y ``dgii``.
            base_url: Base de la API v1 (default ``https://api.emite.do/api/v1``).
            timeout: Timeout HTTP en segundos. Las descargas de PDF/ZIP usan 120 s.
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        headers = {"X-API-Key": api_key} if api_key else {}
        self._http = httpx.Client(
            base_url=self._base_url,
            headers=headers,
            timeout=timeout,
        )
        self.ecf = _ECFResource(self._http)
        self.client = _ClientResource(self._http)
        self.dgii = _DGIIResource(self._http)

    def health(self) -> HealthStatus:
        """GET ``/health``. ``ok`` o ``degraded`` son aceptables para operar."""
        resp = self._http.get("/health")
        resp.raise_for_status()
        return HealthStatus.model_validate(resp.json())

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> ECFClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class _BaseResource:
    def __init__(self, http: httpx.Client):
        self._http = http

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        if "json" in kwargs:
            kwargs.setdefault("headers", {})["Content-Type"] = "application/json"
        resp = self._http.request(method, path, **kwargs)
        self._handle_error(resp)
        return resp

    @staticmethod
    def _handle_error(resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return
        try:
            body = resp.json()
        except Exception:
            body = {"detail": resp.text}

        detail = body if isinstance(body, dict) else {"detail": str(body)}
        msg = detail.get("detail", str(body))

        if resp.status_code == 401:
            raise ECFAuthError(msg, status_code=resp.status_code, detail=detail)
        if resp.status_code == 404:
            raise ECFNotFoundError(msg, status_code=resp.status_code, detail=detail)
        if resp.status_code == 422:
            raise ECFValidationError(msg, status_code=resp.status_code, detail=detail)
        if resp.status_code == 409:
            raise ECFConflictError(msg, status_code=resp.status_code, detail=detail)
        raise ECFError(msg, status_code=resp.status_code, detail=detail)


class _ECFResource(_BaseResource):
    """Operaciones sobre documentos e-CF."""

    def create(
        self,
        *,
        idempotency_key: str,
        ecf_type: str,
        payload: dict[str, Any],
        external_id: str | None = None,
        environment: str | None = None,
        mode: SubmissionMode = SubmissionMode.ONLINE,
        scheduled_for: datetime | None = None,
    ) -> ECFDocument:
        """POST ``/ecf``. Devuelve ``received``; el veredicto fiscal llega después.

        Args:
            idempotency_key: Clave estable por documento. La misma key
                devuelve el original (el payload no se compara).
            ecf_type: ``31``…``47``.
            payload: JSON DGII (``Encabezado`` / ``DetallesItems``).
            environment: ``TesteCF``, ``CerteCF`` o ``ecf``.
            mode: ``online`` (default) o ``deferred``.
        """
        data: dict[str, Any] = {
            "idempotency_key": idempotency_key,
            "ecf_type": ecf_type,
            "payload": payload,
        }
        if external_id:
            data["external_id"] = external_id
        if environment:
            data["environment"] = environment
        if scheduled_for:
            data["scheduled_for"] = scheduled_for.isoformat()

        resp = self._request("POST", "/ecf", params={"mode": mode.value}, json=data)
        return ECFDocument.model_validate(resp.json())

    def get(self, public_id: str) -> ECFDocument:
        """GET ``/ecf/{public_id}``."""
        resp = self._request("GET", f"/ecf/{public_id}")
        return ECFDocument.model_validate(resp.json())

    def list(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> EcfListResponse:
        """GET ``/ecf`` paginado. ``status`` es el valor API (``accepted``, no el enum)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        resp = self._request("GET", "/ecf", params=params)
        return EcfListResponse.model_validate(resp.json())

    def download_xml(self, public_id: str) -> bytes:
        """XML firmado."""
        resp = self._request("GET", f"/ecf/{public_id}/xml")
        return resp.content

    def download_rfce(self, public_id: str) -> bytes:
        """RFCE (resumen). Solo aplica a E32 bajo el umbral."""
        resp = self._request("GET", f"/ecf/{public_id}/rfce")
        return resp.content

    def download_pdf(self, public_id: str, *, refresh: bool = False) -> bytes:
        """Representación impresa (PDF). ``refresh=True`` regenera la RI."""
        params = {"refresh": "true"} if refresh else None
        resp = self._request("GET", f"/ecf/{public_id}/pdf", params=params, timeout=_DOWNLOAD_TIMEOUT)
        return resp.content

    def mark_incapacity(self, public_id: str) -> ECFDocument:
        resp = self._request("POST", f"/ecf/{public_id}/mark-incapacity")
        return ECFDocument.model_validate(resp.json())

    def states(self) -> dict[str, Any]:
        resp = self._request("GET", "/ecf/states")
        return resp.json()

    def status_public(self, external_id: str, *, company_rnc: str) -> ECFDocument:
        resp = self._request(
            "GET",
            f"/ecf/status-public/{external_id}",
            params={"company_rnc": company_rnc},
        )
        return ECFDocument.model_validate(resp.json())

    def submit_acecf(
        self,
        *,
        idempotency_key: str,
        encf: str,
        rnc_emisor: str,
        rnc_comprador: str,
        fecha_emision: str,
        monto_total: str,
        estado: str,
        detalle_motivo_rechazo: str | None = None,
        fecha_hora_aprobacion: str | None = None,
        environment: str | None = None,
        ecf_type: str = "31",
    ) -> AcecfResponse:
        """POST ``/ecf/acecf/submit``. ``estado`` es ``1`` (acepta) o ``2`` (rechaza)."""
        data: dict[str, Any] = {
            "idempotency_key": idempotency_key,
            "encf": encf,
            "rnc_emisor": rnc_emisor,
            "rnc_comprador": rnc_comprador,
            "fecha_emision": fecha_emision,
            "monto_total": monto_total,
            "estado": estado,
            "ecf_type": ecf_type,
        }
        if detalle_motivo_rechazo:
            data["detalle_motivo_rechazo"] = detalle_motivo_rechazo
        if fecha_hora_aprobacion:
            data["fecha_hora_aprobacion"] = fecha_hora_aprobacion
        if environment:
            data["environment"] = environment
        resp = self._request("POST", "/ecf/acecf/submit", json=data)
        return AcecfResponse.model_validate(resp.json())

    def acecf_outbound(self, **fields: Any) -> AcecfResponse:
        """POST ``/ecf/acecf/outbound``. Campos del contrato AcecfInboundRequest."""
        resp = self._request("POST", "/ecf/acecf/outbound", json=fields)
        return AcecfResponse.model_validate(resp.json())

    def acecf_inbound(self, **fields: Any) -> AcecfResponse:
        """POST ``/ecf/acecf/inbound``. Recibe un ACECF de otro facturador."""
        resp = self._request("POST", "/ecf/acecf/inbound", json=fields)
        return AcecfResponse.model_validate(resp.json())

    def cancel_sequences(
        self,
        *,
        idempotency_key: str,
        cancellations: list[dict[str, Any]],
    ) -> AnecfResponse:
        """POST ``/ecf/cancellations`` (ANECF). Hasta 10 rangos."""
        resp = self._request(
            "POST",
            "/ecf/cancellations",
            json={"idempotency_key": idempotency_key, "cancellations": cancellations},
        )
        return AnecfResponse.model_validate(resp.json())


class _ClientResource(_BaseResource):
    """Operaciones del portal cliente."""

    # -- Company --
    def company(self) -> CompanyProfile:
        """GET ``/client/company``."""
        resp = self._request("GET", "/client/company")
        return CompanyProfile.model_validate(resp.json())

    def update_company(
        self,
        *,
        address: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> CompanyProfile:
        data = {}
        if address is not None:
            data["address"] = address
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        resp = self._request("PATCH", "/client/company", json=data)
        return CompanyProfile.model_validate(resp.json())

    def summary(self) -> dict[str, Any]:
        resp = self._request("GET", "/client/summary")
        return resp.json()

    # -- Sequences --
    def sequences(
        self,
        *,
        environment: str | None = None,
        ecf_type: str | None = None,
        active_only: bool = False,
    ) -> SequenceListResponse:
        """Lista rangos e-NCF. El contrato v1 no crea rangos."""
        params: dict[str, Any] = {"active_only": str(active_only).lower()}
        if environment:
            params["environment"] = environment
        if ecf_type:
            params["ecf_type"] = ecf_type
        resp = self._request("GET", "/client/sequences", params=params)
        return SequenceListResponse.model_validate(resp.json())

    # -- Certificates --
    def list_certificates(self) -> list[CertificateInfo]:
        resp = self._request("GET", "/client/certificates")
        return [CertificateInfo.model_validate(c) for c in resp.json()]

    def upload_certificate(
        self,
        *,
        certificate_path: str,
        pin: str,
        environment: str | None = None,
    ) -> CertificateInfo:
        with open(certificate_path, "rb") as f:
            files = {"certificate": (certificate_path, f, "application/x-pkcs12")}
            data: dict[str, Any] = {"pin": pin}
            if environment:
                data["environment"] = environment
            # No usamos _request para no inyectar Content-Type json en multipart
            resp = self._http.post("/client/certificates", files=files, data=data)
            self._handle_error(resp)
        return CertificateInfo.model_validate(resp.json())

    # -- Documents --
    def documents(
        self,
        *,
        status: str | None = None,
        ecf_type: str | None = None,
        environment: str | None = None,
        encf: str | None = None,
        external_id: str | None = None,
        track_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ClientDocumentListResponse:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if ecf_type:
            params["ecf_type"] = ecf_type
        if environment:
            params["environment"] = environment
        if encf:
            params["encf"] = encf
        if external_id:
            params["external_id"] = external_id
        if track_id:
            params["track_id"] = track_id
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        resp = self._request("GET", "/client/documents", params=params)
        return ClientDocumentListResponse.model_validate(resp.json())

    def get_document(self, public_id: str) -> ClientDocument:
        resp = self._request("GET", f"/client/documents/{public_id}")
        return ClientDocument.model_validate(resp.json())

    def download_artifact(
        self,
        public_id: str,
        artifact_type: ArtifactType,
        *,
        refresh: bool = False,
    ) -> bytes:
        params = {"refresh": "true"} if refresh else None
        resp = self._request(
            "GET",
            f"/client/documents/{public_id}/artifacts/{artifact_type.value}",
            params=params,
            timeout=_DOWNLOAD_TIMEOUT,
        )
        return resp.content

    # -- Webhooks --
    def list_webhooks(self) -> list[WebhookEndpoint]:
        resp = self._request("GET", "/client/webhooks")
        return [WebhookEndpoint.model_validate(w) for w in resp.json()]

    def create_webhook(
        self,
        *,
        url: str,
        events: list[str],
        secret: str | None = None,
    ) -> WebhookCreateResponse:
        data: dict[str, Any] = {"url": url, "events": events}
        if secret:
            data["secret"] = secret
        resp = self._request("POST", "/client/webhooks", json=data)
        return WebhookCreateResponse.model_validate(resp.json())

    def update_webhook(
        self,
        public_id: str,
        *,
        url: str | None = None,
        events: list[str] | None = None,
        is_active: bool | None = None,
    ) -> WebhookEndpoint:
        data: dict[str, Any] = {}
        if url is not None:
            data["url"] = url
        if events is not None:
            data["events"] = events
        if is_active is not None:
            data["is_active"] = is_active
        resp = self._request("PATCH", f"/client/webhooks/{public_id}", json=data)
        return WebhookEndpoint.model_validate(resp.json())

    def rotate_webhook_secret(
        self,
        public_id: str,
        *,
        secret: str | None = None,
    ) -> WebhookRotateSecretResponse:
        data = {}
        if secret:
            data["secret"] = secret
        resp = self._request("POST", f"/client/webhooks/{public_id}/rotate-secret", json=data)
        return WebhookRotateSecretResponse.model_validate(resp.json())

    def delete_webhook(self, public_id: str) -> None:
        self._request("DELETE", f"/client/webhooks/{public_id}")

    def inbox(
        self,
        *,
        acked: bool | None = False,
        limit: int = 50,
        offset: int = 0,
    ) -> InboxListResponse:
        """e-CF recibidos como comprador. No son tus emisiones."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if acked is not None:
            params["acked"] = str(acked).lower()
        resp = self._request("GET", "/client/inbox", params=params)
        return InboxListResponse.model_validate(resp.json())

    def ack_inbox(self, public_id: str) -> InboxAckResponse:
        resp = self._request("POST", f"/client/inbox/{public_id}/ack")
        return InboxAckResponse.model_validate(resp.json())

    def download_inbox_xml(self, public_id: str) -> bytes:
        resp = self._request("GET", f"/client/inbox/{public_id}/xml")
        return resp.content

    def download_inbox_arecf(self, public_id: str) -> bytes:
        resp = self._request("GET", f"/client/inbox/{public_id}/arecf")
        return resp.content

    def list_artifacts(self, public_id: str) -> dict[str, Any]:
        resp = self._request("GET", f"/client/documents/{public_id}/artifacts")
        return resp.json()

    def audit_export(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> bytes:
        params: dict[str, Any] = {}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        resp = self._request(
            "GET",
            "/client/audit-export",
            params=params or None,
            timeout=_DOWNLOAD_TIMEOUT,
        )
        return resp.content

    def test_webhook(self, public_id: str) -> dict[str, Any]:
        resp = self._request("POST", f"/client/webhooks/{public_id}/test")
        return resp.json()

    def webhook_deliveries(
        self,
        public_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> WebhookDeliveryListResponse:
        resp = self._request(
            "GET",
            f"/client/webhooks/{public_id}/deliveries",
            params={"limit": limit, "offset": offset},
        )
        return WebhookDeliveryListResponse.model_validate(resp.json())


class _DGIIResource(_BaseResource):
    """Consultas públicas al padrón DGII (no requieren API key)."""

    def rnc(self, rnc: str) -> DGIIContributor:
        """GET ``/dgii/rnc/{rnc}``. No requiere API key."""
        resp = self._request("GET", f"/dgii/rnc/{rnc}")
        return DGIIContributor.model_validate(resp.json())

    def directory(self, *, rnc: str) -> dict[str, Any]:
        resp = self._request("GET", "/dgii/directory", params={"rnc": rnc})
        return resp.json()

    def status_services(self) -> dict[str, Any]:
        resp = self._request("GET", "/dgii/status/services")
        return resp.json()

    def status_maintenance(self) -> dict[str, Any]:
        resp = self._request("GET", "/dgii/status/maintenance")
        return resp.json()

    def status_environment(self, environment: str) -> dict[str, Any]:
        resp = self._request("GET", f"/dgii/status/environment/{environment}")
        return resp.json()

    def status_refresh(self) -> dict[str, Any]:
        resp = self._request("GET", "/dgii/status/refresh")
        return resp.json()
