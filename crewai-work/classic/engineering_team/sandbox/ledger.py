"""Core account ledger for the trading simulation platform."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from models import AccountState, AccountSummary, HoldingRecord, TransactionRecord
from prices import get_share_price


class InsufficientFundsError(Exception):
    pass


class InsufficientHoldingsError(Exception):
    pass


class InvalidTransactionError(Exception):
    pass


class UnsupportedSymbolError(Exception):
    pass


class TradingAccountLedger:
    def __init__(self, account_id: str, price_lookup: Callable[[str], float] = get_share_price) -> None:
        self._state = AccountState(account_id=account_id)
        self._price_lookup = price_lookup

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _get_current_price(self, symbol: str) -> float:
        try:
            price = float(self._price_lookup(symbol))
        except Exception as exc:
            raise UnsupportedSymbolError(f"Unsupported symbol: {symbol!r}") from exc
        if price <= 0:
            raise UnsupportedSymbolError(f"Unsupported symbol: {symbol!r}")
        return price

    def validate_symbol(self, symbol: str) -> None:
        self._get_current_price(symbol)

    @staticmethod
    def validate_quantity(quantity: int) -> None:
        if not isinstance(quantity, int) or quantity <= 0:
            raise InvalidTransactionError("Quantity must be a positive integer")

    def _record_transaction(self, tx_type: str, cash_amount: float, symbol: str | None = None, quantity: int | None = None, unit_price: float | None = None) -> TransactionRecord:
        tx = TransactionRecord(self._state.next_tx_id, self._state.account_id, tx_type, symbol, quantity, unit_price, cash_amount, self._now(), self._state.cash_balance)
        self._state.transactions.append(tx)
        self._state.next_tx_id += 1
        return tx

    def deposit(self, amount: float) -> TransactionRecord:
        if amount <= 0:
            raise InvalidTransactionError("Deposit amount must be positive")
        self._state.cash_balance += amount
        self._state.total_deposits += amount
        return self._record_transaction("deposit", cash_amount=amount)

    def withdraw(self, amount: float) -> TransactionRecord:
        if amount <= 0:
            raise InvalidTransactionError("Withdrawal amount must be positive")
        if amount > self._state.cash_balance:
            raise InsufficientFundsError("Insufficient cash balance")
        self._state.cash_balance -= amount
        self._state.total_withdrawals += amount
        return self._record_transaction("withdrawal", cash_amount=-amount)

    def buy_shares(self, symbol: str, quantity: int) -> TransactionRecord:
        self.validate_symbol(symbol)
        self.validate_quantity(quantity)
        symbol = symbol.upper()
        price = self._get_current_price(symbol)
        cost = price * quantity
        if cost > self._state.cash_balance:
            raise InsufficientFundsError("Insufficient cash to buy shares")
        self._state.cash_balance -= cost
        self._state.holdings[symbol] = self._state.holdings.get(symbol, 0) + quantity
        return self._record_transaction("buy", cash_amount=-cost, symbol=symbol, quantity=quantity, unit_price=price)

    def sell_shares(self, symbol: str, quantity: int) -> TransactionRecord:
        self.validate_symbol(symbol)
        self.validate_quantity(quantity)
        symbol = symbol.upper()
        owned = self._state.holdings.get(symbol, 0)
        if quantity > owned:
            raise InsufficientHoldingsError("Insufficient shares to sell")
        price = self._get_current_price(symbol)
        proceeds = price * quantity
        self._state.cash_balance += proceeds
        new_qty = owned - quantity
        if new_qty:
            self._state.holdings[symbol] = new_qty
        else:
            self._state.holdings.pop(symbol, None)
        return self._record_transaction("sell", cash_amount=proceeds, symbol=symbol, quantity=quantity, unit_price=price)

    def _current_holding_value(self) -> float:
        return sum(self._get_current_price(symbol) * quantity for symbol, quantity in self._state.holdings.items())

    def get_holdings(self) -> list[HoldingRecord]:
        return [HoldingRecord(symbol=symbol, quantity=quantity, current_price=(price := self._get_current_price(symbol)), market_value=price * quantity) for symbol, quantity in sorted(self._state.holdings.items())]

    def get_transaction_history(self) -> list[TransactionRecord]:
        return list(self._state.transactions)

    def get_portfolio_value(self) -> float:
        return self._state.cash_balance + self._current_holding_value()

    def get_profit_loss(self) -> float:
        net_contributed_cash = self._state.total_deposits - self._state.total_withdrawals
        return self.get_portfolio_value() - net_contributed_cash

    def get_summary(self) -> AccountSummary:
        holdings_market_value = self._current_holding_value()
        net_contributed_cash = self._state.total_deposits - self._state.total_withdrawals
        total_account_value = self._state.cash_balance + holdings_market_value
        return AccountSummary(self._state.account_id, self._state.cash_balance, net_contributed_cash, holdings_market_value, total_account_value, total_account_value - net_contributed_cash)

    def get_cash_balance(self) -> float:
        return self._state.cash_balance

    def get_holding_quantity(self, symbol: str) -> int:
        return self._state.holdings.get(symbol.upper(), 0)


def create_ledger(account_id: str, price_lookup: Callable[[str], float] = get_share_price) -> TradingAccountLedger:
    return TradingAccountLedger(account_id=account_id, price_lookup=price_lookup)


def ledger_from_seed(account_id: str, initial_deposit: float, price_lookup: Callable[[str], float] = get_share_price) -> TradingAccountLedger:
    ledger = TradingAccountLedger(account_id=account_id, price_lookup=price_lookup)
    ledger.deposit(initial_deposit)
    return ledger
