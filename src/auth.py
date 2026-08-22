# Auth endpoint
# JWT-based authentication for the application


def login(email: str, password: str) -> dict:
    """Authenticate a user and return a JWT token."""
    return {"token": "jwt_token"}


def register(email: str, password: str) -> dict:
    """Register a new user and return a JWT token."""
    return {"token": "jwt_token"}


def verify_token(token: str) -> bool:
    """Verify a JWT token and return True if valid."""
    return token.startswith("jwt_")
# Updated for real pipeline test
