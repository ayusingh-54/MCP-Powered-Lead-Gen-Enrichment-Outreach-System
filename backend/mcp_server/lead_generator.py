"""
Lead Generator Module
=====================
Generates synthetic but realistic-looking leads using the Faker library.
Ensures all generated data is valid and consistent:
- Valid email addresses
- Valid website URLs
- Valid LinkedIn URLs
- Role/title matches industry
- Reproducible with random seed
"""

import uuid
import random
from datetime import datetime
from typing import List, Optional, Dict
from faker import Faker

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.models import Lead, LeadStatus


# =============================================================================
# INDUSTRY AND ROLE MAPPINGS
# =============================================================================

# Industry-specific roles to ensure consistency
INDUSTRY_ROLES: Dict[str, List[str]] = {
    "Technology": [
        "VP of Engineering", "CTO", "Chief Technology Officer",
        "VP of Product", "Director of Engineering", "Head of Data",
        "VP of Operations", "Chief Data Officer", "IT Director",
        "Head of DevOps", "VP of Infrastructure", "Tech Lead"
    ],
    "Finance": [
        "CFO", "Chief Financial Officer", "VP of Finance",
        "Director of Treasury", "Head of Risk", "VP of Operations",
        "Chief Risk Officer", "Controller", "VP of Compliance",
        "Head of Investment", "Director of Finance", "Treasurer"
    ],
    "Healthcare": [
        "Chief Medical Officer", "VP of Operations", "Director of IT",
        "Head of Clinical Operations", "VP of Patient Care",
        "Chief Nursing Officer", "Director of Healthcare IT",
        "VP of Quality", "Chief Operating Officer", "Medical Director"
    ],
    "Manufacturing": [
        "VP of Operations", "Director of Supply Chain", "COO",
        "Head of Procurement", "VP of Manufacturing", "Plant Manager",
        "Director of Quality", "VP of Logistics", "Supply Chain Director",
        "Operations Manager", "Procurement Head", "VP of Production"
    ],
    "Retail": [
        "VP of Merchandising", "Director of E-commerce", "CMO",
        "Head of Retail Operations", "VP of Supply Chain",
        "Chief Merchandising Officer", "Director of Stores",
        "VP of Digital", "Head of Customer Experience", "Retail Director"
    ],
    "Logistics": [
        "VP of Logistics", "Director of Operations", "COO",
        "Head of Supply Chain", "VP of Distribution", "Fleet Manager",
        "Director of Transportation", "Logistics Manager",
        "VP of Warehousing", "Supply Chain Leader", "Operations Director"
    ],
    "Energy": [
        "VP of Operations", "Director of Engineering", "COO",
        "Head of Sustainability", "VP of Production", "Plant Manager",
        "Director of Asset Management", "Chief Sustainability Officer",
        "VP of Power Generation", "Energy Director", "Operations Head"
    ],
    "Consulting": [
        "Managing Director", "Partner", "VP of Consulting",
        "Director of Strategy", "Head of Operations", "Practice Lead",
        "Senior Partner", "VP of Client Services", "Director of Delivery",
        "Head of Advisory", "Principal Consultant", "Strategy Director"
    ],
    "Telecommunications": [
        "VP of Network Operations", "CTO", "Director of IT",
        "Head of Infrastructure", "VP of Engineering", "Network Director",
        "Chief Network Officer", "VP of Customer Operations",
        "Director of Technology", "Head of Digital", "Tech Director"
    ],
    "Real Estate": [
        "VP of Development", "Director of Operations", "COO",
        "Head of Asset Management", "VP of Property Management",
        "Director of Acquisitions", "Chief Investment Officer",
        "VP of Construction", "Real Estate Director", "Development Head"
    ]
}

# Countries with appropriate locales
COUNTRIES = {
    "United States": "en_US",
    "United Kingdom": "en_GB",
    "Canada": "en_CA",
    "Australia": "en_AU",
    "Germany": "de_DE",
    "France": "fr_FR",
    "Netherlands": "nl_NL",
    "Singapore": "en_SG",
    "India": "en_IN",
    "Ireland": "en_IE"
}

