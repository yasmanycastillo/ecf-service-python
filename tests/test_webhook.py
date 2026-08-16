from ecfservice.webhook import verify_webhook_signature


def test_verify_webhook_signature_accepts_prefixed_header():
    body = b'{"event":"accepted"}'
    secret = "super-secret-value"
    import hashlib
    import hmac

    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, f"sha256={digest}", secret)
    assert verify_webhook_signature(body, digest, secret)
    assert not verify_webhook_signature(body, "sha256=deadbeef", secret)
