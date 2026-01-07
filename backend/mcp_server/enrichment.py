"""
Lead Enrichment Module
======================
Enriches leads with additional business intelligence:
- Company size estimation
- Persona classification
- Pain points identification
- Buying triggers detection
- Confidence scoring

Supports two modes:
1. OFFLINE: Rule-based heuristics (no external APIs)
2. AI: Mock LLM enrichment (simulates AI-powered insights)
"""

import random
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.models import LeadEnrichment, CompanySize, EnrichmentMode


# =============================================================================
# ENRICHMENT KNOWLEDGE BASE
# =============================================================================

# Persona mappings based on role keywords
PERSONA_MAPPINGS = {
    # Operations leaders
    ("operations", "ops", "coo", "operating"): "Operations Leader",
    # Data/Analytics leaders
    ("data", "analytics", "bi", "intelligence"): "Data Leader",
    # Technology leaders
    ("cto", "technology", "engineering", "tech", "it director"): "Tech Leader",
    # Finance leaders
    ("cfo", "finance", "financial", "treasury", "controller"): "Finance Leader",
    # Supply chain leaders
    ("supply chain", "procurement", "logistics", "sourcing"): "Supply Chain Leader",
    # Sales/Commercial leaders
    ("sales", "commercial", "revenue", "business development"): "Sales Leader",
    # Marketing leaders
    ("marketing", "cmo", "brand", "growth"): "Marketing Leader",
    # HR leaders
    ("hr", "human resources", "people", "talent"): "HR Leader",
    # C-suite general
    ("ceo", "chief executive", "president", "managing director"): "Executive Leader",
}

# Industry-specific pain points
INDUSTRY_PAIN_POINTS = {
    "Technology": [
        "Scaling engineering teams efficiently",
        "Managing technical debt and legacy systems",
        "Ensuring data security and compliance",
        "Accelerating time-to-market for new features",
        "Retaining top technical talent",
        "Integrating disparate systems and tools",
        "Managing cloud infrastructure costs",
        "Implementing effective DevOps practices"
    ],
    "Finance": [
        "Regulatory compliance burden increasing",
        "Manual processes slowing operations",
        "Data silos preventing unified view",
        "Risk management becoming more complex",
        "Customer expectations rising",
        "Legacy systems limiting agility",
        "Fraud detection and prevention",
        "Real-time reporting requirements"
    ],
    "Healthcare": [
        "Patient data management challenges",
        "Interoperability between systems",
        "Regulatory compliance (HIPAA, etc.)",
        "Cost containment pressures",
        "Staff burnout and retention",
        "Care coordination difficulties",
        "Telehealth integration needs",
        "Clinical workflow optimization"
    ],
    "Manufacturing": [
        "Supply chain disruptions",
        "Production efficiency optimization",
        "Quality control consistency",
        "Equipment downtime reduction",
        "Workforce skill gaps",
        "Inventory management complexity",
        "Sustainability requirements",
        "Digital transformation challenges"
    ],
    "Retail": [
        "Omnichannel experience consistency",
        "Inventory visibility across channels",
        "Customer data unification",
        "Last-mile delivery optimization",
        "Personalization at scale",
        "Returns management costs",
        "Seasonal demand forecasting",
        "Store operations efficiency"
    ],
    "Logistics": [
        "Route optimization complexity",
        "Real-time visibility gaps",
        "Driver shortage and retention",
        "Fuel cost management",
        "Delivery time pressures",
        "Warehouse efficiency",
        "Returns logistics handling",
        "Cross-border compliance"
    ],
    "Energy": [
        "Grid modernization needs",
        "Renewable integration challenges",
        "Asset maintenance optimization",
        "Regulatory compliance costs",
        "Demand forecasting accuracy",
        "Sustainability reporting requirements",
        "Workforce transition management",
        "Cybersecurity threats increasing"
    ],
    "Consulting": [
        "Knowledge management across teams",
        "Resource utilization optimization",
        "Project margin pressures",
        "Client retention challenges",
        "Talent development and retention",
        "Scaling delivery capabilities",
        "Competitive differentiation",
        "Digital offering development"
    ],
    "Telecommunications": [
        "Network infrastructure modernization",
        "Customer churn reduction",
        "5G deployment complexities",
        "Service quality management",
        "Competitive pricing pressure",
        "Legacy system migration",
        "Cybersecurity threats",
        "Customer experience improvement"
    ],
    "Real Estate": [
        "Property management efficiency",
        "Tenant experience improvement",
        "Sustainability compliance",
        "Market volatility navigation",
        "Data-driven decision making",
        "Asset valuation accuracy",
        "Regulatory compliance",
        "Remote work impact on portfolios"
    ]
}

