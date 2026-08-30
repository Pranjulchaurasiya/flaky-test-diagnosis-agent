import random
import string

class ApiTokenService:
    """
    Token generator.
    Flake Cause: Uses unseeded random.choice() with an alphabet containing invalid prefix chars ('_', '-').
    Token parser rejects tokens starting with punctuation, causing ~15% test failure rate.
    """
    ALPHABET = string.ascii_letters + string.digits + "_-"

    def generate_token(self, length: int = 16) -> str:
        # Unseeded non-deterministic random generation
        return "".join(random.choice(self.ALPHABET) for _ in range(length))

    def validate_token_format(self, token: str) -> bool:
        if not token or len(token) < 8:
            return False
        # Rule: Tokens MUST start with an alphanumeric character
        if token[0] in ("_", "-"):
            return False
        return True
