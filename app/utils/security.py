import bcrypt
import re

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: The password to hash

    Returns:
        The hashed password as a string
    """
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash

    Args:
        plain_password: The plaintext password to check
        hashed_password: The hash to check against

    Returns:
        True if the password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def validate_email(email: str) -> bool:
    """
    Validate email format using regex

    Args:
        email: The email to validate

    Returns:
        True if the email format is valid, False otherwise
    """
    # Simple email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password_complexity(password: str) -> dict:
    """
    Validate password complexity

    Password must:
    - Be at least 8 characters long
    - Contain at least one uppercase letter
    - Contain at least one number

    Args:
        password: The password to validate

    Returns:
        Dict with validation result and message
    """
    errors = []

    # Check password length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    # Check for uppercase
    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter")

    # Check for digit
    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one number")

    if errors:
        return {"valid": False, "errors": errors}

    return {"valid": True, "errors": []}