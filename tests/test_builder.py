from ecfservice.builder import ECFPayloadBuilder


def test_builder_uses_tipoecf_and_maps_aliases():
    payload = (
        ECFPayloadBuilder(ecf_type="32")
        .id_doc(eNCF="E320000000001")
        .emisor(RNC="130478031", RazonSocial="Demo", FechaEmision="15-08-2026")
        .comprador(RNC="131098193", RazonSocial="Cliente")
        .totales(MontoTotal=100.0)
        .add_item({"NumeroLinea": 1, "Descripcion": "Item", "MontoItem": 100.0})
        .build()
    )
    id_doc = payload["Encabezado"]["IdDoc"]
    assert id_doc["TipoeCF"] == "32"
    assert "TipoEcf" not in id_doc
    assert payload["Encabezado"]["Emisor"]["RNCEmisor"] == "130478031"
    assert payload["Encabezado"]["Emisor"]["FechaEmision"] == "15-08-2026"
    assert payload["Encabezado"]["Comprador"]["RNCComprador"] == "131098193"
    assert payload["DetallesItems"]["Item"][0]["NombreItem"] == "Item"
    assert "Descripcion" not in payload["DetallesItems"]["Item"][0]


def test_builder_keeps_canonical_field_names():
    payload = (
        ECFPayloadBuilder(ecf_type="31")
        .id_doc(eNCF="E310000000001", TipoeCF="31")
        .emisor(RNCEmisor="130478031", RazonSocialEmisor="Demo")
        .add_item({"NumeroLinea": 1, "NombreItem": "Servicio", "MontoItem": 1})
        .build()
    )
    assert payload["Encabezado"]["IdDoc"]["TipoeCF"] == "31"
    assert payload["Encabezado"]["Emisor"]["RNCEmisor"] == "130478031"
    assert payload["DetallesItems"]["Item"][0]["NombreItem"] == "Servicio"
