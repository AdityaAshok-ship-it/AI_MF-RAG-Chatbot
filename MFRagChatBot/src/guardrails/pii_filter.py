import re
import logging

logger = logging.getLogger("PIIFilter")

# Aadhaar: 12 digits starting with 2-9, allowing spaces in groups of 4
_AADHAAR_PATTERN = re.compile(r'\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b')

# PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
_PAN_PATTERN = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')

# Indian phone: 10 digits optionally prefixed with +91 or 0, not part of a longer number
_PHONE_PATTERN = re.compile(r'(?<!\d)(?:\+91|0)?[6-9]\d{9}(?!\d)')

# Email address
_EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')

_PII_PATTERNS = [
    ("Aadhaar", _AADHAAR_PATTERN),
    ("PAN", _PAN_PATTERN),
    ("Phone", _PHONE_PATTERN),
    ("Email", _EMAIL_PATTERN),
]

_REFUSAL_MESSAGE = (
    "Your message contains sensitive personal information (such as Aadhaar, PAN, "
    "phone number, or email). For your security, this information cannot be processed. "
    "Please remove personal details and ask only about HDFC mutual fund facts."
)


class PIIFilter:
    def contains_pii(self, text: str) -> bool:
        """Return True if the text contains any detectable PII."""
        for label, pattern in _PII_PATTERNS:
            if pattern.search(text):
                logger.warning(f"PII detected: {label} pattern matched in input.")
                return True
        return False

    def get_refusal_message(self) -> str:
        return _REFUSAL_MESSAGE
