import socket

class CurrencyExchangeClient:
    """
    Currency converter service.
    Flake Cause: Secondary fallback makes an unmocked live socket call to an external endpoint
    which raises ConnectionRefusedError / ConnectionError.
    """
    RATES = {"USD_EUR": 0.92, "USD_GBP": 0.79}

    def convert(self, pair: str, amount: float, use_live_fallback: bool = False) -> float:
        if pair in self.RATES and not use_live_fallback:
            return amount * self.RATES[pair]

        # Flaky unmocked external network probe (immediate connection refusal)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.05)
            s.connect(("127.0.0.1", 59199))  # Closed port triggering immediate connection refusal
            s.close()
            return amount * 1.05
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            raise ConnectionError(f"External currency upstream unreachable: {e}")
