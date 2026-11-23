"""RSA key used to sign the JSON web tokens Euphrosyne issues.

Only Euphrosyne holds the private key: other services, such as the Tools API,
verify tokens with the public key. Imported by the settings, so it must not
depend on Django being set up.
"""

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


def public_key_pem(private_key_pem: str) -> str:
    """Return the PEM of the public key matching a private key PEM."""
    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    return (
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
