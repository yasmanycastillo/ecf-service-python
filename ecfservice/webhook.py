"""Verificador de firmas HMAC-SHA256 para webhooks de ECF Service."""

import hashlib
import hmac


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verifica la firma HMAC-SHA256 de un webhook entrante.

    Args:
        payload: Cuerpo raw de la request (bytes).
        signature: Valor del header X-ECF-Signature (formato: sha256=<hex>).
        secret: Secreto compartido del webhook.

    Returns:
        True si la firma es válida.
    """
    if signature.startswith("sha256="):
        signature = signature[7:]

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
