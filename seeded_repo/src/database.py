class InMemoryOrderDB:
    """
    In-memory database singleton.
    Flake Cause: Test assumes order of execution where insert test ran before delete test.
    """
    _INSTANCE = None

    def __new__(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = super(InMemoryOrderDB, cls).__new__(cls)
            cls._INSTANCE.orders = {}
        return cls._INSTANCE

    def create_order(self, order_id: str, amount: float):
        self.orders[order_id] = {"id": order_id, "amount": amount, "status": "PENDING"}
        return self.orders[order_id]

    def get_order(self, order_id: str):
        return self.orders.get(order_id)

    def delete_order(self, order_id: str):
        if order_id not in self.orders:
            raise KeyError(f"Order {order_id} not found in database")
        return self.orders.pop(order_id)

    def clear(self):
        self.orders.clear()
