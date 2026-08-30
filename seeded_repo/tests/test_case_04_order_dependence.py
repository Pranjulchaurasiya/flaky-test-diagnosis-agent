import pytest
from database import InMemoryOrderDB

def test_create_order_step():
    """
    Test Case 04: Order Dependence (Setup Step)
    Creates order ORD-777.
    """
    db = InMemoryOrderDB()
    order = db.create_order("ORD-777", 250.0)
    assert order["status"] == "PENDING"

def test_delete_existing_order():
    """
    Test Case 04: Order Dependence
    Taxonomy: test_order_dependence
    Description: Assumes test_create_order_step ran previously.
    Fails with KeyError when executed in isolation or reverse test order.
    """
    db = InMemoryOrderDB()
    # Flaky assumption: assumes "ORD-777" already exists from prior test execution
    deleted = db.delete_order("ORD-777")
    assert deleted["id"] == "ORD-777"
