"""Test QR publik: shape ringkas, denylist PII, batas pindai, roundtrip."""

from __future__ import annotations

import pytest

from app.services.qr_service import (
    MAX_PAYLOAD_CHARS,
    build_qr_payload,
    make_qr_png,
    parse_qr_payload,
    verify_url,
)


def _base(**over):
    args = {
        "document_id": "doc-1",
        "sig_id": "sv_abc123",
        "signer_name": "Sinta Prabowo",
        "signer_position": "Direktur",
        "signer_org": "PT Maju",
        "signed_at": "2026-09-29T10:00:00+00:00",
        "algorithm": "RSA_PSS_2048",
    }
    args.update(over)
    return build_qr_payload(**args)


def test_shape_dan_roundtrip() -> None:
    text = _base()
    data = parse_qr_payload(text)
    assert data["v"] == 1 and data["doc"] == "doc-1" and data["sig"] == "sv_abc123"
    assert data["name"] == "Sinta Prabowo" and data["pos"] == "Direktur"
    assert data["org"] == "PT Maju" and data["alg"] == "RSA_PSS_2048"
    assert data["url"] == verify_url("sv_abc123")


def test_tanpa_posisi_tetap_valid() -> None:
    data = parse_qr_payload(_base(signer_position=None))
    assert data["pos"] == ""


def test_batas_pindai() -> None:
    assert len(_base()) <= MAX_PAYLOAD_CHARS
    with pytest.raises(ValueError):
        _base(signer_name="X" * 500)


def test_denylist_pii() -> None:
    with pytest.raises(ValueError):
        _base(signer_name="bocor password rahasia")
    with pytest.raises(ValueError):
        _base(signer_org="kantor 192.168.1.1")
    # Payload lolos denylist harus bisa jadi QR.
    png = make_qr_png(_base())
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_bukan_payload_qr_ditolak() -> None:
    with pytest.raises(ValueError):
        parse_qr_payload("https://localhost:8000/api/v1/verify/sv_lama")
    with pytest.raises(ValueError):
        parse_qr_payload("bukan-json")
