"""Strict, dependency-free validation helpers for untrusted evidence payloads."""
from __future__ import annotations
import ipaddress, math, re
from urllib.parse import unquote, urlsplit
_HEX = re.compile(r"[0-9a-fA-F]{2}\Z")
_DNS_LABEL = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\Z")

def validate_primitive(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value): raise ValueError("Non-finite floating-point values are not allowed.")
    if isinstance(value, (bytes, bytearray, memoryview)): raise ValueError("Binary values are not supported.")
def _validate_percent_encoding(path: str) -> None:
    for i, char in enumerate(path):
        if char == "%" and (i + 2 >= len(path) or not _HEX.fullmatch(path[i + 1:i + 3])): raise ValueError("Malformed percent-encoding in URL path.")
    current = path
    for _ in range(5):
        try: decoded = unquote(current, errors="strict")
        except (UnicodeError, ValueError) as exc: raise ValueError("Malformed percent-encoding in URL path.") from exc
        if any(segment in {".", ".."} for segment in decoded.split("/")): raise ValueError("URL path contains traversal segments.")
        if decoded == current: return
        current = decoded
    raise ValueError("URL path contains excessively nested percent-encoding.")
def _validate_host(host: str) -> None:
    if host.endswith("."): host = host[:-1]
    if not host: raise ValueError("URL host is empty.")
    try: ipaddress.ip_address(host); return
    except ValueError: pass
    if re.fullmatch(r"(?:0x[0-9a-f]+|[0-9]+|[0-7]+)(?:\.(?:0x[0-9a-f]+|[0-9]+|[0-7]+))*", host, re.I): raise ValueError("Non-canonical numeric IP address is not allowed.")
    try: ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc: raise ValueError("Invalid internationalized hostname.") from exc
    if len(ascii_host) > 253 or any(not _DNS_LABEL.fullmatch(x) for x in ascii_host.split(".")): raise ValueError("Invalid DNS hostname.")
def validate_url(value: str, *, allowed_schemes: tuple[str, ...] = ("http", "https")) -> str:
    """Validate an absolute URL without fetching it; return the original value."""
    if not isinstance(value, str) or not value or len(value) > 8192: raise ValueError("URL must be a non-empty string of at most 8192 characters.")
    if any(ord(c) < 0x20 or ord(c) == 0x7f for c in value): raise ValueError("Control characters are not allowed in URLs.")
    try: parts = urlsplit(value); port = parts.port
    except ValueError as exc: raise ValueError("Malformed URL authority or port.") from exc
    if parts.scheme.lower() not in allowed_schemes: raise ValueError("URL scheme is not allowed.")
    if not parts.netloc or not parts.hostname or parts.username is not None or parts.password is not None: raise ValueError("URL must have a host and must not contain user information.")
    if port is not None and not 1 <= port <= 65535: raise ValueError("URL port is outside the valid range.")
    _validate_host(parts.hostname); _validate_percent_encoding(parts.path)
    return value
