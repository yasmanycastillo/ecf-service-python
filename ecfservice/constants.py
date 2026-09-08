"""Constantes y enums del dominio DGII para facturación electrónica."""

from __future__ import annotations

from enum import Enum, IntEnum


class ECFType(str, Enum):
    E31 = "31"
    E32 = "32"
    E33 = "33"
    E34 = "34"
    E41 = "41"
    E43 = "43"
    E44 = "44"
    E45 = "45"
    E46 = "46"
    E47 = "47"


class ECFState(str, Enum):
    RECEIVED = "received"
    DEFERRED = "deferred"
    VALIDATED = "validated"
    SIGNED = "signed"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    CONDITIONALLY_ACCEPTED = "conditionally_accepted"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CONTINGENCY = "contingency"
    INCAPACITY = "incapacity"


class Environment(str, Enum):
    TEST = "TesteCF"
    CERT = "CerteCF"
    PROD = "ecf"


class NoticeCategory(str, Enum):
    DGII_INCIDENT = "dgii_incident"
    EMITE_INCIDENT = "emite_incident"
    ANNOUNCEMENT = "announcement"
    ACTION_REQUIRED = "action_required"


class NoticeSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NoticeState(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    EXPIRED = "expired"
    RESOLVED = "resolved"
    WITHDRAWN = "withdrawn"


class NoticeOperation(str, Enum):
    UPSERT = "upsert"
    REVOKE = "revoke"


class SubmissionMode(str, Enum):
    ONLINE = "online"
    DEFERRED = "deferred"


class ArtifactType(str, Enum):
    GENERATED_XML = "generated-xml"
    SIGNED_XML = "signed-xml"
    RFCE = "rfce"
    RI = "ri"
    DGII_RESPONSE = "dgii-response"


class PaymentType(IntEnum):
    CASH = 1
    CREDIT = 2
    GRATIS = 3


class IncomeType(str, Enum):
    OPERATIONAL = "01"
    FINANCIAL = "02"
    EXTRAORDINARY = "03"
    LEASING = "04"
    ASSET_SALE = "05"
    OTHER = "06"


class BillingIndicator(IntEnum):
    NOT_BILLABLE_18 = 0
    ITBIS_18 = 1
    ITBIS_16 = 2
    ZERO_RATED = 3
    EXEMPT = 4


class ModificationCode(IntEnum):
    TOTAL_CANCEL = 1
    TEXT_CORRECTION = 2
    AMOUNT_CORRECTION = 3
    CONTINGENCY_REPLACE = 4
    RFCE_REFERENCE = 5


class IndicadorMontoGravado(IntEnum):
    NO_INCLUDE = 0
    PRICE_INCLUDE = 1


class BienOServicio(IntEnum):
    GOOD = 1
    SERVICE = 2


class TipoAjuste(str, Enum):
    DISCOUNT = "D"
    SURCHARGE = "R"


class TipoValor(str, Enum):
    FIXED = "$"
    PERCENTAGE = "%"
