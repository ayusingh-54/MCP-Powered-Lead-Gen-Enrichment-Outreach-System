"""
Validation Utilities
====================
Provides validation helpers for ensuring data integrity.
Includes email, URL, and LinkedIn URL validation.
"""

import re
from typing import Tuple, List
from urllib.parse import urlparse


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # RFC 5322 compliant email regex (simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email:
        return False, "Email is required"
    
    if len(email) > 254:
        return False, "Email exceeds maximum length"
    
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, ""


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    try:
        result = urlparse(url)
        
        # Check for required components
        if not result.scheme:
            return False, "URL must include scheme (http/https)"
        
        if result.scheme not in ("http", "https"):
            return False, "URL scheme must be http or https"
        
        if not result.netloc:
            return False, "URL must include domain"
        
        # Check for valid domain format
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, result.netloc.split(':')[0]):
            return False, "Invalid domain format"
        
        return True, ""
        
    except Exception as e:
        return False, f"URL parsing error: {str(e)}"


def validate_linkedin_url(url: str) -> Tuple[bool, str]:
    """
    Validate LinkedIn profile URL format.
    
    Args:
        url: LinkedIn URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "LinkedIn URL is required"
    
    # Check basic URL validity first
    is_valid, error = validate_url(url)
    if not is_valid:
        return False, error
    
    # LinkedIn URL patterns
    linkedin_patterns = [
        r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?$',
        r'^https?://(www\.)?linkedin\.com/pub/[a-zA-Z0-9_-]+(/[a-zA-Z0-9]+)*/?$',
    ]
    
    for pattern in linkedin_patterns:
        if re.match(pattern, url):
            return True, ""
    
    return False, "Invalid LinkedIn profile URL format"


def validate_lead_data(lead_data: dict) -> Tuple[bool, List[str]]:
    """
    Validate all fields of a lead.
    
    Args:
        lead_data: Dictionary containing lead fields
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required_fields = [
        "full_name", "company_name", "role", "industry",
        "website", "email", "linkedin_url", "country"
    ]
    
    for field in required_fields:
        if field not in lead_data or not lead_data[field]:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate email
    is_valid, error = validate_email(lead_data["email"])
    if not is_valid:
        errors.append(f"Email: {error}")
    
    # Validate website
    is_valid, error = validate_url(lead_data["website"])
    if not is_valid:
        errors.append(f"Website: {error}")
    
    # Validate LinkedIn URL
    is_valid, error = validate_linkedin_url(lead_data["linkedin_url"])
    if not is_valid:
        errors.append(f"LinkedIn: {error}")
    
    # Validate name length
    if len(lead_data["full_name"]) < 2:
        errors.append("Full name must be at least 2 characters")
    
    if len(lead_data["full_name"]) > 100:
        errors.append("Full name exceeds maximum length")
    
    return len(errors) == 0, errors


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    Sanitize a string for safe storage and display.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")
    
    # Trim whitespace
    text = text.strip()
    
    # Truncate if needed
    if len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    return text


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Text to count words in
        
    Returns:
        Word count
    """
    if not text:
        return 0
    
    # Split on whitespace and filter empty strings
    words = [w for w in text.split() if w]
    return len(words)
