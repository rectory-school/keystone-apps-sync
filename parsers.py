"""Parsers for managers"""

import logging

from typing import Any
from abc import ABC, abstractmethod
import re

log = logging.getLogger(__name__)

class Parser(ABC):
    """Base parser that configures failure modes"""

    def __init__(self, default_value: Any = Exception):
        self.default_value = default_value

    @abstractmethod
    def transform(self, val: Any) -> Any:
        """Transform into a new value, pass through the value unchanged, or through a ValueError"""

        raise NotImplementedError()

    def parse(self, val: Any) -> Any:
        """Call the transform and handle the errors"""

        try:
            return self.transform(val)
        except ValueError as exc:
            if self.default_value == Exception:
                raise exc
            
            return self.default_value

class BooleanParse(Parser):
    """Transform a variety of boolean values into a bool"""

    def transform(self, val: Any) -> bool:
        if val == True:
            return True
        
        if val == False:
            return False
        
        if val == None:
            raise ValueError("Value was none")
        
        if val.lower().strip() in {'yes', 'true', 't', '1'}:
            return True
        
        if val.lower().strip() in {'no', 'false', 'f', '0'}:
            return False
        
        raise ValueError(f"Unknown true/false value: {val}")

class BoarderDayParser(Parser):
    """Transform B/D values into a boolean 'is_boarder'"""

    def transform(self, val: str) -> bool:
        if not val:
            raise ValueError("Boarder/day value was empty")
        
        val = val.strip()

        if val == 'B':
            return True
        
        if val == 'D':
            return False
        
        raise ValueError("Unknown boarder/day value")
    
    def is_boarder(self, val: str) -> bool:
        """Determine if the student is a boarding student"""

        return self.transform(val)

class EmailParser(Parser):
    """Email parser"""

    user_regex = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',  # quoted-string
        re.IGNORECASE)

    domain_regex = re.compile(
        # max length for domain name labels is 63 characters per RFC 1034
        r'((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))\Z',
        re.IGNORECASE)

    def transform(self, val: str) -> Any:
        if not val:
            raise ValueError('Email is empty')
        
        # Clean up any whitespace
        val = val.strip()

        if '@' not in val:
            raise ValueError('Email must have at least an "@"')

        # From this part on, we are pretty well a copy/paste from Django's validator
        # This is so that I can remove my janky Django dependency for email validation
        user_part, domain_part = val.rsplit('@', 1)

        EmailParser.validate_user_part(user_part)
        EmailParser.validate_domain_part(domain_part)

        return val
    
    @staticmethod
    def validate_user_part(user_part):
        """Validate the user part of the email address"""

        if not EmailParser.user_regex.match(user_part):
            raise ValueError("User part of email was not valid")

    @staticmethod
    def validate_domain_part(domain_part):
        if not EmailParser.domain_regex.match(domain_part):
            raise ValueError('Domain part of email was not valid')

    @staticmethod
    def punycode(domain: str):
        """Return the Punycode of the given domain if it's non-ASCII."""
        return domain.encode('idna').decode('ascii')