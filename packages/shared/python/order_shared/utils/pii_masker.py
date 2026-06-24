"""PII masking utility for safe logging.

Masks email addresses, phone numbers, and names in log strings.
"""

import re


def mask_email(email: str) -> str:
    """Mask an email address: john.doe@example.com -> j***@example.com"""
    if "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    if len(local) <= 1:
        masked_local = "*"
    else:
        masked_local = local[0] + "***"
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask a phone number: +14165551234 -> ***-***-1234"""
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) >= 4:
        return f"***-***-{digits[-4:]}"
    return "***"


def mask_name(name: str) -> str:
    """Mask a person's name: John Doe -> J*** D***"""
    parts = name.split()
    masked_parts = []
    for part in parts:
        if len(part) <= 1:
            masked_parts.append("*")
        else:
            masked_parts.append(part[0] + "***")
    return " ".join(masked_parts)


def mask_pii(text: str) -> str:
    """Apply PII masking to a text string.

    Detects and masks:
    - Email addresses
    - Phone numbers (various formats)
    - Does NOT mask names (too many false positives in free text)

    Used by the structured logger to sanitize log output.
    """
    # Mask email addresses
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    text = re.sub(email_pattern, lambda m: mask_email(m.group()), text)

    # Mask phone numbers (various formats)
    # +1-416-555-1234, (416) 555-1234, 416.555.1234, 4165551234
    phone_pattern = r"(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
    text = re.sub(phone_pattern, lambda m: mask_phone(m.group()), text)

    return text
