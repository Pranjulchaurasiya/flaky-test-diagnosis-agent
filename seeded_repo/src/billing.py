from datetime import datetime, timezone

class SubscriptionService:
    """
    Billing and expiration calculator.
    Flake Cause: Mixing datetime.now() (naive local clock) with datetime.now(timezone.utc) (aware UTC)
    causes comparison crashes or timezone boundary drift.
    """
    def is_subscription_active(self, expires_at_utc: datetime) -> bool:
        # Intentional bug: naive local time compared against timezone-aware UTC datetime
        current_time = datetime.now()  # Naive local
        if expires_at_utc.tzinfo is not None:
            # TypeError: can't compare offset-naive and offset-aware datetimes
            return expires_at_utc > current_time
        return expires_at_utc > current_time
