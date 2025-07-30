"""Dummy country service for testing."""

def get_country_info_by_code(code: str) -> dict:
    """Returns dummy country info."""
    return {'name': 'Test Country', 'capital': 'Test Capital'}

def get_country_info_by_name(name: str) -> dict:
    """Returns dummy country info."""
    return {'name': name, 'capital': 'Test Capital'}
