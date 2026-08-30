class UserSessionCache:
    """
    Session cache with a class-level shared dictionary.
    Flake Cause: Class-level _STORE retains state across independent test instances.
    """
    _STORE = {}  # Global/class-level shared store

    def __init__(self, ttl: int = 3600):
        self.ttl = ttl

    def set_session(self, user_id: str, data: dict):
        self._STORE[user_id] = data

    def get_session(self, user_id: str):
        return self._STORE.get(user_id)

    def count(self) -> int:
        return len(self._STORE)

    @classmethod
    def purge_all(cls):
        cls._STORE.clear()