# Company name suffixes by industry
COMPANY_SUFFIXES = {
    "Technology": ["Tech", "Systems", "Solutions", "Labs", "Software", "Digital", "AI"],
    "Finance": ["Capital", "Partners", "Financial", "Investments", "Group", "Holdings"],
    "Healthcare": ["Health", "Medical", "Care", "Therapeutics", "Pharma", "Life Sciences"],
    "Manufacturing": ["Industries", "Manufacturing", "Production", "Corp", "Works"],
    "Retail": ["Retail", "Stores", "Commerce", "Brands", "Outlets", "Markets"],
    "Logistics": ["Logistics", "Transport", "Freight", "Supply Chain", "Distribution"],
    "Energy": ["Energy", "Power", "Resources", "Utilities", "Renewables"],
    "Consulting": ["Consulting", "Advisory", "Group", "Partners", "Associates"],
    "Telecommunications": ["Telecom", "Communications", "Networks", "Connect", "Mobile"],
    "Real Estate": ["Properties", "Realty", "Development", "Estates", "Ventures"]
}


class LeadGenerator:
    """
    Generates synthetic leads with realistic, valid data.
    All generated data passes validation checks.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the lead generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        self.faker = Faker()
        
        # Set seed if provided for reproducibility
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
        
        self.industries = list(INDUSTRY_ROLES.keys())
    
    def _generate_company_name(self, industry: str) -> str:
        """
        Generate a realistic company name for the industry.
        
        Args:
            industry: Industry sector
            
        Returns:
            Company name string
        """
        # Use Faker for the base name
        base_name = self.faker.last_name()
        
        # Sometimes use a compound name
        if random.random() < 0.3:
            base_name = f"{self.faker.last_name()} & {self.faker.last_name()}"
        elif random.random() < 0.5:
            base_name = self.faker.word().title() + self.faker.last_name()
        
        # Add industry-appropriate suffix
        suffixes = COMPANY_SUFFIXES.get(industry, ["Inc", "Corp", "LLC"])
        suffix = random.choice(suffixes)
        
        return f"{base_name} {suffix}"
    
    def _generate_website(self, company_name: str) -> str:
        """
        Generate a valid website URL from company name.
        
        Args:
            company_name: Company name to derive URL from
            
        Returns:
            Valid website URL
        """
        # Clean company name for domain
        domain_name = company_name.lower()
        domain_name = ''.join(c if c.isalnum() else '' for c in domain_name)
        
        # Choose TLD
        tlds = [".com", ".io", ".co", ".net", ".org"]
        tld = random.choice(tlds)
        
        return f"https://www.{domain_name}{tld}"
    
    def _generate_email(self, full_name: str, company_name: str) -> str:
        """
        Generate a valid business email address.
        
        Args:
            full_name: Person's full name
            company_name: Company name for domain
            
        Returns:
            Valid email address
        """
        # Create email username from name
        name_parts = full_name.lower().split()
        
        # Different email patterns
        patterns = [
            lambda: f"{name_parts[0]}.{name_parts[-1]}",  # john.smith
            lambda: f"{name_parts[0][0]}{name_parts[-1]}",  # jsmith
            lambda: f"{name_parts[0]}",  # john
            lambda: f"{name_parts[0]}{name_parts[-1][0]}",  # johns
        ]
        
        username = random.choice(patterns)()
        username = ''.join(c if c.isalnum() or c == '.' else '' for c in username)
        
        # Create domain from company name
        domain = company_name.lower()
        domain = ''.join(c if c.isalnum() else '' for c in domain)
        
        return f"{username}@{domain}.com"
    
    def _generate_linkedin_url(self, full_name: str) -> str:
        """
        Generate a valid LinkedIn profile URL.
        
        Args:
            full_name: Person's full name
            
        Returns:
            Valid LinkedIn URL
        """
        # Create LinkedIn handle from name
        name_parts = full_name.lower().split()
        
        # Different patterns
        patterns = [
            lambda: f"{name_parts[0]}-{name_parts[-1]}",
            lambda: f"{name_parts[0]}{name_parts[-1]}",
            lambda: f"{name_parts[0]}-{name_parts[-1]}-{random.randint(1, 999)}",
        ]
        
        handle = random.choice(patterns)()
        handle = ''.join(c if c.isalnum() or c == '-' else '' for c in handle)
        
        return f"https://www.linkedin.com/in/{handle}"
    
    def generate_lead(self, industry: Optional[str] = None) -> Lead:
        """
        Generate a single lead with valid data.
        
        Args:
            industry: Specific industry (random if None)
            
        Returns:
            Lead object with valid data
        """
        # Select industry
        if industry and industry in self.industries:
            selected_industry = industry
        else:
            selected_industry = random.choice(self.industries)
        
        # Select country and create locale-specific faker
        country = random.choice(list(COUNTRIES.keys()))
        locale = COUNTRIES[country]
        
        # Create locale-specific faker for names
        locale_faker = Faker(locale)
        if self.seed is not None:
            locale_faker.seed_instance(self.seed + hash(country))
        
        # Generate full name
        full_name = locale_faker.name()
        
        # Select appropriate role for industry
        roles = INDUSTRY_ROLES[selected_industry]
        role = random.choice(roles)
        
        # Generate company name
        company_name = self._generate_company_name(selected_industry)
        
        # Generate other fields
        website = self._generate_website(company_name)
        email = self._generate_email(full_name, company_name)
        linkedin_url = self._generate_linkedin_url(full_name)
        
        # Create lead object
        lead = Lead(
            id=str(uuid.uuid4()),
            full_name=full_name,
            company_name=company_name,
            role=role,
            industry=selected_industry,
            website=website,
            email=email,
            linkedin_url=linkedin_url,
            country=country,
            status=LeadStatus.NEW,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return lead
    
    def generate_leads(
        self,
        count: int = 200,
        industries: Optional[List[str]] = None
    ) -> List[Lead]:
        """
        Generate multiple leads.
        
        Args:
            count: Number of leads to generate
            industries: List of industries to filter by (all if None)
            
        Returns:
            List of Lead objects
        """
        leads = []
        
        # Filter industries if specified
        available_industries = industries if industries else self.industries
        available_industries = [i for i in available_industries if i in self.industries]
        
        if not available_industries:
            available_industries = self.industries
        
        for i in range(count):
            # Rotate through industries for even distribution
            industry = available_industries[i % len(available_industries)]
            lead = self.generate_lead(industry)
            leads.append(lead)
        
        return leads
    
    def get_available_industries(self) -> List[str]:
        """
        Get list of available industries.
        
        Returns:
            List of industry names
        """
        return self.industries.copy()


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def generate_leads(
    count: int = 200,
    seed: Optional[int] = None,
    industries: Optional[List[str]] = None
) -> List[Lead]:
    """
    Convenience function to generate leads.
    
    Args:
        count: Number of leads to generate
        seed: Random seed for reproducibility
        industries: List of industries to filter by
        
    Returns:
        List of Lead objects
    """
    generator = LeadGenerator(seed=seed)
    return generator.generate_leads(count=count, industries=industries)


if __name__ == "__main__":
    # Test lead generation
    print("Testing Lead Generator...")
    print("-" * 50)
    
    # Generate with seed for reproducibility
    leads = generate_leads(count=5, seed=42)
    
    for lead in leads:
        print(f"Name: {lead.full_name}")
        print(f"Company: {lead.company_name}")
        print(f"Role: {lead.role}")
        print(f"Industry: {lead.industry}")
        print(f"Website: {lead.website}")
        print(f"Email: {lead.email}")
        print(f"LinkedIn: {lead.linkedin_url}")
        print(f"Country: {lead.country}")
        print("-" * 50)
