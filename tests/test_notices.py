import httpx
import pytest
import respx
from ecfservice import ECFClient, ECFConflictError, NoticeOperation
from ecfservice.exceptions import ECFError

FEED = {
    "schema_version": 1,
    "changes": [
        {
            "event_id": "01JEVENTOPAQUE0000000000001",
            "operation": "upsert",
            "company_id": "01JCOMPANYOPAQUE0000000001",
            "notice": {
                "id": "01JNOTICEOPAQUE000000000001",
                "revision": 2,
                "category": "dgii_incident",
                "severity": "warning",
                "title": "Recepción DGII intermitente",
                "body": "Se observan retrasos en producción.",
                "state": "active",
                "source": "support",
                "environments": ["prod"],
                "starts_at": "2026-09-08T14:00:00Z",
                "expires_at": None,
                "resolved_at": None,
                "resolution_note": None,
                "updated_at": "2026-09-08T14:05:00Z",
            },
        },
        {
            "event_id": "01JEVENTOPAQUE0000000000002",
            "operation": "revoke",
            "company_id": "01JCOMPANYOPAQUE0000000002",
            "notice": {"id": "01JNOTICEOPAQUE000000000001"},
        },
    ],
    "next_cursor": "opaque_checkpoint",
    "has_more": False,
    "checked_at": "2026-09-08T14:06:00Z",
}


@respx.mock
def test_notice_changes_bootstrap():
    respx.get("https://api.emite.do/api/v1/notices/changes").mock(
        return_value=httpx.Response(200, json=FEED)
    )
    with ECFClient(api_key="ecf_test") as client:
        feed = client.notices.changes()
    assert feed.schema_version == 1
    assert feed.has_more is False
    assert feed.next_cursor == "opaque_checkpoint"
    assert feed.changes[0].operation == NoticeOperation.UPSERT
    assert feed.changes[0].notice.title.startswith("Recepción")
    assert "audience" not in feed.changes[0].notice.model_dump()
    assert feed.changes[1].operation == NoticeOperation.REVOKE
    assert feed.changes[1].notice.id == "01JNOTICEOPAQUE000000000001"
    assert feed.changes[1].notice.title is None


@respx.mock
def test_notice_changes_sends_cursor():
    route = respx.get("https://api.emite.do/api/v1/notices/changes").mock(
        return_value=httpx.Response(200, json={**FEED, "changes": []})
    )
    with ECFClient(api_key="ecf_test") as client:
        feed = client.notices.changes(cursor="opaque_checkpoint", limit=50)
    assert feed.changes == []
    assert "cursor=opaque_checkpoint" in str(route.calls.last.request.url)
    assert "limit=50" in str(route.calls.last.request.url)


@respx.mock
def test_notice_get_detail():
    respx.get("https://api.emite.do/api/v1/notices/01JNOTICEOPAQUE000000000001").mock(
        return_value=httpx.Response(200, json=FEED["changes"][0]["notice"])
    )
    with ECFClient(api_key="ecf_test") as client:
        notice = client.notices.get("01JNOTICEOPAQUE000000000001")
    assert notice.state == "active"
    assert notice.revision == 2


@respx.mock
def test_cursor_expired_raises_conflict():
    respx.get("https://api.emite.do/api/v1/notices/changes").mock(
        return_value=httpx.Response(
            409,
            json={
                "detail": {
                    "code": "cursor_expired",
                    "message": "Cursor vencido; repetir bootstrap",
                    "request_id": "01JREQ",
                }
            },
        )
    )
    with ECFClient(api_key="ecf_test") as client:
        with pytest.raises(ECFConflictError) as err:
            client.notices.changes(cursor="stale")
    assert err.value.status_code == 409
    assert "Cursor vencido" in str(err.value)


@respx.mock
def test_notices_disabled_raises():
    respx.get("https://api.emite.do/api/v1/notices/changes").mock(
        return_value=httpx.Response(
            503,
            json={"detail": {"code": "notices_disabled", "message": "Consumo de avisos desactivado"}},
        )
    )
    with ECFClient(api_key="ecf_test") as client:
        with pytest.raises(ECFError) as err:
            client.notices.changes()
    assert err.value.status_code == 503
    assert "desactivado" in str(err.value)
