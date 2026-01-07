"""
Message Generator Module
========================
Generates personalized outreach messages for leads:
- Cold emails (max 120 words)
- LinkedIn DMs (max 60 words)
- A/B variants for testing
- References enrichment insights
- Includes clear CTAs
- Supports both template-based and AI-powered generation
"""

import os
import random
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.models import GeneratedMessage

# Try to import OpenAI (optional dependency)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


# =============================================================================
# MESSAGE TEMPLATES
# =============================================================================

# Email templates - Variant A (Direct approach)
EMAIL_TEMPLATES_A = [
    {
        "subject": "Quick question about {pain_point_short}",
        "body": """Hi {first_name},

I noticed {company_name} is in the {industry} space, and I've been helping {persona}s tackle {pain_point}.

{trigger_context}

Would you be open to a quick 15-minute call to explore how we might help {company_name} address this?

Best,
{sender_name}"""
    },
    {
        "subject": "{persona} at {company_name} - quick thought",
        "body": """Hi {first_name},

As a {persona} at {company_name}, you're likely dealing with {pain_point}.

We've helped similar {industry} companies solve this challenge. {trigger_context}

Would a brief 15-minute call make sense to discuss?

Best regards,
{sender_name}"""
    },
    {
        "subject": "Idea for {company_name}",
        "body": """{first_name},

{industry} leaders like yourself often mention {pain_point} as a top priority.

{trigger_context}

I'd love to share how we've helped other {persona}s address this. Do you have 15 minutes this week?

Thanks,
{sender_name}"""
    }
]

# Email templates - Variant B (Value-first approach)
EMAIL_TEMPLATES_B = [
    {
        "subject": "A resource for {industry} leaders",
        "body": """Hi {first_name},

I came across {company_name} and thought you might find value in our latest research on {pain_point_short}.

{trigger_context}

Happy to share insights from similar {persona}s in {industry}. Worth a 15-minute conversation?

Cheers,
{sender_name}"""
    },
    {
        "subject": "Solving {pain_point_short} at {company_name}",
        "body": """Hi {first_name},

{persona}s in {industry} have shared that {pain_point} is a major focus right now.

{trigger_context}

I have some ideas that might help {company_name}. Open to a quick 15-minute chat?

Best,
{sender_name}"""
    },
    {
        "subject": "For {first_name} at {company_name}",
        "body": """{first_name},

Noticed {company_name}'s growth in {industry}. Many {persona}s I speak with mention {pain_point} as a key challenge.

{trigger_context}

Would you be interested in a brief 15-minute call to explore solutions?

Regards,
{sender_name}"""
    }
]

# LinkedIn DM templates - Variant A
LINKEDIN_TEMPLATES_A = [
    """Hi {first_name}, I help {persona}s in {industry} tackle {pain_point_short}. Would love to connect and share ideas. Open to a quick chat?""",
    
    """Hi {first_name}! Impressed by {company_name}'s work. I focus on helping {industry} leaders with {pain_point_short}. Worth connecting?""",
    
    """{first_name}, as a {persona} you might find our {industry} insights valuable. {trigger_short} Happy to share over a brief call."""
]

# LinkedIn DM templates - Variant B
LINKEDIN_TEMPLATES_B = [
    """Hi {first_name}, connecting with {industry} leaders like yourself. I specialize in {pain_point_short}. Would value your perspective - open to a quick chat?""",
    
    """Hey {first_name}! Love what {company_name} is doing. I work with {persona}s on {pain_point_short}. Interested in connecting?""",
    
    """{first_name}, saw your profile and thought we might have synergies. I help {industry} companies with {pain_point_short}. Quick call sometime?"""
]

# CTAs
EMAIL_CTAS = [
    "15-minute call",
    "brief chat",
    "quick conversation",
    "short call this week"
]

LINKEDIN_CTAS = [
    "quick chat",
    "brief call",
    "connect"
]


# =============================================================================
# MESSAGE GENERATOR ENGINE
# =============================================================================

