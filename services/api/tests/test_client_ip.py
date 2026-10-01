from __future__ import annotations

import pytest
from tsuyulabo_api.services.client_ip import extract_client_ip


@pytest.mark.parametrize(
    ("forwarded", "hops", "expected"),
    [
        ("192.0.2.1, 192.0.2.2", 0, "172.18.0.1"),
        ("192.0.2.1, 192.0.2.2", 1, "192.0.2.2"),
        ("192.0.2.1, 192.0.2.2", 2, "192.0.2.1"),
        ("192.0.2.1", 2, "172.18.0.1"),
        (None, 1, "172.18.0.1"),
        ("", 1, "172.18.0.1"),
        ("unknown, 192.0.2.1", 1, "172.18.0.1"),
        ("192.0.2.1:1234", 1, "172.18.0.1"),
        ("192.0.2.1,", 1, "172.18.0.1"),
        ("2001:db8::1", 1, "2001:db8::1"),
        ("192.0.2.1," * 40, 1, "172.18.0.1"),
        (" " * 2049, 1, "172.18.0.1"),
    ],
)
def test_client_ip(forwarded: str | None, hops: int, expected: str) -> None:
    assert extract_client_ip("172.18.0.1", forwarded, hops) == expected
