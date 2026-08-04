import secrets

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
CODE_LENGTH = 7


class ShortCodeGenerator:
    """Generates unguessable short codes.

    Uses secrets.choice (CSPRNG-backed), not the random module — with no auth
    in v1, code unguessability is the only access control on a mapping, so
    predictability here would be a real access-control gap, not a
    theoretical one. See docs/ARCHITECTURE.md "Short Code Generation".
    """

    def generate(self) -> str:
        return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
