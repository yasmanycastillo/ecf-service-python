# emite.do SDK — Python

SDK oficial para [api.emite.do](https://api.emite.do). El mismo `POST /api/v1/ecf` cubre **E31–E47**.

Guía: [docs.emite.do/sdks/python](https://docs.emite.do/sdks/python) · API: [docs.emite.do](https://docs.emite.do)

## Instalación

```bash
pip install ecfservice
```

## Inicio rápido

```python
from datetime import date
from ecfservice import ECFClient

with ECFClient(api_key="...") as client:
    doc = client.ecf.create(
        idempotency_key="INV-2026-0001",
        ecf_type="31",
        environment="TesteCF",
        payload={
            "Encabezado": {
                "Version": "1.0",
                "IdDoc": {
                    "TipoeCF": "31",
                    "eNCF": "E310000000001",
                    "FechaVencimientoSecuencia": "31-12-2028",
                    "IndicadorMontoGravado": 0,
                    "TipoIngresos": "01",
                    "TipoPago": "1",
                },
                "Emisor": {
                    "RNCEmisor": "130478031",
                    "RazonSocialEmisor": "Mi Empresa SRL",
                    "DireccionEmisor": "AV. DEMO 1",
                    "FechaEmision": date.today().strftime("%d-%m-%Y"),
                },
                "Comprador": {
                    "RNCComprador": "131098193",
                    "RazonSocialComprador": "Cliente SRL",
                },
                "Totales": {
                    "MontoGravadoTotal": 10000.0,
                    "MontoGravadoI1": 10000.0,
                    "ITBIS1": 18,
                    "TotalITBIS": 1800.0,
                    "TotalITBIS1": 1800.0,
                    "MontoTotal": 11800.0,
                },
            },
            "DetallesItems": {
                "Item": [
                    {
                        "NumeroLinea": 1,
                        "IndicadorFacturacion": 1,
                        "NombreItem": "SERVICIO DEMO",
                        "IndicadorBienoServicio": 2,
                        "CantidadItem": 1.0,
                        "UnidadMedida": "43",
                        "PrecioUnitarioItem": 10000.0,
                        "MontoItem": 10000.0,
                    }
                ]
            },
        },
    )
    print(doc.public_id, doc.status)  # received — el veredicto fiscal llega después
    doc = client.ecf.get(doc.public_id)
    xml = client.ecf.download_xml(doc.public_id)
```

`ecf_type` acepta `31` `32` `33` `34` `41` `43` `44` `45` `46` `47`. Cambia `TipoeCF` y el e-NCF (`E32…`, `E47…`) al tipo.

Misma `idempotency_key` → `200` del original (el payload no se compara).

## Builder

```python
from ecfservice import ECFPayloadBuilder

payload = (
    ECFPayloadBuilder(ecf_type="31")
    .id_doc(eNCF="E310000000001", FechaVencimientoSecuencia="31-12-2028")
    .emisor(RNCEmisor="130478031", RazonSocialEmisor="Mi Empresa SRL", FechaEmision="15-08-2026")
    .comprador(RNCComprador="131098193", RazonSocialComprador="Cliente SRL")
    .totales(MontoTotal=11800.0, TotalITBIS=1800.0)
    .add_item({"NumeroLinea": 1, "NombreItem": "Servicio", "MontoItem": 10000.0})
    .build()
)
```

Pone `TipoeCF` (no `TipoEcf`). `FechaEmision` va en `Emisor`.

## Empresa, rangos, inbox

```python
profile = client.client.company()
seqs = client.client.sequences(active_only=True)
inbox = client.client.inbox(acked=False)
client.client.ack_inbox(inbox.items[0].public_id)
```

Los rangos se listan; no se crean por API.

## Comunicaciones Emite

Feed de avisos de soporte (`GET /notices/changes`). No es el calendario DGII
(`client.dgii.status_maintenance()`). Un feed vacío no resuelve nada; un
`409 cursor_expired` exige bootstrap de nuevo y retirar réplicas ausentes
sin marcarlas resueltas.

```python
feed = client.notices.changes()  # bootstrap
cursor = feed.next_cursor
later = client.notices.changes(cursor=cursor)
notice = client.notices.get(feed.changes[0].notice.id)
```

## ACECF y ANECF

```python
client.ecf.submit_acecf(
    idempotency_key="ac-001",
    encf="E310000000001",
    rnc_emisor="130478031",
    rnc_comprador="131098193",
    fecha_emision="15-08-2026",
    monto_total="11800.00",
    estado="1",
)
client.ecf.cancel_sequences(
    idempotency_key="an-001",
    cancellations=[{
        "ecf_type": "31",
        "sequence_from": "E310000000010",
        "sequence_to": "E310000000012",
        "quantity": 3,
    }],
)
```

## Webhooks

Hoy el service notifica `accepted`, `conditionally_accepted` y `rejected`.

```python
wh = client.client.create_webhook(
    url="https://mi-app.example/webhooks/ecf",
    events=["accepted", "conditionally_accepted", "rejected"],
)
from ecfservice.webhook import verify_webhook_signature
ok = verify_webhook_signature(request_body, request.headers["X-ECF-Signature"], wh.secret)
```

## Salud y padrón (sin API key)

```python
client = ECFClient()  # key opcional
print(client.health().status)
print(client.dgii.rnc("130478031").razon_social)
```

## Errores

El service responde `{ "detail": "..." }` (FastAPI).

```python
from ecfservice import ECFAuthError, ECFValidationError, ECFConflictError, ECFNotFoundError
```

- `401` → `ECFAuthError`
- `404` → `ECFNotFoundError`
- `409` e-NCF usado → `ECFConflictError`
- `422` payload / rango / P12 / header faltante → `ECFValidationError`

## Qué no hace este SDK

- No valida el XSD DGII (lo hace el service).
- No crea rangos e-NCF; solo los lista.
- El `201` de `create` es `received`, no el veredicto fiscal. Usa webhooks o `client.ecf.get`.

## Licencia

MIT