# Persona-specific pain points (overlay on industry)
PERSONA_PAIN_POINTS = {
    "Operations Leader": [
        "Process efficiency and standardization",
        "Cross-functional coordination challenges",
        "Operational cost optimization"
    ],
    "Data Leader": [
        "Data quality and governance",
        "Democratizing data access",
        "Building data-driven culture"
    ],
    "Tech Leader": [
        "Technical talent acquisition",
        "Technology stack modernization",
        "Innovation vs. maintenance balance"
    ],
    "Supply Chain Leader": [
        "Supplier risk management",
        "Demand forecasting accuracy",
        "End-to-end visibility"
    ],
    "Finance Leader": [
        "Cash flow optimization",
        "Financial planning accuracy",
        "Audit and compliance burden"
    ]
}

# Industry-specific buying triggers
INDUSTRY_BUYING_TRIGGERS = {
    "Technology": [
        "Series B+ funding received",
        "Rapid headcount growth planned",
        "New product launch announced",
        "International expansion planned",
        "Digital transformation initiative",
        "New CTO/VP Engineering hired"
    ],
    "Finance": [
        "Regulatory changes announced",
        "M&A activity",
        "New compliance requirements",
        "Digital banking initiative",
        "Cost reduction mandate"
    ],
    "Healthcare": [
        "New facility opening",
        "EMR/EHR migration planned",
        "Value-based care initiative",
        "Telehealth expansion",
        "New leadership appointed"
    ],
    "Manufacturing": [
        "New facility construction",
        "Industry 4.0 initiative",
        "Supply chain restructuring",
        "Sustainability commitment",
        "Automation investment planned"
    ],
    "Retail": [
        "E-commerce expansion",
        "New store openings",
        "Omnichannel initiative",
        "Customer experience overhaul",
        "Loyalty program launch"
    ],
    "Logistics": [
        "Fleet expansion planned",
        "New distribution center",
        "Technology modernization",
        "Service expansion",
        "Sustainability initiative"
    ],
    "Energy": [
        "Renewable investment announced",
        "Grid modernization project",
        "New regulatory requirements",
        "Sustainability targets set",
        "Asset optimization initiative"
    ],
    "Consulting": [
        "New practice area launch",
        "Geographic expansion",
        "Digital capabilities investment",
        "Partnership announcement",
        "Major client win"
    ],
    "Telecommunications": [
        "5G rollout",
        "Network expansion",
        "New service launch",
        "Customer experience initiative",
        "Infrastructure investment"
    ],
    "Real Estate": [
        "Portfolio expansion",
        "PropTech adoption",
        "Sustainability retrofit",
        "New development project",
        "Management technology upgrade"
    ]
}


# =============================================================================
# ENRICHMENT ENGINE
# =============================================================================