class MessageGenerator:
    """
    Generates personalized outreach messages using templates and lead/enrichment data.
    Ensures messages stay within word limits and reference real insights.
    Supports both template-based and AI-powered generation (via OpenAI).
    """
    
    def __init__(self, sender_name: str = "Alex Johnson", seed: Optional[int] = None, use_ai: bool = None):
        """
        Initialize message generator.
        
        Args:
            sender_name: Name to use as sender in messages
            seed: Random seed for reproducibility
            use_ai: Use AI-powered generation if available (defaults to env var OPENAI_ENABLED)
        """
        self.sender_name = sender_name
        self.seed = seed
        
        # Determine if AI should be used
        if use_ai is None:
            use_ai = os.getenv("OPENAI_ENABLED", "false").lower() == "true"
        
        self.use_ai = use_ai and OPENAI_AVAILABLE
        
        # Configure OpenAI if available and enabled
        if self.use_ai:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                openai.api_key = api_key
                self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                print(f"MessageGenerator: AI-powered generation enabled (model: {self.openai_model})")
            else:
                self.use_ai = False
                print("MessageGenerator: OpenAI API key not found, falling back to template-based generation")
        else:
            print("MessageGenerator: Using template-based generation")
        
        if seed is not None:
            random.seed(seed)
    
    def _deterministic_choice(self, lead_id: str, options: List, salt: str = "") -> any:
        """
        Make deterministic random choice based on lead ID.
        
        Args:
            lead_id: Lead identifier
            options: List of options to choose from
            salt: Additional salt for different selections
            
        Returns:
            Selected option
        """
        hash_input = f"{lead_id}{salt}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest()[:8], 16)
        return options[hash_value % len(options)]
    
    def _get_first_name(self, full_name: str) -> str:
        """Extract first name from full name."""
        return full_name.split()[0] if full_name else "there"
    
    def _shorten_pain_point(self, pain_point: str, max_words: int = 6) -> str:
        """
        Shorten pain point for subject lines and short messages.
        
        Args:
            pain_point: Full pain point text
            max_words: Maximum words to keep
            
        Returns:
            Shortened pain point
        """
        words = pain_point.split()[:max_words]
        shortened = " ".join(words)
        
        # Remove trailing punctuation and add lowercase
        shortened = shortened.rstrip(".,;:")
        
        return shortened.lower()
    
    def _create_trigger_context(self, triggers: List[str], industry: str) -> str:
        """
        Create trigger context sentence.
        
        Args:
            triggers: List of buying triggers
            industry: Industry name
            
        Returns:
            Trigger context sentence
        """
        if not triggers:
            return f"Given the current {industry} landscape, timing seems right."
        
        trigger = triggers[0]
        
        # Create natural sentence
        contexts = [
            f"Given {trigger.lower()}, this might be timely.",
            f"With {trigger.lower()} on the horizon, this could be relevant.",
            f"I understand {trigger.lower()} - this might help.",
        ]
        
        return random.choice(contexts)
    
    def _shorten_trigger(self, triggers: List[str]) -> str:
        """Create short trigger reference for LinkedIn."""
        if not triggers:
            return "Timing seems right!"
        
        trigger = triggers[0]
        words = trigger.split()[:4]
        return " ".join(words) + "!"
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def _truncate_to_word_limit(self, text: str, max_words: int) -> str:
        """
        Truncate text to word limit while keeping it coherent.
        
        Args:
            text: Text to truncate
            max_words: Maximum word count
            
        Returns:
            Truncated text
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        
        # Find last sentence that fits
        truncated = " ".join(words[:max_words])
        
        # Try to end at sentence boundary
        last_period = truncated.rfind(".")
        last_question = truncated.rfind("?")
        last_boundary = max(last_period, last_question)
        
        if last_boundary > len(truncated) * 0.5:  # At least half the content
            return truncated[:last_boundary + 1]
        
        return truncated + "..."
    
    def _generate_with_ai(
        self,
        lead: Dict,
        enrichment: Dict,
        channel: str,
        variant: str,
        max_words: int
    ) -> Dict[str, str]:
        """
        Generate message content using OpenAI API.
        
        Args:
            lead: Lead dictionary
            enrichment: Enrichment dictionary
            channel: 'email' or 'linkedin'
            variant: 'A' or 'B'
            max_words: Maximum word count
            
        Returns:
            Dictionary with 'subject' (for email) and 'body' keys
        """
        if not self.use_ai:
            return None
        
        # Prepare context
        pain_points = enrichment.get("pain_points", [])
        triggers = enrichment.get("buying_triggers", [])
        persona = enrichment.get("persona", "executive")
        
        # Build prompt based on channel and variant
        if channel == "email":
            approach = "direct and value-focused" if variant == "A" else "consultative and insight-sharing"
            prompt = f"""Write a personalized cold email for outreach. Requirements:

