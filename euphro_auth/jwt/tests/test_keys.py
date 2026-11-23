import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from ..keys import key_id, load_private_key_pem


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


def test_key_id_is_the_rfc_7638_thumbprint():
    # Example of RFC 7638, section 3.1.
    n = (
        "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFF"
        "xuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt"
        "7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6"
        "qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINH"
        "aQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw"
    )
    raw = base64.urlsafe_b64decode(n + "=" * (-len(n) % 4))
    key = rsa.RSAPublicNumbers(65537, int.from_bytes(raw, "big")).public_key()

    assert key_id(key) == "NzbLsXh8uDCcd-6MNwXF4W_7noWXFZAfHkxZsRGC9Xs"
