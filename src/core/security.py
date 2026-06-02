import hashlib
import hmac


def pseudonymize(value: str, key: str, length: int = 16) -> str:
    # HMAC-SHA256 tronqué.
    # Même entrée + même clé = même hash, pratique pour les jointures sans exposer l'identité.
    digest = hmac.new(
        key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:length]
