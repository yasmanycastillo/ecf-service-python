"""Modelos Pydantic para el SDK ECF Service."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from ecfservice.constants import (
    ArtifactType,
    ECFState,
    ECFType,
    Environment,
    SubmissionMode,
)


class ECFCreateRequest(BaseModel):
    """Payload para crear un documento e-CF."""

    idempotency_key: str = Field(..., min_length=1, max_length=100)
    ecf_type: ECFType
    payload: dict[str, Any]
    external_id: str | None = Field(default=None, max_length=100)
    environment: Environment | None = None
    scheduled_for: datetime | None = None


class ECFDocument(BaseModel):
    """Documento e-CF con estado y metadatos."""

    public_id: str
    idempotency_key: str
    external_id: str | None = None
    ecf_type: str
    environment: str
    encf: str | None = None
    status: ECFState
    scheduled_for: datetime | None = None
    dgii_track_id: str | None = None
    dgii_security_code: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class EcfListResponse(BaseModel):
    items: list[ECFDocument]
    total: int
    limit: int
    offset: int


class ArtifactLinks(BaseModel):
    generated_xml: bool
    signed_xml: bool
    rfce: bool
    ri: bool
    dgii_response: bool
    links: dict[str, str] | None = None
    retention_years: int = 10


class ClientDocument(BaseModel):
    """Documento e-CF con artefactos para la app cliente."""

    public_id: str
    idempotency_key: str
    external_id: str | None = None
    ecf_type: str
    environment: str
    encf: str | None = None
    status: ECFState
    scheduled_for: datetime | None = None
    dgii_track_id: str | None = None
    dgii_security_code: str | None = None
    electronic_stamp: str | None = None
    sign_date: str | None = None
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
    dgii_response: dict[str, Any] | None = None
    artifacts: ArtifactLinks | None = None
    created_at: datetime
    updated_at: datetime


class ClientDocumentListResponse(BaseModel):
    items: list[ClientDocument]
    total: int
    limit: int
    offset: int


class CertificateSummary(BaseModel):
    """Certificado activo dentro del perfil de empresa."""

    active: bool
    environment: str | None = None
    expires_at: datetime | None = None
    days_until_expiry: int | None = None
    subject_cn: str | None = None
    serial_number: str | None = None


class CompanyProfile(BaseModel):
    """Perfil de empresa."""

    public_id: str
    rnc: str
    name: str
    trade_name: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    default_environment: str
    is_active: bool
    certificate: CertificateSummary | None = None
    active_ncf_types: list[str] = Field(default_factory=list)


class SequenceInfo(BaseModel):
    """Información de secuencia eNCF."""

    ecf_type: str
    environment: str
    range_start: int
    range_end: int
    next_sequence: int
    used: int
    available: int
    total: int
    valid_until: date | None = None
    is_active: bool
    state: str


class SequenceListResponse(BaseModel):
    items: list[SequenceInfo]
    total: int


class CertificateInfo(BaseModel):
    """Información de certificado digital."""

    public_id: str
    alias: str
    environment: str
    subject_cn: str | None = None
    issuer: str | None = None
    serial_number: str | None = None
    not_before: datetime | None = None
    not_after: datetime | None = None
    is_active: bool
    uploaded_at: datetime | None = None
    days_until_expiry: int | None = None


class WebhookEndpoint(BaseModel):
    """Endpoint de webhook."""

    public_id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


class WebhookCreateResponse(BaseModel):
    """Respuesta al crear un webhook (secret solo se muestra una vez)."""

    public_id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime
    secret: str
    only_shown_once: bool


class WebhookRotateSecretResponse(BaseModel):
    """Respuesta al rotar secreto de webhook."""

    public_id: str
    secret: str
    only_shown_once: bool


class WebhookDelivery(BaseModel):
    """Entrega de webhook."""

    id: int
    event: str
    attempt: int
    status_code: int | None = None
    response_excerpt: str | None = None
    succeeded: bool | None = None
    sent_at: datetime


class WebhookDeliveryListResponse(BaseModel):
    items: list[WebhookDelivery]
    total: int
    limit: int
    offset: int


class DGIIContributor(BaseModel):
    """Contribuyente del padrón DGII."""

    rnc: str
    razon_social: str
    nombre_comercial: str | None = None
    actividad_economica: str | None = None
    estado: str | None = None
    regimen_pagos: str | None = None


class InboxItem(BaseModel):
    public_id: str
    encf: str | None = None
    ecf_type: str
    environment: str
    status: str
    rnc_emisor: str | None = None
    rnc_comprador: str | None = None
    razon_social_emisor: str | None = None
    monto_total: str | None = None
    fecha_emision: str | None = None
    acked: bool
    xml_available: bool
    arecf_available: bool
    created_at: datetime


class InboxListResponse(BaseModel):
    items: list[InboxItem]
    total: int
    limit: int
    offset: int


class InboxAckResponse(BaseModel):
    public_id: str
    acked: bool
    acked_at: datetime


class AcecfResponse(BaseModel):
    public_id: str
    status: str
    message: str
    dgii_response: dict[str, Any] | None = None


class AnecfResponse(BaseModel):
    public_id: str
    status: str
    message: str


class HealthStatus(BaseModel):
    status: str
    checks: dict[str, Any] | None = None
    version: str | None = None
