import pytest
from currency import CurrencyExchangeClient

def test_currency_conversion_fallback():
    """
    Test Case 05: Flaky External Dependency
    Taxonomy: flaky_external_dependency
    Description: When converting exotic currency pairs (e.g. USD_JPY), client executes
    an unmocked socket connection to an external endpoint that times out or refuses connection.
    """
    client = CurrencyExchangeClient()
    # USD_JPY is not in static RATES dict -> triggers live fallback network call
    result = client.convert("USD_JPY", 100.0, use_live_fallback=True)
    assert result > 0
