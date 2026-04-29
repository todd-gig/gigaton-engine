"""Tests for Apollo client real-mode infrastructure.

These tests verify the real-mode code paths WITHOUT calling the actual API.
They test: factory function, rate limiting, error handling, response parsing.
"""

import sys
import os
import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from apollo_enrichment.engines.apollo_client import (
    ApolloClient, create_apollo_client,
    APOLLO_RATE_LIMIT_RPM, APOLLO_RETRY_MAX,
)


class TestFactoryFunction:
    def test_mock_mode_by_default(self):
        # Ensure no API key is set
        old = os.environ.pop("APOLLO_API_KEY", None)
        try:
            client = create_apollo_client()
            assert client.mock_mode is True
            assert client.api_key == ""
        finally:
            if old:
                os.environ["APOLLO_API_KEY"] = old

    def test_real_mode_with_key(self):
        os.environ["APOLLO_API_KEY"] = "test_key_123"
        try:
            client = create_apollo_client()
            assert client.mock_mode is False
            assert client.api_key == "test_key_123"
        finally:
            del os.environ["APOLLO_API_KEY"]


class TestMockMode:
    def test_search_returns_results(self):
        client = ApolloClient(mock_mode=True)
        results = client.search_people(
            filters={"person_titles": ["VP Marketing"]},
            max_results=5,
        )
        assert len(results) == 5
        assert all("email" in r for r in results)
        assert all("first_name" in r for r in results)

    def test_enrich_returns_person(self):
        client = ApolloClient(mock_mode=True)
        result = client.enrich_person("sarah.jones@example.com")
        assert result["email"] == "sarah.jones@example.com"
        assert result["first_name"] == "Sarah"

    def test_search_with_industry_filter(self):
        client = ApolloClient(mock_mode=True)
        results = client.search_people(
            filters={"organization_industry_tag_ids": ["healthcare"]},
            max_results=3,
        )
        assert len(results) == 3


class TestRealModeInfrastructure:
    def test_rate_limiter_initialized(self):
        client = ApolloClient(api_key="test", mock_mode=False)
        assert client._min_interval > 0
        assert client._min_interval == 60.0 / APOLLO_RATE_LIMIT_RPM

    def test_real_mode_raises_on_connection_failure(self):
        """Real API calls should raise RuntimeError on connection/import failure."""
        client = ApolloClient(api_key="test", mock_mode=False)
        # The _api_request method will try to import httpx and connect.
        # In test environments (sandbox, no API), it should raise RuntimeError
        # from either: missing httpx, connection error, or proxy error.
        with pytest.raises((RuntimeError, ImportError)):
            client._search_people_real({"person_titles": ["CEO"]}, 1)


class TestResponseParsing:
    """Test the search/enrich result normalization logic."""

    def test_mock_response_schema(self):
        client = ApolloClient(mock_mode=True)
        results = client.search_people({}, max_results=1)
        person = results[0]
        required_keys = [
            "id", "first_name", "last_name", "name", "title",
            "email", "phone_number", "linkedin_url",
            "organization_name", "organization_domain",
        ]
        for key in required_keys:
            assert key in person, f"Missing key: {key}"

    def test_mock_enrich_schema(self):
        client = ApolloClient(mock_mode=True)
        person = client.enrich_person("test@example.com")
        required_keys = [
            "id", "first_name", "last_name", "name", "title",
            "email", "linkedin_url",
        ]
        for key in required_keys:
            assert key in person, f"Missing key: {key}"
