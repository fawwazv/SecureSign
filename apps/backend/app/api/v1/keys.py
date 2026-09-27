"""Endpoint keys — generate/list (Signer), revoke (Super Admin)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from prisma import Prisma

from app.api.deps import require_role
from app.core.exceptions import AppError
from app.crypto.key_manager import generate_keypair
from app.models.prisma_client import get_db
from app.schemas.key import GenerateKeyRequest, KeyPairResponse, to_key_response

router = APIRouter(tags=["keys"])

SignerOnly = Annotated[dict[str, Any], Depends(require_role("SIGNER"))]
AdminOnly = Annotated[dict[str, Any], Depends(require_role("SUPER_ADMIN"))]


@router.post(
    "/keys/generate", response_model=KeyPairResponse, response_model_by_alias=True, status_code=201
)
async def generate_key(
    payload: GenerateKeyRequest,
    user: SignerOnly,
    db: Annotated[Prisma, Depends(get_db)],
):
    try:
        public_pem, enc_priv, nonce = generate_keypair(payload.algorithm)
    except ValueError as exc:
        raise AppError("UNSUPPORTED_ALGORITHM", str(exc), status=400) from exc
    key = await db.keypair.create(
        data={
            "ownerId": user["id"],
            "algorithm": payload.algorithm,
            "publicKey": public_pem,
            "encryptedPrivateKey": enc_priv,
            "privateKeyNonce": nonce,
        }
    )
    return to_key_response(key)


@router.get("/keys", response_model=dict)
async def list_keys(user: SignerOnly, db: Annotated[Prisma, Depends(get_db)]):
    keys = await db.keypair.find_many(where={"ownerId": user["id"]}, order={"createdAt": "desc"})
    return {"data": [to_key_response(k) for k in keys]}


@router.post("/keys/{id}/revoke", response_model=KeyPairResponse, response_model_by_alias=True)
async def revoke_key(
    id: str,
    _admin: AdminOnly,
    db: Annotated[Prisma, Depends(get_db)],
):
    key = await db.keypair.find_unique(where={"id": id})
    if key is None:
        raise AppError("NOT_FOUND", "Key tidak ditemukan.", status=404)
    if key.revoked:
        return to_key_response(key)
    updated = await db.keypair.update(
        where={"id": id},
        data={"revoked": True, "revokedAt": datetime.now(UTC)},
    )
    return to_key_response(updated)
