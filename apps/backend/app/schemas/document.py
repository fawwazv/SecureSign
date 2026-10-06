"""Response dokumen & sign-request & notifikasi — camelCase persis openapi.yaml."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    storage_path: str = Field(alias="storagePath")
    file_hash: str = Field(alias="fileHash")
    metadata: dict[str, Any] = {}
    status: str
    version: int
    page_count: int = Field(default=1, alias="pageCount")
    page_width: float | None = Field(default=None, alias="pageWidth")
    page_height: float | None = Field(default=None, alias="pageHeight")
    qr_placements: list[dict[str, Any]] = Field(default_factory=list, alias="qrPlacements")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


def to_document_response(doc: object) -> dict:
    meta = doc.metadata  # type: ignore[attr-defined]
    placements = getattr(doc, "qrPlacements", []) or []
    return DocumentResponse(
        id=doc.id,  # type: ignore[attr-defined]
        title=doc.title,  # type: ignore[attr-defined]
        description=doc.description,  # type: ignore[attr-defined]
        storagePath=doc.storagePath,  # type: ignore[attr-defined]
        fileHash=doc.fileHash,  # type: ignore[attr-defined]
        metadata=dict(meta) if isinstance(meta, dict) else {},
        status=str(doc.status),  # type: ignore[attr-defined]
        version=doc.version,  # type: ignore[attr-defined]
        pageCount=int(getattr(doc, "pageCount", 1) or 1),
        pageWidth=getattr(doc, "pageWidth", None),
        pageHeight=getattr(doc, "pageHeight", None),
        qrPlacements=list(placements) if isinstance(placements, list) else [],
        createdAt=str(doc.createdAt),  # type: ignore[attr-defined]
        updatedAt=str(doc.updatedAt),  # type: ignore[attr-defined]
    ).model_dump(by_alias=True, mode="json")


class SignRequestResponse(BaseModel):
    id: str
    document_id: str = Field(alias="documentId")
    signer_id: str = Field(alias="signerId")
    status: str
    message: str | None = None
    reject_reason: str | None = Field(default=None, alias="rejectReason")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


def to_sign_request_response(sr: object) -> dict:
    return SignRequestResponse(
        id=sr.id,  # type: ignore[attr-defined]
        documentId=sr.documentId,  # type: ignore[attr-defined]
        signerId=sr.signerId,  # type: ignore[attr-defined]
        status=str(sr.status),  # type: ignore[attr-defined]
        message=sr.message,  # type: ignore[attr-defined]
        rejectReason=sr.rejectReason,  # type: ignore[attr-defined]
        createdAt=str(sr.createdAt),  # type: ignore[attr-defined]
        updatedAt=str(sr.updatedAt),  # type: ignore[attr-defined]
    ).model_dump(by_alias=True, mode="json")


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    is_read: bool = Field(alias="isRead")
    created_at: str = Field(alias="createdAt")


def to_notification_response(n: object) -> dict:
    return NotificationResponse(
        id=n.id,  # type: ignore[attr-defined]
        type=n.type,  # type: ignore[attr-defined]
        title=n.title,  # type: ignore[attr-defined]
        message=n.message,  # type: ignore[attr-defined]
        isRead=n.isRead,  # type: ignore[attr-defined]
        createdAt=str(n.createdAt),  # type: ignore[attr-defined]
    ).model_dump(by_alias=True, mode="json")
