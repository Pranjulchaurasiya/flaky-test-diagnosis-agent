import os
import pytest
from config_service import AppConfigService

def test_override_env_production():
    """
    Test Case 09: Environment Variable Mutation (Step A)
    Mutates os.environ['APP_ENV'] without restoring previous value.
    """
    os.environ["APP_ENV"] = "production"
    assert AppConfigService.is_production() is True
    assert AppConfigService.get_max_connections() == 100

def test_default_env_development():
    """
    Test Case 09: Environment Variable Mutation (Step B)
    Taxonomy: environment_mutation
    Description: Assumes test runs in default 'development' mode.
    Fails when test_override_env_production ran previously because os.environ was not restored.
    """
    # Fails if prior test leaked APP_ENV=production
    assert AppConfigService.get_environment() == "development", (
        f"Environment state contamination! Expected 'development' but got '{AppConfigService.get_environment()}'"
    )
    assert AppConfigService.get_max_connections() == 10
