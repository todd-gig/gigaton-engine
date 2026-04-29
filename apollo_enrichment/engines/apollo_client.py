"""Apollo API client for person/people search and enrichment.

Supports mock mode (default) and real API mode via APOLLO_API_KEY env var.
Real mode requires httpx and uses rate-limited retry logic.
"""

import logging
import os
import random
import string
import time
from typing import Dict, List, Any, Optional
from apollo_enrichment.models.enriched_lead import EnrichedLead

logger = logging.getLogger(__name__)

# Rate limiting constants
APOLLO_RATE_LIMIT_RPM = 50  # requests per minute (conservative)
APOLLO_RETRY_MAX = 3
APOLLO_RETRY_BACKOFF = 2.0  # seconds, doubles each retry


# Mock data: realistic names, titles, companies for different segments
MOCK_FIRST_NAMES = [
    "Sarah", "Michael", "Jennifer", "David", "Emily",
    "James", "Lisa", "Robert", "Maria", "John",
    "Katherine", "William", "Jessica", "Richard", "Amanda",
]

MOCK_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
]

MOCK_COMPANIES = {
    "technology": [
        "TechCore Inc", "DataFlow Systems", "CloudVision Labs",
        "API Gateway Inc", "DevOps Dynamics", "SaaS Accelerator",
    ],
    "saas": [
        "Growth Engine Co", "Analytics Pro", "MarketLead AI",
        "Pipeline Genius", "RevOps AI", "Engagement Stack",
    ],
    "financial services": [
        "Capital Partners", "Wealth Advisors Inc", "Investment Group",
        "Financial Innovations", "Security Systems Corp",
    ],
    "healthcare": [
        "MedTech Solutions", "Health Analytics", "Patient Care Systems",
        "Medical Innovations", "HealthTech Partners",
    ],
    "professional services": [
        "Consulting Group Inc", "Advisory Partners", "Strategy House",
        "Business Solutions", "Enterprise Advisors",
    ],
    "manufacturing": [
        "Advanced Manufacturing", "Industrial Solutions", "Production Dynamics",
    ],
    "media": [
        "Content Studios", "Digital Media Group", "Publishing Plus",
    ],
    "education": [
        "EdTech Innovations", "Learning Systems", "Academic Tech",
    ],
    "software": [
        "SoftDev Inc", "Engineering Labs", "Code Solutions",
    ],
    "developer tools": [
        "Dev Tools Pro", "Developer Hub", "Engineer's Toolkit",
    ],
}

MOCK_EMAILS_DOMAINS = [
    "gmail.com", "company.com", "outlook.com", "yahoo.com",
    "hotmail.com", "work.com", "email.com",
]


def create_apollo_client() -> "ApolloClient":
    """Factory: create an ApolloClient from env vars.

    Reads APOLLO_API_KEY from environment. If present and non-empty,
    creates a real-mode client. Otherwise creates a mock-mode client.
    """
    api_key = os.environ.get("APOLLO_API_KEY", "")
    if api_key:
        logger.info("Apollo client: REAL mode (API key present)")
        return ApolloClient(api_key=api_key, mock_mode=False)
    else:
        logger.info("Apollo client: MOCK mode (no APOLLO_API_KEY)")
        return ApolloClient(api_key="", mock_mode=True)


