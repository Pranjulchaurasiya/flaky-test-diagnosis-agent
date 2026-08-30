import pytest
from security import ApiTokenService

def test_api_token_validity_batches():
    """
    Test Case 08: Unseeded Pseudo-Randomness
    Taxonomy: unseeded_randomness
    Description: Generates 20 random tokens. Because the alphabet contains '_' and '-',
    approximately ~15% of generated tokens start with '_' or '-', which fails validate_token_format().
    """
    service = ApiTokenService()
    for _ in range(20):
        token = service.generate_token(16)
        assert service.validate_token_format(token), (
            f"Random token failure! Token '{token}' failed format validation rules."
        )
