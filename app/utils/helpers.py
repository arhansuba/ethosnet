import re
from typing import List, Dict, Any, Union
from datetime import datetime, timezone
import hashlib
import json
from eth_utils import is_address, to_checksum_address

def sanitize_text(text: str) -> str:
    """
    Sanitize input text by removing special characters and excessive whitespace.
    
    Args:
        text (str): The input text to sanitize.
    
    Returns:
        str: The sanitized text.
    """
    # Remove special characters except basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()

def validate_ethereum_address(address: str) -> bool:
    """
    Validate an Ethereum address.
    
    Args:
        address (str): The Ethereum address to validate.
    
    Returns:
        bool: True if the address is valid, False otherwise.
    """
    return is_address(address)

def normalize_ethereum_address(address: str) -> str:
    """
    Normalize an Ethereum address to its checksum version.
    
    Args:
        address (str): The Ethereum address to normalize.
    
    Returns:
        str: The normalized (checksum) Ethereum address.
    """
    if not is_address(address):
        raise ValueError("Invalid Ethereum address")
    return to_checksum_address(address)

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a specified maximum length.
    
    Args:
        text (str): The input text to truncate.
        max_length (int): The maximum length of the truncated text.
    
    Returns:
        str: The truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def generate_content_hash(content: Union[str, Dict, List]) -> str:
    """
    Generate a hash of the content for integrity checks.
    
    Args:
        content (Union[str, Dict, List]): The content to hash.
    
    Returns:
        str: The generated hash.
    """
    if isinstance(content, (dict, list)):
        content = json.dumps(content, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()

def is_valid_json(json_string: str) -> bool:
    """
    Check if a string is valid JSON.
    
    Args:
        json_string (str): The string to check.
    
    Returns:
        bool: True if the string is valid JSON, False otherwise.
    """
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError:
        return False

def format_timestamp(timestamp: Union[int, float, str, datetime]) -> str:
    """
    Format a timestamp to ISO 8601 format.
    
    Args:
        timestamp (Union[int, float, str, datetime]): The timestamp to format.
    
    Returns:
        str: The formatted timestamp.
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    elif isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp.rstrip('Z')).replace(tzinfo=timezone.utc)
    elif isinstance(timestamp, datetime):
        dt = timestamp.replace(tzinfo=timezone.utc)
    else:
        raise ValueError("Unsupported timestamp format")
    return dt.isoformat()

def parse_timestamp(timestamp: str) -> datetime:
    """
    Parse an ISO 8601 formatted timestamp.
    
    Args:
        timestamp (str): The timestamp string to parse.
    
    Returns:
        datetime: The parsed datetime object.
    """
    return datetime.fromisoformat(timestamp.rstrip('Z')).replace(tzinfo=timezone.utc)

def calculate_percentage(part: Union[int, float], whole: Union[int, float]) -> float:
    """
    Calculate the percentage of a part relative to a whole.
    
    Args:
        part (Union[int, float]): The part value.
        whole (Union[int, float]): The whole value.
    
    Returns:
        float: The calculated percentage.
    """
    if whole == 0:
        return 0.0
    return (part / whole) * 100

def validate_url(url: str) -> bool:
    """
    Validate a URL.
    
    Args:
        url (str): The URL to validate.
    
    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        d (Dict[str, Any]): The dictionary to flatten.
        parent_key (str): The parent key for nested dictionaries.
        sep (str): The separator to use between keys.
    
    Returns:
        Dict[str, Any]: The flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split a long text into overlapping chunks.
    
    Args:
        text (str): The text to split.
        chunk_size (int): The size of each chunk.
        overlap (int): The number of characters to overlap between chunks.
    
    Returns:
        List[str]: A list of text chunks.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    
    Args:
        s1 (str): The first string.
        s2 (str): The second string.
    
    Returns:
        int: The Levenshtein distance.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def is_valid_ipfs_cid(cid: str) -> bool:
    """
    Validate an IPFS Content Identifier (CID).
    
    Args:
        cid (str): The CID to validate.
    
    Returns:
        bool: True if the CID is valid, False otherwise.
    """
    # This is a basic check and might need to be updated as IPFS evolves
    cid_regex = r'^(Qm[1-9A-HJ-NP-Za-km-z]{44}|b[A-Za-z2-7]{58}|B[A-Z2-7]{58}|z[1-9A-HJ-NP-Za-km-z]{48}|F[0-9A-F]{50})$'
    return re.match(cid_regex, cid) is not None