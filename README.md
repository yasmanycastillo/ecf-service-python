# ECF Service SDK — Python

SDK oficial para integrar con [ECF Service](https://ecfservice.do), plataforma de facturación electrónica e-CF certificada DGII para República Dominicana.

## Instalación

```bash
pip install ecfservice
```

## Inicio rápido

```python
from ecfservice import ECFClient

with ECFClient(api_key="ecf_tu_api_key") as client:
    # Crear factura electrónica (e-CF tipo 31)
    doc = client.ecf.create(
        idempotency_key="INV-2026-0001",
        ecf_type="31",
        payload={
            "Encabezado": {
                "Version": "1.0",
                "IdDoc": {"eNCF": "E310000000001"},
                "Emisor": {"RNC": "130478031", "RazonSocial": "Mi Empresa SRL"},
                "Comprador": {"RNC": "123456789", "RazonSocial": "Cliente S.A."},
                "Totales": {"MontoTotal": 1000.00, "TotalITBIS": 180.00},
            },
            "DetallesItems": {
                "Item": [{"NumeroLinea": 1, "Descripcion": "Servicio", "MontoItem": 1000.00}]
            },
        },
    )
    print(f"Documento: {doc.public_id} — Estado: {doc.status}")

    # Consultar estado
    doc = client.ecf.get(doc.public_id)

    # Descargar XML firmado
    xml_bytes = client.ecf.download_xml(doc.public_id)

    # Descargar PDF (Representación Impresa)
    pdf_bytes = client.ecf.download_pdf(doc.public_id)
```

## Perfil de empresa

```python
profile = client.client.company()
print(f"RNC: {profile.rnc} — Nombre: {profile.name}")
```

## Secuencias eNCF

```python
result = client.client.sequences(active_only=True)
for seq in result.items:
    print(f"Tipo {seq.ecf_type}: {seq.next_sequence} de {seq.range_end} — Disponibles: {seq.available}")
```

## Webhooks

```python
# Crear webhook
wh = client.client.create_webhook(
    url="https://mi-app.com/webhooks/ecf",
    events=["accepted", "rejected"],
)
print(f"Secreto (guardar ahora): {wh.secret}")  # Solo se muestra una vez

# Verificar firma entrante
from ecfservice.webhook import verify_webhook_signature

is_valid = verify_webhook_signature(
    payload=request.body,
    signature=request.headers["X-ECF-Signature"],
    secret=wh_secret,
)
```

## Consultas DGII (públicas, sin API key)

```python
from ecfservice import ECFClient

client = ECFClient(api_key="any", base_url="http://localhost:8000/api/v1")
contributor = client.dgii.rnc("130478031")
print(f"Nombre: {contributor.razon_social} — Estado: {contributor.estado}")
```

## Manejo de errores

```python
from ecfservice import ECFClient, ECFAuthError, ECFValidationError, ECFNotFoundError

with ECFClient(api_key="ecf_...") as client:
    try:
        doc = client.ecf.create(...)
    except ECFAuthError:
        print("API key inválida o expirada")
    except ECFValidationError as e:
        print(f"Error de validación: {e.detail}")
    except ECFNotFoundError:
        print("Recurso no encontrado")
```

## Licencia

MIT
