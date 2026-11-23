import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from ..keys import load_private_key_pem, public_key_pem


def _pem(key) -> str:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def test_load_private_key_pem_accepts_escaped_line_breaks():
    pem = _pem(rsa.generate_private_key(public_exponent=65537, key_size=2048))

    assert load_private_key_pem(pem.replace("\n", "\\n")) == pem


def test_load_private_key_pem_rejects_non_rsa_keys():
    with pytest.raises(ValueError):
        load_private_key_pem(_pem(ec.generate_private_key(ec.SECP256R1())))


def test_public_key_pem_matches_private_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    assert public_key_pem(_pem(key)) == (
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
