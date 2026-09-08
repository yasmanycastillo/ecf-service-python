"""Excepciones del SDK ECF Service."""


class ECFError(Exception):
    """Error base del SDK."""

    def __init__(self, message: str, status_code: int | None = None, detail: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class ECFAuthError(ECFError):
    """API key inválida, expirada o revocada (401)."""


class ECFNotFoundError(ECFError):
    """Recurso no encontrado (404)."""


class ECFValidationError(ECFError):
    """Error de validación de payload o datos (422)."""


class ECFConflictError(ECFError):
    """Conflicto (409): unicidad, idempotencia o cursor de avisos vencido."""