class EnrichmentEngine:
    """
    Enriches lead data using rule-based heuristics or AI simulation.
    Provides consistent, deterministic enrichment based on lead attributes.
    """
    
    def __init__(self, mode: EnrichmentMode = EnrichmentMode.OFFLINE, seed: Optional[int] = None):
        """
        Initialize enrichment engine.
        
        Args:
            mode: Enrichment mode (OFFLINE or AI)
            seed: Random seed for reproducibility
        """
        self.mode = mode
        self.seed = seed
        
        if seed is not None:
            random.seed(seed)
    
    def _deterministic_random(self, lead_id: str, salt: str = "") -> float:
        """
        Generate deterministic random value based on lead ID.
        Ensures same lead always gets same enrichment.
        
        Args:
            lead_id: Lead identifier
            salt: Additional salt for different random streams
            
        Returns:
            Float between 0 and 1
        """
        hash_input = f"{lead_id}{salt}".encode()
        hash_value = hashlib.md5(hash_input).hexdigest()
        return int(hash_value[:8], 16) / 0xFFFFFFFF
    
    def _classify_company_size(self, lead: Dict) -> CompanySize:
        """
        Estimate company size based on lead attributes.
        Uses heuristics based on role seniority and industry.
        
        Args:
            lead: Lead dictionary
            
        Returns:
            CompanySize enum value
        """
        role = lead.get("role", "").lower()
        industry = lead.get("industry", "")
        company = lead.get("company_name", "").lower()
        
        # Enterprise indicators
        enterprise_roles = ["chief", "vp", "vice president", "director", "head"]
        enterprise_industries = ["Finance", "Healthcare", "Energy", "Telecommunications"]
        enterprise_company_words = ["global", "international", "holdings", "group", "corp"]
        
        # Score-based classification
        score = 0
        
        # Role scoring
        if any(r in role for r in enterprise_roles):
            score += 2
        
        # Industry scoring
        if industry in enterprise_industries:
            score += 1
        
        # Company name scoring
        if any(w in company for w in enterprise_company_words):
            score += 1
        
        # Add some randomness for variety
        random_factor = self._deterministic_random(lead.get("id", ""), "size")
        if random_factor > 0.8:
            score += 1
        elif random_factor < 0.2:
            score -= 1
        
        # Classify based on score
        if score >= 3:
            return CompanySize.ENTERPRISE
        elif score >= 1:
            return CompanySize.MEDIUM
        else:
            return CompanySize.SMALL
    
    def _classify_persona(self, lead: Dict) -> str:
        """
        Classify lead into a persona based on role.
        
        Args:
            lead: Lead dictionary
            
        Returns:
            Persona string
        """
        role = lead.get("role", "").lower()
        
        # Check against persona mappings
        for keywords, persona in PERSONA_MAPPINGS.items():
            if any(kw in role for kw in keywords):
                return persona
        
        # Default persona based on seniority
        if any(w in role for w in ["vp", "vice president", "head", "director"]):
            return "Senior Leader"
        
        return "Business Leader"
    
    def _get_pain_points(self, lead: Dict, persona: str) -> List[str]:
        """
        Select relevant pain points for the lead.
        
        Args:
            lead: Lead dictionary
            persona: Classified persona
            
        Returns:
            List of 2-3 pain points
        """
        industry = lead.get("industry", "Technology")
        lead_id = lead.get("id", "")
        
        # Get industry pain points
        industry_points = INDUSTRY_PAIN_POINTS.get(industry, INDUSTRY_PAIN_POINTS["Technology"])
        
        # Get persona pain points if available
        persona_points = PERSONA_PAIN_POINTS.get(persona, [])
        
        # Combine and select
        all_points = industry_points + persona_points
        
        # Use deterministic selection
        random.seed(hash(lead_id + "pain"))
        selected = random.sample(all_points, min(3, len(all_points)))
        
        return selected
    
    def _get_buying_triggers(self, lead: Dict) -> List[str]:
        """
        Select relevant buying triggers for the lead.
        
        Args:
            lead: Lead dictionary
            
        Returns:
            List of 1-2 buying triggers
        """
        industry = lead.get("industry", "Technology")
        lead_id = lead.get("id", "")
        
        triggers = INDUSTRY_BUYING_TRIGGERS.get(industry, INDUSTRY_BUYING_TRIGGERS["Technology"])
        
        # Use deterministic selection
        random.seed(hash(lead_id + "triggers"))
        selected = random.sample(triggers, min(2, len(triggers)))
        
        return selected
    
    def _calculate_confidence(self, lead: Dict, company_size: CompanySize, persona: str) -> int:
        """
        Calculate confidence score for the enrichment.
        
        Args:
            lead: Lead dictionary
            company_size: Classified company size
            persona: Classified persona
            
        Returns:
            Confidence score 0-100
        """
        base_score = 60
        
        # Higher confidence for well-known industries
        well_known_industries = ["Technology", "Finance", "Healthcare"]
        if lead.get("industry") in well_known_industries:
            base_score += 10
        
        # Higher confidence for senior roles
        role = lead.get("role", "").lower()
        if any(w in role for w in ["chief", "cto", "cfo", "coo", "vp"]):
            base_score += 10
        
        # Higher confidence for enterprise companies
        if company_size == CompanySize.ENTERPRISE:
            base_score += 5
        
        # Specific persona gets higher confidence
        if persona not in ["Senior Leader", "Business Leader"]:
            base_score += 5
        
        # Add some variance
        lead_id = lead.get("id", "")
        variance = int(self._deterministic_random(lead_id, "confidence") * 20) - 10
        
        final_score = max(40, min(95, base_score + variance))
        
        return final_score
    
    def _ai_enrich(self, lead: Dict) -> Tuple[List[str], List[str], int]:
        """
        Simulate AI-powered enrichment.
        In production, this would call an LLM API.
        
        Args:
            lead: Lead dictionary
            
        Returns:
            Tuple of (pain_points, buying_triggers, confidence_boost)
        """
        # Simulate more sophisticated AI analysis
        # Add "AI-discovered" insights
        ai_pain_points = [
            f"Strategic priority: {lead.get('industry', 'Industry')} digital transformation",
            f"Likely facing: Talent and skill gaps in {lead.get('role', 'role').split()[0]} function"
        ]
        
        ai_triggers = [
            f"Market conditions favorable for {lead.get('industry', 'Industry')} investment"
        ]
        
        confidence_boost = 10  # AI enrichment adds confidence
        
        return ai_pain_points, ai_triggers, confidence_boost
    
    def enrich_lead(self, lead: Dict) -> LeadEnrichment:
        """
        Enrich a single lead with additional business intelligence.
        
        Args:
            lead: Lead dictionary with basic info
            
        Returns:
            LeadEnrichment object with enriched data
        """
        lead_id = lead.get("id", "")
        
        # Basic classifications (rule-based)
        company_size = self._classify_company_size(lead)
        persona = self._classify_persona(lead)
        
        # Get pain points and triggers
        pain_points = self._get_pain_points(lead, persona)
        buying_triggers = self._get_buying_triggers(lead)
        
        # Calculate base confidence
        confidence = self._calculate_confidence(lead, company_size, persona)
        
        # Apply AI enrichment if in AI mode
        if self.mode == EnrichmentMode.AI:
            ai_pain, ai_triggers, confidence_boost = self._ai_enrich(lead)
            
            # Add AI insights
            pain_points = pain_points[:2] + ai_pain[:1]  # Keep 2-3 total
            if len(buying_triggers) < 2:
                buying_triggers.extend(ai_triggers)
            
            confidence = min(95, confidence + confidence_boost)
        
        # Ensure correct list lengths
        pain_points = pain_points[:3] if len(pain_points) > 3 else pain_points
        buying_triggers = buying_triggers[:2] if len(buying_triggers) > 2 else buying_triggers
        
        return LeadEnrichment(
            lead_id=lead_id,
            company_size=company_size,
            persona=persona,
            pain_points=pain_points,
            buying_triggers=buying_triggers,
            confidence_score=confidence,
            enrichment_mode=self.mode,
            enriched_at=datetime.utcnow()
        )
    
    def enrich_leads(self, leads: List[Dict]) -> List[LeadEnrichment]:
        """
        Enrich multiple leads.
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            List of LeadEnrichment objects
        """
        enrichments = []
        
        for lead in leads:
            enrichment = self.enrich_lead(lead)
            enrichments.append(enrichment)
        
        return enrichments


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def enrich_lead(lead: Dict, mode: EnrichmentMode = EnrichmentMode.OFFLINE) -> LeadEnrichment:
    """
    Convenience function to enrich a single lead.
    
    Args:
        lead: Lead dictionary
        mode: Enrichment mode
        
    Returns:
        LeadEnrichment object
    """
    engine = EnrichmentEngine(mode=mode)
    return engine.enrich_lead(lead)