class ApolloClient:
    """Apollo API client with mock and real mode support.

    Real mode uses httpx for HTTP calls with rate limiting and retry logic.
    Mock mode generates realistic synthetic data for development/testing.

    Environment-driven activation:
        APOLLO_API_KEY env var → real mode when set, mock mode when absent.
        Use create_apollo_client() factory for automatic detection.
    """

    def __init__(self, api_key: str = "", mock_mode: bool = True):
        """Initialize Apollo client.

        Args:
            api_key: Apollo API key (unused in mock mode)
            mock_mode: If True, generate mock data. If False, call real API.
        """
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.base_url = "https://api.apollo.io/api/v1"
        self._last_request_time = 0.0
        self._min_interval = 60.0 / APOLLO_RATE_LIMIT_RPM

    def search_people(self, filters: Dict[str, Any], max_results: int = 25) -> List[Dict]:
        """Search for people matching the given filters.

        Args:
            filters: Dict of Apollo API filters (from ApolloTargeting.to_apollo_filters())
            max_results: Maximum number of results to return

        Returns:
            List of person dicts with fields: first_name, last_name, title, email,
            organization_name, organization_domain, organization_industry, etc.
        """
        if self.mock_mode:
            return self._generate_mock_people(filters, max_results)
        else:
            return self._search_people_real(filters, max_results)

    def enrich_person(self, email: str) -> Dict[str, Any]:
        """Enrich a single person by email address.

        Args:
            email: Email address to enrich

        Returns:
            Dict with enriched person data
        """
        if self.mock_mode:
            return self._generate_mock_person(email)
        else:
            return self._enrich_person_real(email)

    def _generate_mock_people(
        self, filters: Dict[str, Any], max_results: int
    ) -> List[Dict]:
        """Generate realistic mock people matching filter criteria.

        Args:
            filters: Apollo filters from ApolloTargeting.to_apollo_filters()
            max_results: Number of leads to generate

        Returns:
            List of mock person dicts
        """
        results = []

        # Extract filter criteria
        industries = filters.get("organization_industry_tag_ids", [])
        titles = filters.get("person_titles", [])
        departments = filters.get("person_departments", [])
        seniority = filters.get("person_seniorities", [])
        employee_ranges = filters.get("organization_num_employees_ranges", [])
        revenue_ranges = filters.get("organization_revenue_ranges", [])

        # Use industries as fallback for company selection
        company_keys = industries if industries else ["technology", "saas"]

        for i in range(max_results):
            # Select title from filters or use random
            if titles:
                title = random.choice(titles)
            else:
                title = self._generate_mock_title(departments, seniority)

            # Select company
            available_companies = []
            for key in company_keys:
                if key in MOCK_COMPANIES:
                    available_companies.extend(MOCK_COMPANIES[key])
            if not available_companies:
                available_companies = MOCK_COMPANIES["technology"]

            company_name = random.choice(available_companies)

            # Generate person
            first_name = random.choice(MOCK_FIRST_NAMES)
            last_name = random.choice(MOCK_LAST_NAMES)
            email = self._generate_mock_email(first_name, last_name)
            domain = company_name.lower().replace(" ", "").replace("inc", "") + ".com"

            results.append({
                "id": self._generate_mock_id(),
                "first_name": first_name,
                "last_name": last_name,
                "name": f"{first_name} {last_name}",
                "title": title,
                "email": email,
                "phone_number": self._generate_mock_phone(),
                "linkedin_url": f"https://linkedin.com/in/{first_name.lower()}{last_name.lower()}",
                "organization_name": company_name,
                "organization_domain": domain,
                "organization_industry": random.choice(company_keys) if company_keys else "technology",
                "organization_size": random.choice(employee_ranges) if employee_ranges else "51-200",
                "organization_revenue_range": random.choice(revenue_ranges) if revenue_ranges else "$10M-$50M",
            })

        return results

    def _generate_mock_person(self, email: str) -> Dict[str, Any]:
        """Generate a mock enriched person by email."""
        # Parse email for name hints
        local_part = email.split("@")[0]
        names = local_part.split(".")
        first_name = names[0].capitalize() if names else random.choice(MOCK_FIRST_NAMES)
        last_name = names[1].capitalize() if len(names) > 1 else random.choice(MOCK_LAST_NAMES)

        return {
            "id": self._generate_mock_id(),
            "first_name": first_name,
            "last_name": last_name,
            "name": f"{first_name} {last_name}",
            "title": random.choice(["VP Marketing", "Director of Marketing", "Manager"]),
            "email": email,
            "phone_number": self._generate_mock_phone(),
            "linkedin_url": f"https://linkedin.com/in/{first_name.lower()}{last_name.lower()}",
            "organization_name": "Tech Company Inc",
            "organization_domain": "techcompany.com",
        }

    def _generate_mock_title(self, departments: List[str], seniority: List[str]) -> str:
        """Generate a title matching department and seniority filters."""
        title_options = {
            "marketing": {
                "director": "Director of Marketing",
                "vp": "VP Marketing",
                "c_suite": "CMO",
                "manager": "Marketing Manager",
            },
            "sales": {
                "director": "Director of Sales",
                "vp": "VP Sales",
                "c_suite": "CRO",
                "manager": "Sales Manager",
            },
            "growth": {
                "director": "Director of Growth",
                "vp": "VP Growth",
                "manager": "Growth Manager",
            },
            "product": {
                "director": "Director of Product",
                "vp": "VP Product",
                "c_suite": "Chief Product Officer",
                "manager": "Product Manager",
            },
            "revenue operations": {
                "director": "Director of RevOps",
                "vp": "VP Revenue Operations",
                "manager": "RevOps Manager",
            },
            "content": {
                "director": "Director of Content",
                "manager": "Content Manager",
            },
        }

        # Use first department/seniority combination found
        for dept in departments:
            if dept in title_options:
                for sen in seniority:
                    if sen in title_options[dept]:
                        return title_options[dept][sen]

        # Fallback
        return "Manager"

    def _generate_mock_email(self, first_name: str, last_name: str) -> str:
        """Generate a realistic mock email."""
        formats = [
            f"{first_name.lower()}.{last_name.lower()}@{random.choice(MOCK_EMAILS_DOMAINS)}",
            f"{first_name[0].lower()}{last_name.lower()}@{random.choice(MOCK_EMAILS_DOMAINS)}",
            f"{first_name.lower()}@{random.choice(MOCK_EMAILS_DOMAINS)}",
        ]
        return random.choice(formats)

    def _generate_mock_phone(self) -> str:
        """Generate a realistic mock phone number."""
        return f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"

    def _generate_mock_id(self) -> str:
        """Generate a mock Apollo person ID."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=24))

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _api_request(
        self, method: str, endpoint: str, json_body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make an API request with rate limiting and retry logic.

        Args:
            method: HTTP method (POST, GET)
            endpoint: API endpoint path (e.g., /mixed_people/search)
            json_body: Request body

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: If all retries exhausted or non-retryable error
        """
        try:
            import httpx
        except ImportError:
            raise RuntimeError(
                "httpx is required for real Apollo API calls. "
                "Install with: pip install httpx"
            )

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,
        }

        last_error = None
        for attempt in range(APOLLO_RETRY_MAX):
            self._rate_limit()
            try:
                with httpx.Client(timeout=30.0) as client:
                    if method.upper() == "POST":
                        response = client.post(url, headers=headers, json=json_body)
                    else:
                        response = client.get(url, headers=headers, params=json_body)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited — back off and retry
                    backoff = APOLLO_RETRY_BACKOFF * (2 ** attempt)
                    logger.warning(
                        f"Apollo rate limited (429), backing off {backoff:.1f}s "
                        f"(attempt {attempt + 1}/{APOLLO_RETRY_MAX})"
                    )
                    time.sleep(backoff)
                    last_error = f"Rate limited (429) after {attempt + 1} attempts"
                    continue
                elif response.status_code in (500, 502, 503):
                    # Server error — retry
                    backoff = APOLLO_RETRY_BACKOFF * (2 ** attempt)
                    logger.warning(
                        f"Apollo server error ({response.status_code}), "
                        f"retrying in {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                    last_error = f"Server error ({response.status_code})"
                    continue
                else:
                    # Non-retryable error
                    raise RuntimeError(
                        f"Apollo API error {response.status_code}: {response.text[:500]}"
                    )

            except httpx.TimeoutException:
                backoff = APOLLO_RETRY_BACKOFF * (2 ** attempt)
                logger.warning(f"Apollo timeout, retrying in {backoff:.1f}s")
                time.sleep(backoff)
                last_error = "Request timeout"
                continue
            except httpx.ConnectError as e:
                raise RuntimeError(f"Cannot connect to Apollo API: {e}")

        raise RuntimeError(f"Apollo API: exhausted {APOLLO_RETRY_MAX} retries. Last error: {last_error}")

    def _search_people_real(self, filters: Dict[str, Any], max_results: int) -> List[Dict]:
        """Call real Apollo People Search API.

        POST to https://api.apollo.io/api/v1/mixed_people/search

        Args:
            filters: Apollo API filters from ApolloTargeting.to_apollo_filters()
            max_results: Maximum results to return

        Returns:
            List of person dicts normalized to our standard schema
        """
        # Build request body per Apollo API spec
        body = {
            "per_page": min(max_results, 100),  # Apollo max is 100
            "page": 1,
        }
        # Map our filter keys to Apollo's expected keys
        if "person_titles" in filters:
            body["person_titles"] = filters["person_titles"]
        if "person_departments" in filters:
            body["person_departments"] = filters["person_departments"]
        if "person_seniorities" in filters:
            body["person_seniorities"] = filters["person_seniorities"]
        if "organization_industry_tag_ids" in filters:
            body["organization_industry_tag_ids"] = filters["organization_industry_tag_ids"]
        if "organization_num_employees_ranges" in filters:
            body["organization_num_employees_ranges"] = filters["organization_num_employees_ranges"]
        if "organization_revenue_ranges" in filters:
            body["organization_revenue_ranges"] = filters["organization_revenue_ranges"]

        response = self._api_request("POST", "/mixed_people/search", body)

        # Parse Apollo response — people are in response["people"]
        raw_people = response.get("people", [])
        results = []
        for person in raw_people[:max_results]:
            org = person.get("organization", {}) or {}
            results.append({
                "id": person.get("id", ""),
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "name": person.get("name", ""),
                "title": person.get("title", ""),
                "email": person.get("email", ""),
                "phone_number": (
                    person.get("phone_numbers", [{}])[0].get("sanitized_number", "")
                    if person.get("phone_numbers") else ""
                ),
                "linkedin_url": person.get("linkedin_url", ""),
                "organization_name": org.get("name", ""),
                "organization_domain": org.get("primary_domain", ""),
                "organization_industry": org.get("industry", ""),
                "organization_size": org.get("estimated_num_employees", ""),
                "organization_revenue_range": org.get("annual_revenue_printed", ""),
            })

        logger.info(f"Apollo search returned {len(results)} people (requested {max_results})")
        return results

    def _enrich_person_real(self, email: str) -> Dict[str, Any]:
        """Call real Apollo People Match/Enrichment API.

        POST to https://api.apollo.io/api/v1/people/match

        Args:
            email: Email address to enrich

        Returns:
            Normalized person dict
        """
        body = {"email": email, "reveal_personal_emails": False}
        response = self._api_request("POST", "/people/match", body)

        person = response.get("person", {}) or {}
        org = person.get("organization", {}) or {}

        return {
            "id": person.get("id", ""),
            "first_name": person.get("first_name", ""),
            "last_name": person.get("last_name", ""),
            "name": person.get("name", ""),
            "title": person.get("title", ""),
            "email": person.get("email", email),
            "phone_number": (
                person.get("phone_numbers", [{}])[0].get("sanitized_number", "")
                if person.get("phone_numbers") else ""
            ),
            "linkedin_url": person.get("linkedin_url", ""),
            "organization_name": org.get("name", ""),
            "organization_domain": org.get("primary_domain", ""),
            "organization_industry": org.get("industry", ""),
        }
