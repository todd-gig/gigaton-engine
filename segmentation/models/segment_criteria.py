"""SegmentCriteria and ApolloTargeting models for customer segmentation."""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ApolloTargeting:
    """Maps segment criteria to Apollo search filter fields."""

    # Company filters
    industries: List[str] = field(default_factory=list)
    employee_count_ranges: List[str] = field(default_factory=list)  # e.g. ["51-200", "201-500"]
    revenue_ranges: List[str] = field(default_factory=list)  # e.g. ["$10M-$50M"]
    technologies: List[str] = field(default_factory=list)  # e.g. ["HubSpot", "Salesforce"]
    keywords: List[str] = field(default_factory=list)  # company description keywords

    # Contact filters
    titles: List[str] = field(default_factory=list)  # e.g. ["VP Marketing", "CMO"]
    seniority_levels: List[str] = field(default_factory=list)  # e.g. ["director", "vp", "c_suite"]
    departments: List[str] = field(default_factory=list)  # e.g. ["marketing", "sales"]

    # Geographic
    locations: List[str] = field(default_factory=list)  # e.g. ["United States", "Canada"]

    def to_apollo_filters(self) -> Dict[str, Any]:
        """Convert to Apollo API filter format."""
        filters = {}
        if self.industries:
            filters["organization_industry_tag_ids"] = self.industries
        if self.employee_count_ranges:
            filters["organization_num_employees_ranges"] = self.employee_count_ranges
        if self.technologies:
            filters["currently_using_any_of_technology_uids"] = self.technologies
        if self.titles:
            filters["person_titles"] = self.titles
        if self.seniority_levels:
            filters["person_seniorities"] = self.seniority_levels
        if self.departments:
            filters["person_departments"] = self.departments
        if self.locations:
            filters["person_locations"] = self.locations
        if self.keywords:
            filters["q_organization_keyword_tags"] = self.keywords
        if self.revenue_ranges:
            filters["organization_revenue_ranges"] = self.revenue_ranges
        return filters
