"""Response signature — camelCase persis kontrak openapi.yaml."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SignatureResponse(BaseModel):
    id: str
    document_id: str = Field(alias="documentId")
    signer_id: str = Field(alias="signerId")
    key_pair_id: str = Field(alias="keyPairId")
    algorithm: str
    signature_value: str = Field(alias="signatureValue")
    signed_hash: str = Field(alias="signedHash")
    canonical_metadata: str = Field(alias="canonicalMetadata")
    qr_payload: str = Field(alias="qrPayload")
    signed_pdf_path: str | None = Field(default=None, alias="signedPdfPath")
    sig_format: str = Field(default="LEGACY", alias="sigFormat")
    byte_range: str | None = Field(default=None, alias="byteRange")
    signer_position: str | None = Field(default=None, alias="signerPosition")
    created_at: str = Field(alias="createdAt")


def to_signature_response(sig: object) -> dict:
    return SignatureResponse(
        id=sig.id,  # type: ignore[attr-defined]
        documentId=sig.documentId,  # type: ignore[attr-defined]
        signerId=sig.signerId,  # type: ignore[attr-defined]
        keyPairId=sig.keyPairId,  # type: ignore[attr-defined]
        algorithm=str(sig.algorithm),  # type: ignore[attr-defined]
        signatureValue=sig.signatureValue,  # type: ignore[attr-defined]
        signedHash=sig.signedHash,  # type: ignore[attr-defined]
        canonicalMetadata=sig.canonicalMetadata,  # type: ignore[attr-defined]
        qrPayload=sig.qrPayload,  # type: ignore[attr-defined]
        signedPdfPath=sig.signedPdfPath,  # type: ignore[attr-defined]
        sigFormat=str(getattr(sig, "sigFormat", "LEGACY")),
        byteRange=getattr(sig, "byteRange", None),
        signerPosition=getattr(sig, "signerPosition", None),
        createdAt=str(sig.createdAt),  # type: ignore[attr-defined]
    ).model_dump(by_alias=True, mode="json")