Lead Details:
- Name: {lead.get('full_name')}
- Company: {lead.get('company_name')}
- Role: {lead.get('role')}
- Industry: {lead.get('industry')}
- Persona: {persona}

Context:
- Pain Point: {pain_points[0] if pain_points else 'operational efficiency'}
- Buying Trigger: {triggers[0] if triggers else 'growth initiative'}

Instructions:
1. Write in a {approach} tone
2. Maximum {max_words} words total
3. Reference ONE pain point naturally
4. Include ONE buying trigger context
5. Clear CTA: "15-minute call"
6. Use {lead.get('full_name').split()[0]} as first name
7. Sign off as {self.sender_name}
8. DO NOT hallucinate company facts
9. Keep it professional and concise

Format:
Subject: [write subject line here]

Body:
[write email body here]"""
        
        else:  # linkedin
            approach = "direct" if variant == "A" else "value-first"
            prompt = f"""Write a personalized LinkedIn DM. Requirements:

Lead: {lead.get('full_name')}, {lead.get('role')} at {lead.get('company_name')}
Industry: {lead.get('industry')}
Persona: {persona}
Pain Point: {pain_points[0] if pain_points else 'operational challenges'}
Buying Trigger: {triggers[0] if triggers else 'growth phase'}

Instructions:
1. {approach} approach
2. MAXIMUM {max_words} words
3. Reference pain point briefly
4. Clear CTA: "15-minute call"
5. Use first name only: {lead.get('full_name').split()[0]}
6. Professional but conversational
7. NO hallucinated facts

