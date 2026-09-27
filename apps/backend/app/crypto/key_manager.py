"""Key manager: generate + enkripsi AES-256-GCM private key dengan KEK dari .env.

Skema simpan (kolom KeyPair): publicKey (PEM string), encryptedPrivateKey
(base64: ciphertext+tag), privateKeyNonce (base64, 12 byte).
"""

from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.crypto import ecdsa, ed25519, rsa
from app.core.config import settings

ALGORITHMS = ("RSA_PSS_2048", "ECDSA_P256", "ED25519")
_GENERATORS = {
    "RSA_PSS_2048": rsa.generate,
    "ECDSA_P256": ecdsa.generate,
    "ED25519": ed25519.generate,
}
_SIGNERS = {
    "RSA_PSS_2048": (rsa.sign, rsa.verify),
    "ECDSA_P256": (ecdsa.sign, ecdsa.verify),
    "ED25519": (ed25519.sign, ed25519.verify),
}
NONCE_BYTES = 12


def _kek() -> bytes:
    raw = settings.kek_secret.strip()
    try:
        key = bytes.fromhex(raw)
    except ValueError as exc:
        raise RuntimeError("KEK_SECRET harus 64-char hex (32 byte).") from exc
    if len(key) != 32:
        raise RuntimeError("KEK_SECRET harus 32 byte untuk AES-256-GCM.")
    return key


def generate_keypair(algorithm: str) -> tuple[str, str, str]:
    """Return (public_pem_str, enc_priv_b64, nonce_b64). Raise ValueError bila algo tak dikenal."""
    if algorithm not in _GENERATORS:
        raise ValueError(f"Algoritma tidak didukung: {algorithm}")
    priv_pem, pub_pem = _GENERATORS[algorithm]()
    enc, nonce = encrypt_private(priv_pem)
    return pub_pem.decode("utf-8"), enc, nonce


def encrypt_private(private_pem: bytes) -> tuple[str, str]:
    nonce = os.urandom(NONCE_BYTES)
    ct = AESGCM(_kek()).encrypt(nonce, private_pem, associated_data=None)
    return base64.b64encode(ct).decode(), base64.b64encode(nonce).decode()


def decrypt_private(enc_b64: str, nonce_b64: str) -> bytes:
    ct = base64.b64decode(enc_b64)
    nonce = base64.b64decode(nonce_b64)
    return AESGCM(_kek()).decrypt(nonce, ct, associated_data=None)


def sign_with(algorithm: str, enc_priv_b64: str, nonce_b64: str, message: bytes) -> bytes:
    if algorithm not in _SIGNERS:
        raise ValueError(f"Algoritma tidak didukung: {algorithm}")
    priv_pem = decrypt_private(enc_priv_b64, nonce_b64)
    sign_fn, _ = _SIGNERS[algorithm]
    return sign_fn(priv_pem, message)


def verify_with(algorithm: str, public_pem_str: str, message: bytes, signature: bytes) -> bool:
    if algorithm not in _SIGNERS:
        raise ValueError(f"Algoritma tidak didukung: {algorithm}")
    _, verify_fn = _SIGNERS[algorithm]
    return verify_fn(public_pem_str.encode("utf-8"), message, signature)
