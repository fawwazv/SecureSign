"""Agregator router /api/v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.keys import router as keys_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.sign_requests import router as sign_requests_router
from app.api.v1.users import router as users_router
from app.api.v1.verify import audit_router
from app.api.v1.verify import router as verify_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(keys_router)
router.include_router(documents_router)
router.include_router(sign_requests_router)
router.include_router(notifications_router)
router.include_router(verify_router)
router.include_router(audit_router)
