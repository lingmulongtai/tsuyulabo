from __future__ import annotations

from ipaddress import ip_address

from fastapi import Request


def extract_client_ip(peer: str, forwarded: str | None, hops: int) -> str:
    """Select from the right; insufficient or malformed chains fall back to the socket peer."""
    if hops <= 0 or not forwarded or len(forwarded) > 2048:
        return peer
    chain = forwarded.split(",")
    if len(chain) < hops or len(chain) > 32:
        return peer
    try:
        addresses = [str(ip_address(part.strip())) for part in chain]
    except ValueError:
        return peer
    return addresses[-hops]


def client_ip(request: Request) -> str:
    return extract_client_ip(
        request.client.host if request.client else "unknown",
        request.headers.get("x-forwarded-for"),
        request.app.state.settings.trusted_proxy_hops,
    )
