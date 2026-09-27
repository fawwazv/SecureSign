"""RSA-2048 PSS (salt 32, SHA-256) — prd.md §8."""

from __future__ import annotations

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

PSS_SALT_LENGTH = 32


def generate() -> tuple[bytes, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return _priv_bytes(key), _pub_bytes(key)


def sign(private_pem: bytes, message: bytes) -> bytes:
    key = serialization.load_pem_private_key(private_pem, password=None)
    assert isinstance(key, rsa.RSAPrivateKey)
    return key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=PSS_SALT_LENGTH),
        hashes.SHA256(),
    )


def verify(public_pem: bytes, message: bytes, signature: bytes) -> bool:
    key = serialization.load_pem_public_key(public_pem)
    assert isinstance(key, rsa.RSAPublicKey)
    try:
        key.verify(
            signature,
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=PSS_SALT_LENGTH),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False


def _priv_bytes(key: rsa.RSAPrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _pub_bytes(key: rsa.RSAPrivateKey) -> bytes:
    return key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
