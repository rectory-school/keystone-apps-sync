"""Parsers for managers"""

import logging
from typing import Any

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

log = logging.getLogger(__name__)

def active_parse(val: str) -> bool:
    if val == "":
        return False

    if val == "0":
        return True

    if val == "1":
        return True

    log.warning("Unknown value '%s' when parsing acive field, assuming false", val)
    return False

def email_parse_continue_blank(val: str) -> str:
    """Validate an email and return None if it isn't valid"""

    if not val:
        return ''

    try:
        validate_email(val)
        return val
    except ValidationError as exc:
        for error in exc.error_list:
            log.warning("Unable to parse '%s' as email", val)
        return ''

def email_parse_fail(val: str) -> str:
    """Validate an email and except if it isn't valid"""

    validate_email(val)
    return val

def is_boarder_from_boarder_day(val: str) -> bool:
    if val == 'B':
        return True
    
    if val == 'D':
        return False

    log.warn("Unknown boarder/day value: %s", val)
    return None