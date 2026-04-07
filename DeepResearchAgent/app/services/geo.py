from __future__ import annotations

import ipaddress
from typing import Optional

import httpx

from app.config import settings


def _is_public_ip(value: str | None) -> bool:
    if not value:
        return False
    try:
        ip = ipaddress.ip_address(value)
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def _lookup_location_from_ip(ip_address: str | None = None) -> str | None:
    endpoint = f"http://ip-api.com/json/{ip_address}" if ip_address else "http://ip-api.com/json"
    with httpx.Client(timeout=3.0) as client:
        resp = client.get(endpoint)
        if resp.status_code != 200:
            return None
        data = resp.json()
        city = data.get("city")
        country = data.get("country")
        if city and country:
            return f"{city}, {country}"
    return None


def infer_location(explicit_location: Optional[str], ip_address: Optional[str]) -> str:
    if explicit_location:
        return explicit_location

    # Prefer request IP if it is routable public IP.
    if _is_public_ip(ip_address):
        try:
            location = _lookup_location_from_ip(ip_address)
            if location:
                return location
        except Exception:
            pass

    # Local/dev mode usually gives 127.0.0.1; then infer from host machine public egress IP.
    try:
        auto_location = _lookup_location_from_ip(None)
        if auto_location:
            return auto_location
    except Exception:
        pass

    return settings.default_location
