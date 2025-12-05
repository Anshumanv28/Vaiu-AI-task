"""
Email extraction and validation utilities
"""
import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    """
    Validate email format using regex
    Args:
        email: Email string to validate
    Returns:
        True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    if not email:
        return False
    
    # RFC 5322 compliant regex (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from text
    Args:
        text: Text that may contain an email address
    Returns:
        Extracted email address or None if not found
    """
    if not text or not isinstance(text, str):
        return None
    
    # Pattern to match email addresses
    pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    matches = re.findall(pattern, text)
    
    if matches:
        # Return the first valid email found
        for match in matches:
            if is_valid_email(match):
                return match.lower().strip()
    
    return None

