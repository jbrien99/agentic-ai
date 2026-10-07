"""Price lookup utilities for the trading simulation platform."""
from __future__ import annotations

from typing import Final

_TEST_PRICES: Final[dict[str, float]] = {
    "AAPL": 175.25,
    "TSLA": 242.18,
    "GOOGL": 138.64,
}


def get_test_share_price(symbol: str) -> float:
    """Return a fixed test price for supported symbols."""
    try:
        return _TEST_PRICES[symbol.upper()]
    except KeyError as exc:
        raise LookupError(f"Unsupported symbol: {symbol!r}") from exc


def get_share_price(symbol: str) -> float:
    """Production price lookup placeholder.

    In this sandboxed implementation we use the deterministic test prices.
    """
    return get_test_share_price(symbol)


def is_supported_symbol(symbol: str) -> bool:
    """Return True if the symbol has an available price."""
    try:
        get_test_share_price(symbol)
        return True
    except LookupError:
        return False
