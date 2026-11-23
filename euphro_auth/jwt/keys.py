"""RSA key used to sign the JSON web tokens Euphrosyne issues.

Only Euphrosyne holds the private key: other services, such as the Tools API,
verify tokens with the public keys published in /.well-known/jwks.json.
Imported by the settings, so it must not depend on Django being set up.
"""

import base64
import hashlib
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def load_private_key_pem(value: str) -> str:
    """Return the PEM of an RSA private key given in an environment variable.

    Line breaks may be written as literal ``\\n`` when the environment does not
    allow multi-line values."""
    pem = value.replace("\\n", "\n").strip() + "\n"
    key = serialization.load_pem_private_key(pem.encode(), password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ValueError("The token signing key must be an RSA private key.")
    return pem


def key_id(public_key: rsa.RSAPublicKey) -> str:
    """RFC 7638 thumbprint of an RSA public key: the ``kid`` allauth publishes
    for it in /.well-known/jwks.json."""
    numbers = public_key.public_numbers()
    jwk = {"e": _b64_uint(numbers.e), "kty": "RSA", "n": _b64_uint(numbers.n)}
    digest = hashlib.sha256(
        json.dumps(jwk, separators=(",", ":"), sort_keys=True).encode()
    ).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _b64_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
