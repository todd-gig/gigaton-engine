"""Apollo API client for person/people search and enrichment."""

import random
import string
from typing import Dict, List, Any
from apollo_enrichment.models.enriched_lead import EnrichedLead


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


class ApolloClient:
    """Apollo API client with mock and real mode support."""

    def __init__(self, api_key: str = "", mock_mode: bool = True):
        """Initialize Apollo client.

        Args:
            api_key: Apollo API key (unused in mock mode)
            mock_mode: If True, generate mock data. If False, call real API.
        """
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.base_url = "https://api.apollo.io/api/v1"

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

    def _search_people_real(self, filters: Dict[str, Any], max_results: int) -> List[Dict]:
        """Call real Apollo People Search API.

        POST to https://api.apollo.io/api/v1/mixed_people/search
        with filters in request body.
        """
        # Placeholder for real API implementation
        # Would require: requests library, proper error handling, API response parsing
        raise NotImplementedError(
            "Real Apollo API calls not yet implemented. Use mock_mode=True for now."
        )

    def _enrich_person_real(self, email: str) -> Dict[str, Any]:
        """Call real Apollo People Enrichment API.

        POST to https://api.apollo.io/api/v1/people/match
        """
        # Placeholder for real API implementation
        raise NotImplementedError(
            "Real Apollo API calls not yet implemented. Use mock_mode=True for now."
        )
