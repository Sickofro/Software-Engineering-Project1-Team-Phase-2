import re
from urllib.parse import unquote

def canonicalize_name(name: str) -> str:
    """
    Canonicalize artifact names for consistent storage and lookup.
    Steps:
    - Decode percent-encoding once
    - Trim whitespace
    - Collapse consecutive slashes
    - Remove trailing slash (unless name is exactly '/')
    - Lowercase (for case-insensitive matching)
    """
    if not isinstance(name, str):
        return ""
    # Decode percent-encoding
    name = unquote(name)
    # Trim whitespace
    name = name.strip()
    # Collapse consecutive slashes
    name = re.sub(r'/+', '/', name)
    # Remove trailing slash (unless name is exactly '/')
    if name != '/' and name.endswith('/'):
        name = name[:-1]
    # Lowercase
    name = name.lower()
    return name
