from datetime import datetime, timezone, timedelta
import pytest
from billing import SubscriptionService

def test_future_subscription_validity():
    """
    Test Case 07: Timezone / DateTime Clock Boundary Drift
    Taxonomy: datetime_clock_drift
    Description: Passes timezone-aware UTC datetime to service which compares against naive datetime.now().
    Raises TypeError: can't compare offset-naive and offset-aware datetimes.
    """
    service = SubscriptionService()
    # Explicit UTC expiry
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    # Fails due to naive vs aware datetime comparison
    is_active = service.is_subscription_active(expires_at)
    assert is_active is True
