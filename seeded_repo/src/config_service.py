import os

class AppConfigService:
    """
    Configuration reader.
    Flake Cause: Tests mutate os.environ['APP_ENV'] directly without cleanup fixture,
    contaminating downstream test executions.
    """
    @staticmethod
    def get_environment() -> str:
        return os.environ.get("APP_ENV", "development")

    @staticmethod
    def is_production() -> bool:
        return os.environ.get("APP_ENV", "development").lower() == "production"

    @staticmethod
    def get_max_connections() -> int:
        if AppConfigService.is_production():
            return 100
        return 10
