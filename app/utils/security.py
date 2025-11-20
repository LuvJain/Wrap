import re
import logging
from typing import Any, Dict, List, Union

def mask_sensitive_data(data: Union[Dict, str],
                        sensitive_keys: List[str] = None) -> Union[Dict, str]:
    """
    Mask sensitive data in logs and error messages.

    Args:
        data: Dictionary or string containing potentially sensitive data
        sensitive_keys: List of keys to mask (defaults to common sensitive keys)

    Returns:
        Masked data with sensitive information replaced by asterisks
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'key', 'secret', 'password', 'token', 'auth',
            'credential', 'api_key', 'private', 'secret_key'
        ]

    # For string data
    if isinstance(data, str):
        # Mask common patterns like API keys and tokens
        masked = data
        # Mask Stripe secret keys pattern
        masked = re.sub(r'(sk_(?:test|live)_[0-9a-zA-Z]{24})[0-9a-zA-Z]+', r'\1***', masked)
        # Mask Stripe publishable keys pattern
        masked = re.sub(r'(pk_(?:test|live)_[0-9a-zA-Z]{24})[0-9a-zA-Z]+', r'\1***', masked)
        # Mask webhook secrets
        masked = re.sub(r'(whsec_[0-9a-zA-Z]{24})[0-9a-zA-Z]+', r'\1***', masked)
        return masked

    # For dictionary data
    if isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            # Check if key contains any sensitive keyword
            is_sensitive = any(sensitive_word in key.lower() for sensitive_word in sensitive_keys)

            if is_sensitive and isinstance(value, str):
                # Mask the value if it's a string and key is sensitive
                if len(value) > 8:
                    masked_data[key] = value[:4] + '****' + value[-4:]
                else:
                    masked_data[key] = '********'
            elif isinstance(value, dict):
                # Recursively mask nested dictionaries
                masked_data[key] = mask_sensitive_data(value, sensitive_keys)
            else:
                masked_data[key] = value

        return masked_data

    # Return as-is if not a string or dict
    return data


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter to mask sensitive data in log records.
    """
    def __init__(self, sensitive_keys: List[str] = None):
        super().__init__()
        self.sensitive_keys = sensitive_keys or [
            'key', 'secret', 'password', 'token', 'auth',
            'credential', 'api_key', 'private', 'secret_key'
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = mask_sensitive_data(record.msg, self.sensitive_keys)

        if hasattr(record, 'args') and record.args:
            args = list(record.args)
            for i, arg in enumerate(args):
                if isinstance(arg, (str, dict)):
                    args[i] = mask_sensitive_data(arg, self.sensitive_keys)
            record.args = tuple(args)

        return True


def setup_secure_logging():
    """
    Configure logging to filter sensitive data.
    """
    # Get the root logger
    root_logger = logging.getLogger()

    # Add our filter to all handlers
    for handler in root_logger.handlers:
        handler.addFilter(SensitiveDataFilter())

    # Set the logging level if not already set
    if root_logger.level == logging.NOTSET:
        root_logger.setLevel(logging.INFO)

    # If no handlers exist, add a console handler
    if not root_logger.handlers:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        console.addFilter(SensitiveDataFilter())
        root_logger.addHandler(console)

    logging.info("Secure logging configured with sensitive data filtering")