def enrich_leads(leads: List[Dict], mode: EnrichmentMode = EnrichmentMode.OFFLINE) -> List[LeadEnrichment]:
    """
    Convenience function to enrich multiple leads.
    
    Args:
        leads: List of lead dictionaries
        mode: Enrichment mode
        
    Returns:
        List of LeadEnrichment objects
    """
    engine = EnrichmentEngine(mode=mode)
    return engine.enrich_leads(leads)


if __name__ == "__main__":
    # Test enrichment
    print("Testing Lead Enrichment...")
    print("-" * 50)
    
    # Sample lead
    test_lead = {
        "id": "test-123",
        "full_name": "John Smith",
        "company_name": "Acme Tech Corp",
        "role": "VP of Operations",
        "industry": "Technology",
        "website": "https://www.acmetech.com",
        "email": "john.smith@acmetech.com",
        "linkedin_url": "https://www.linkedin.com/in/john-smith",
        "country": "United States"
    }
    
    # Test offline mode
    print("OFFLINE MODE:")
    enrichment = enrich_lead(test_lead, EnrichmentMode.OFFLINE)
    print(f"Company Size: {enrichment.company_size}")
    print(f"Persona: {enrichment.persona}")
    print(f"Pain Points: {enrichment.pain_points}")
    print(f"Buying Triggers: {enrichment.buying_triggers}")
    print(f"Confidence: {enrichment.confidence_score}")
    print()
    
    # Test AI mode
    print("AI MODE:")
    enrichment_ai = enrich_lead(test_lead, EnrichmentMode.AI)
    print(f"Company Size: {enrichment_ai.company_size}")
    print(f"Persona: {enrichment_ai.persona}")
    print(f"Pain Points: {enrichment_ai.pain_points}")
    print(f"Buying Triggers: {enrichment_ai.buying_triggers}")
    print(f"Confidence: {enrichment_ai.confidence_score}")
