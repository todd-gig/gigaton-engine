"""Tests for Apollo API client."""

import pytest
from apollo_enrichment.engines.apollo_client import ApolloClient


class TestApolloClient:
    """Test ApolloClient functionality."""

    def test_apollo_client_creation_mock_mode(self):
        """Test creating ApolloClient in mock mode."""
        client = ApolloClient(api_key="test-key", mock_mode=True)
        assert client.mock_mode is True
        assert client.api_key == "test-key"

    def test_apollo_client_creation_real_mode(self):
        """Test creating ApolloClient in real mode."""
        client = ApolloClient(api_key="test-key", mock_mode=False)
        assert client.mock_mode is False

    def test_apollo_client_default_mock_mode(self):
        """Test that ApolloClient defaults to mock mode."""
        client = ApolloClient()
        assert client.mock_mode is True


class TestApolloClientMockMode:
    """Test Apollo mock data generation."""

    def test_search_people_returns_list(self):
        """Test that search_people returns a list."""
        client = ApolloClient(mock_mode=True)
        results = client.search_people({}, max_results=5)
        assert isinstance(results, list)
        assert len(results) == 5

    def test_search_people_respects_max_results(self):
        """Test that search_people respects max_results parameter."""
        client = ApolloClient(mock_mode=True)

        results_5 = client.search_people({}, max_results=5)
        assert len(results_5) == 5

        results_10 = client.search_people({}, max_results=10)
        assert len(results_10) == 10

        results_25 = client.search_people({}, max_results=25)
        assert len(results_25) == 25

    def test_search_people_has_required_fields(self):
        """Test that search_people results have all required fields."""
        client = ApolloClient(mock_mode=True)
        results = client.search_people({}, max_results=5)

        required_fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "title",
            "organization_name",
            "organization_domain",
            "organization_industry",
        ]

        for result in results:
            for field in required_fields:
                assert field in result
                # All fields should be strings, not None
                assert isinstance(result[field], str)

    def test_search_people_with_title_filter(self):
        """Test that mock data respects title filters."""
        client = ApolloClient(mock_mode=True)
        filters = {"person_titles": ["VP Marketing", "CMO"]}

        results = client.search_people(filters, max_results=20)

        for result in results:
            assert result["title"] in ["VP Marketing", "CMO"]

    def test_search_people_with_industry_filter(self):
        """Test that mock data respects industry filters."""
        client = ApolloClient(mock_mode=True)
        filters = {"organization_industry_tag_ids": ["saas", "technology"]}

        results = client.search_people(filters, max_results=20)

        for result in results:
            assert result["organization_industry"] in ["saas", "technology"]

    def test_search_people_with_department_and_seniority(self):
        """Test that mock data respects department and seniority filters."""
        client = ApolloClient(mock_mode=True)
        filters = {
            "person_departments": ["marketing"],
            "person_seniorities": ["director", "vp"],
        }

        results = client.search_people(filters, max_results=20)

        for result in results:
            title = result["title"].lower()
            # Should contain director or vp keywords
            assert "director" in title or "vp" in title or "head" in title

    def test_search_people_generates_valid_emails(self):
        """Test that mock emails are realistically formatted."""
        client = ApolloClient(mock_mode=True)
        results = client.search_people({}, max_results=20)

        for result in results:
            email = result["email"]
            assert "@" in email
            assert "." in email
            parts = email.split("@")
            assert len(parts) == 2
            assert len(parts[0]) > 0
            assert len(parts[1]) > 0

    def test_search_people_generates_unique_ids(self):
        """Test that mock people have unique IDs."""
        client = ApolloClient(mock_mode=True)
        results = client.search_people({}, max_results=30)

        ids = [result["id"] for result in results]
        assert len(ids) == len(set(ids)), "All IDs should be unique"

    def test_search_people_generates_linkedin_urls(self):
        """Test that mock data includes LinkedIn URLs."""
        client = ApolloClient(mock_mode=True)
        results = client.search_people({}, max_results=10)

        for result in results:
            assert "linkedin_url" in result
            assert "linkedin.com/in/" in result["linkedin_url"]

    def test_search_people_with_no_filters(self):
        """Test search_people with empty filters."""
        client = ApolloClient(mock_mode=True)
        results = client.search_people({}, max_results=5)

        assert len(results) == 5
        # Should still have all required fields
        for result in results:
            assert result["first_name"]
            assert result["last_name"]
            assert result["email"]

    def test_search_people_generates_phone_numbers(self):
        """Test that mock data includes phone numbers."""
        client = ApolloClient(mock_mode=True)
        results = client.search_people({}, max_results=10)

        for result in results:
            assert "phone_number" in result
            # Check phone format
            phone = result["phone_number"]
            assert phone.startswith("+1-")
            assert "-" in phone

    def test_enrich_person_by_email(self):
        """Test enrich_person method."""
        client = ApolloClient(mock_mode=True)
        enriched = client.enrich_person("test@example.com")

        assert isinstance(enriched, dict)
        assert "id" in enriched
        assert "first_name" in enriched
        assert "last_name" in enriched
        assert "email" in enriched

    def test_enrich_person_parses_email_for_names(self):
        """Test that enrich_person extracts names from email."""
        client = ApolloClient(mock_mode=True)
        enriched = client.enrich_person("john.doe@example.com")

        # Should infer John and Doe from email
        assert enriched["first_name"].lower() == "john"
        assert enriched["last_name"].lower() == "doe"

    def test_search_people_with_employee_count_range(self):
        """Test that search_people respects employee count ranges."""
        client = ApolloClient(mock_mode=True)
        filters = {"organization_num_employees_ranges": ["51-200", "201-500"]}

        results = client.search_people(filters, max_results=20)

        for result in results:
            assert result["organization_size"] in ["51-200", "201-500"]

    def test_search_people_with_revenue_range(self):
        """Test that search_people respects revenue ranges."""
        client = ApolloClient(mock_mode=True)
        filters = {"organization_revenue_ranges": ["$10M-$50M", "$50M-$100M"]}

        results = client.search_people(filters, max_results=20)

        for result in results:
            assert result["organization_revenue_range"] in ["$10M-$50M", "$50M-$100M"]


class TestApolloClientRealMode:
    """Test Apollo real API mode (structure only)."""

    def test_real_mode_search_people_raises_on_connection(self):
        """Test that real mode search_people raises error without valid endpoint."""
        client = ApolloClient(api_key="test-key", mock_mode=False)

        with pytest.raises((RuntimeError, ImportError)):
            client.search_people({}, max_results=5)

    def test_real_mode_enrich_person_raises_on_connection(self):
        """Test that real mode enrich_person raises error without valid endpoint."""
        client = ApolloClient(api_key="test-key", mock_mode=False)

        with pytest.raises((RuntimeError, ImportError)):
            client.enrich_person("test@example.com")
