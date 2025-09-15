import base64
import hashlib
import ipaddress
import socket
from typing import Dict, Optional
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt


def _derive_fernet_key(secret: str) -> bytes:
    # Create a Fernet-compatible key from arbitrary secret string
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_cipher(secret: Optional[str]) -> Optional[Fernet]:
    if not secret:
        return None
    try:
        key = _derive_fernet_key(secret)
        return Fernet(key)
    except (ValueError, TypeError):
        return None


def encrypt_text(plain: str, secret: Optional[str]) -> str:
    cipher = get_cipher(secret)
    if not cipher:
        return plain
    token: bytes = cipher.encrypt(plain.encode("utf-8"))
    out: str = "enc:" + token.decode("utf-8")
    return out


def decrypt_text(value: str, secret: Optional[str]) -> str:
    if not value or not value.startswith("enc:"):
        return value
    token: str = value[4:]
    cipher = get_cipher(secret)
    if not cipher:
        return value
    try:
        plain_bytes: bytes = cipher.decrypt(token.encode("utf-8"))
        decoded: str = plain_bytes.decode("utf-8")
        return decoded
    except (InvalidToken, ValueError, TypeError):
        return value


def is_url_allowed(url: str) -> bool:
    """Basic SSRF guard: only http(s) and non-private hosts."""
    try:
        p = urlparse(url)
        if p.scheme not in {"http", "https"}:
            return False
        hostname = p.hostname or ""
        if hostname.lower() in {"localhost", "127.0.0.1"}:
            return False
        # Resolve and ensure all addresses are public
        addrs = {ai[4][0] for ai in socket.getaddrinfo(hostname, None)}
        for ip in addrs:
            ipobj = ipaddress.ip_address(ip)
            if ipobj.is_private or ipobj.is_loopback or ipobj.is_link_local:
                return False
        return True
    except Exception:
        return False


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    token = credentials.credentials
    try:
        import os

        secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
