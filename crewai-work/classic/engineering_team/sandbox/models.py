"""Domain models for the trading simulation platform."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TransactionRecord:
    tx_id: int
    account_id: str
    tx_type: str
    symbol: str | None
    quantity: int | None
    unit_price: float | None
    cash_amount: float
    timestamp: str
    cash_balance_after: float


@dataclass(frozen=True)
class HoldingRecord:
    symbol: str
    quantity: int
    current_price: float
    market_value: float


@dataclass(frozen=True)
class AccountSummary:
    account_id: str
    cash_balance: float
    net_contributed_cash: float
    holdings_market_value: float
    total_account_value: float
    profit_loss: float


@dataclass
class AccountState:
    account_id: str
    cash_balance: float = 0.0
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    holdings: dict[str, int] = field(default_factory=dict)
    transactions: list[TransactionRecord] = field(default_factory=list)
    next_tx_id: int = 1