Write the message:"""
        
        try:
            response = openai.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert B2B outreach copywriter. Write concise, personalized messages that reference real insights without hallucinating facts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Parse response
            if channel == "email":
                # Extract subject and body
                if "Subject:" in generated_text:
                    parts = generated_text.split("\n\n", 1)
                    subject_line = parts[0].replace("Subject:", "").strip()
                    body = parts[1].strip() if len(parts) > 1 else generated_text
                else:
                    # Fallback: first line as subject
                    lines = generated_text.split("\n")
                    subject_line = lines[0].strip()
                    body = "\n".join(lines[1:]).strip()
                
                return {"subject": subject_line, "body": body}
            else:
                return {"body": generated_text}
                
        except Exception as e:
            print(f"AI generation failed: {e}. Falling back to templates.")
            return None
    
    def generate_email(
        self,
        lead: Dict,
        enrichment: Dict,
        variant: str = "A"
    ) -> GeneratedMessage:
        """
        Generate a cold email for a lead.
        
        Args:
            lead: Lead dictionary
            enrichment: Enrichment dictionary
            variant: A or B variant
            
        Returns:
            GeneratedMessage object
        """
        lead_id = lead.get("id", "")
        max_words = 120
        
        # Try AI generation first if enabled
        ai_result = self._generate_with_ai(lead, enrichment, "email", variant, max_words)
        
        if ai_result:
            # Use AI-generated content
            subject = ai_result["subject"]
            body = ai_result["body"]
            word_count = self._count_words(body)
            
            # Truncate if needed
            if word_count > max_words:
                body = self._truncate_to_word_limit(body, max_words)
                word_count = self._count_words(body)
            
            # Extract pain point and CTA
            pain_points = enrichment.get("pain_points", ["operational challenges"])
            referenced_insight = pain_points[0] if pain_points else "business challenges"
            cta = "15-minute call" if "15" in body else "call"
            
        else:
            # Fall back to template-based generation
            templates = EMAIL_TEMPLATES_A if variant == "A" else EMAIL_TEMPLATES_B
            template = self._deterministic_choice(lead_id, templates, f"email_{variant}")
            
            # Get enrichment data
            pain_points = enrichment.get("pain_points", ["operational challenges"])
            triggers = enrichment.get("buying_triggers", [])
        persona = enrichment.get("persona", "Business Leader")
        
        # Prepare template variables
        variables = {
            "first_name": self._get_first_name(lead.get("full_name", "")),
            "company_name": lead.get("company_name", "your company"),
            "industry": lead.get("industry", "your industry"),
            "persona": persona,
            "pain_point": pain_points[0] if pain_points else "key challenges",
            "pain_point_short": self._shorten_pain_point(pain_points[0] if pain_points else "key challenges"),
            "trigger_context": self._create_trigger_context(triggers, lead.get("industry", "")),
            "sender_name": self.sender_name
        }
        
        # Generate subject and body
        subject = template["subject"].format(**variables)
        body = template["body"].format(**variables)
        
        # Ensure word limit
        body = self._truncate_to_word_limit(body, 120)
        word_count = self._count_words(body)
        
        # Determine CTA used
        cta = self._deterministic_choice(lead_id, EMAIL_CTAS, f"cta_{variant}")
        
        return GeneratedMessage(
            lead_id=lead_id,
            channel="email",
            variant=variant,
            subject=subject,
            body=body,
            word_count=word_count,
            cta=cta,
            referenced_insight=pain_points[0] if pain_points else "industry challenge",
            generated_at=datetime.utcnow()
        )
    
    def generate_linkedin_dm(
        self,
        lead: Dict,
        enrichment: Dict,
        variant: str = "A"
    ) -> GeneratedMessage:
        """
        Generate a LinkedIn DM for a lead.
        
        Args:
            lead: Lead dictionary
            enrichment: Enrichment dictionary
            variant: A or B variant
            
        Returns:
            GeneratedMessage object
        """
        lead_id = lead.get("id", "")
        max_words = 60
        
        # Try AI generation first if enabled
        ai_result = self._generate_with_ai(lead, enrichment, "linkedin", variant, max_words)
        
        if ai_result:
            # Use AI-generated content
            body = ai_result["body"]
            word_count = self._count_words(body)
            
            # Truncate if needed
            if word_count > max_words:
                body = self._truncate_to_word_limit(body, max_words)
                word_count = self._count_words(body)
            
            # Extract pain point and CTA
            pain_points = enrichment.get("pain_points", ["operational challenges"])
            referenced_insight = pain_points[0] if pain_points else "business challenges"
            cta = "15-minute call" if "15" in body else "call"
            
        else:
            # Fall back to template-based generation
            templates = LINKEDIN_TEMPLATES_A if variant == "A" else LINKEDIN_TEMPLATES_B
            template = self._deterministic_choice(lead_id, templates, f"linkedin_{variant}")
            
            # Get enrichment data
            pain_points = enrichment.get("pain_points", ["operational challenges"])
            triggers = enrichment.get("buying_triggers", [])
        persona = enrichment.get("persona", "Business Leader")
        
        # Prepare template variables
        variables = {
            "first_name": self._get_first_name(lead.get("full_name", "")),
            "company_name": lead.get("company_name", "your company"),
            "industry": lead.get("industry", "your industry"),
            "persona": persona,
            "pain_point_short": self._shorten_pain_point(pain_points[0] if pain_points else "key challenges", 4),
            "trigger_short": self._shorten_trigger(triggers)
        }
        
        # Generate body
        body = template.format(**variables)
        
        # Ensure word limit (60 words for LinkedIn)
        body = self._truncate_to_word_limit(body, 60)
        word_count = self._count_words(body)
        
        # Determine CTA used
        cta = self._deterministic_choice(lead_id, LINKEDIN_CTAS, f"linkedin_cta_{variant}")
        
        return GeneratedMessage(
            lead_id=lead_id,
            channel="linkedin",
            variant=variant,
            subject=None,  # LinkedIn DMs don't have subjects
            body=body,
            word_count=word_count,
            cta=cta,
            referenced_insight=pain_points[0] if pain_points else "industry challenge",
            generated_at=datetime.utcnow()
        )
    
    def generate_messages_for_lead(
        self,
        lead: Dict,
        enrichment: Dict,
        channels: List[str] = None,
        generate_ab: bool = True
    ) -> List[GeneratedMessage]:
        """
        Generate all messages for a single lead.
        
        Args:
            lead: Lead dictionary
            enrichment: Enrichment dictionary
            channels: List of channels (default: ["email", "linkedin"])
            generate_ab: Generate both A and B variants
            
        Returns:
            List of GeneratedMessage objects
        """
        if channels is None:
            channels = ["email", "linkedin"]
        
        messages = []
        variants = ["A", "B"] if generate_ab else ["A"]
        
        for channel in channels:
            for variant in variants:
                if channel == "email":
                    message = self.generate_email(lead, enrichment, variant)
                elif channel == "linkedin":
                    message = self.generate_linkedin_dm(lead, enrichment, variant)
                else:
                    continue
                
                messages.append(message)
        
        return messages
    
    def generate_messages_for_leads(
        self,
        leads_with_enrichment: List[Tuple[Dict, Dict]],
        channels: List[str] = None,
        generate_ab: bool = True
    ) -> List[GeneratedMessage]:
        """
        Generate messages for multiple leads.
        
        Args:
            leads_with_enrichment: List of (lead, enrichment) tuples
            channels: List of channels
            generate_ab: Generate both A and B variants
            
        Returns:
            List of all GeneratedMessage objects
        """
        all_messages = []
        
        for lead, enrichment in leads_with_enrichment:
            messages = self.generate_messages_for_lead(
                lead, enrichment, channels, generate_ab
            )
            all_messages.extend(messages)
        
        return all_messages


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def generate_messages(
    lead: Dict,
    enrichment: Dict,
    channels: List[str] = None,
    generate_ab: bool = True,
    sender_name: str = "Alex Johnson"
) -> List[GeneratedMessage]:
    """
    Convenience function to generate messages for a lead.
    
    Args:
        lead: Lead dictionary
        enrichment: Enrichment dictionary
        channels: List of channels
        generate_ab: Generate A/B variants
        sender_name: Sender name to use
        
    Returns:
        List of GeneratedMessage objects
    """
    generator = MessageGenerator(sender_name=sender_name)
    return generator.generate_messages_for_lead(lead, enrichment, channels, generate_ab)


if __name__ == "__main__":
    # Test message generation
    print("Testing Message Generator...")
    print("=" * 60)
    
    # Sample lead and enrichment
    test_lead = {
        "id": "test-123",
        "full_name": "Sarah Johnson",
        "company_name": "TechCorp Solutions",
        "role": "VP of Operations",
        "industry": "Technology",
        "website": "https://www.techcorp.com",
        "email": "sarah.johnson@techcorp.com",
        "linkedin_url": "https://www.linkedin.com/in/sarah-johnson",
        "country": "United States"
    }
    
    test_enrichment = {
        "company_size": "enterprise",
        "persona": "Operations Leader",
        "pain_points": [
            "Scaling engineering teams efficiently",
            "Managing technical debt and legacy systems",
            "Ensuring data security and compliance"
        ],
        "buying_triggers": [
            "Series B+ funding received",
            "Rapid headcount growth planned"
        ],
        "confidence_score": 85
    }
    
    # Generate messages
    messages = generate_messages(test_lead, test_enrichment)
    
    for msg in messages:
        print(f"\n{'='*60}")
        print(f"Channel: {msg.channel.upper()} | Variant: {msg.variant}")
        print(f"Word Count: {msg.word_count} | CTA: {msg.cta}")
        print(f"Referenced Insight: {msg.referenced_insight}")
        if msg.subject:
            print(f"\nSubject: {msg.subject}")
        print(f"\nBody:\n{msg.body}")
