"""Unit tests for the trading account ledger."""
from __future__ import annotations

import unittest

from ledger import (
    InsufficientFundsError,
    InsufficientHoldingsError,
    InvalidTransactionError,
    TradingAccountLedger,
    UnsupportedSymbolError,
)
from prices import get_test_share_price


class LedgerTests(unittest.TestCase):
    def make_ledger(self) -> TradingAccountLedger:
        return TradingAccountLedger("acct-1", price_lookup=get_test_share_price)

    def test_new_ledger_starts_empty(self):
        ledger = self.make_ledger()
        self.assertEqual(ledger.get_cash_balance(), 0.0)
        self.assertEqual(ledger.get_holdings(), [])
        self.assertEqual(ledger.get_transaction_history(), [])
        self.assertEqual(ledger.get_portfolio_value(), 0.0)
        self.assertEqual(ledger.get_profit_loss(), 0.0)
        summary = ledger.get_summary()
        self.assertEqual(summary.account_id, "acct-1")
        self.assertEqual(summary.cash_balance, 0.0)
        self.assertEqual(summary.net_contributed_cash, 0.0)
        self.assertEqual(summary.holdings_market_value, 0.0)
        self.assertEqual(summary.total_account_value, 0.0)
        self.assertEqual(summary.profit_loss, 0.0)

    def test_deposit_records_transaction_and_rejects_nonpositive_amounts(self):
        ledger = self.make_ledger()
        tx = ledger.deposit(1000)
        self.assertEqual(ledger.get_cash_balance(), 1000)
        self.assertEqual(tx.tx_id, 1)
        self.assertEqual(tx.tx_type, "deposit")
        self.assertEqual(tx.cash_amount, 1000)
        self.assertEqual(tx.cash_balance_after, 1000)
        self.assertEqual(len(ledger.get_transaction_history()), 1)
        with self.assertRaises(InvalidTransactionError):
            ledger.deposit(0)
        with self.assertRaises(InvalidTransactionError):
            ledger.deposit(-1)
        self.assertEqual(ledger.get_cash_balance(), 1000)
        self.assertEqual(len(ledger.get_transaction_history()), 1)

    def test_withdrawal_updates_cash_and_rejects_invalid_or_oversized_amounts(self):
        ledger = self.make_ledger()
        ledger.deposit(500)
        tx = ledger.withdraw(200)
        self.assertEqual(ledger.get_cash_balance(), 300)
        self.assertEqual(tx.tx_type, "withdrawal")
        self.assertEqual(tx.cash_amount, -200)
        self.assertEqual(tx.cash_balance_after, 300)
        with self.assertRaises(InsufficientFundsError):
            ledger.withdraw(301)
        with self.assertRaises(InvalidTransactionError):
            ledger.withdraw(0)
        with self.assertRaises(InvalidTransactionError):
            ledger.withdraw(-1)
        self.assertEqual(ledger.get_cash_balance(), 300)
        self.assertEqual(len(ledger.get_transaction_history()), 2)

    def test_buy_shares_supports_case_insensitive_symbols_and_updates_summary(self):
        ledger = self.make_ledger()
        ledger.deposit(1000)
        tx = ledger.buy_shares("aapl", 2)
        self.assertEqual(tx.tx_type, "buy")
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(tx.quantity, 2)
        self.assertEqual(tx.unit_price, get_test_share_price("AAPL"))
        self.assertEqual(tx.cash_amount, -2 * get_test_share_price("AAPL"))
        self.assertEqual(ledger.get_holding_quantity("AAPL"), 2)
        self.assertEqual(ledger.get_holding_quantity("aapl"), 2)
        self.assertAlmostEqual(ledger.get_cash_balance(), 1000 - 2 * get_test_share_price("AAPL"))
        self.assertAlmostEqual(ledger.get_portfolio_value(), 1000)
        self.assertAlmostEqual(ledger.get_profit_loss(), 0.0)
        summary = ledger.get_summary()
        self.assertAlmostEqual(summary.cash_balance, 1000 - 2 * get_test_share_price("AAPL"))
        self.assertAlmostEqual(summary.holdings_market_value, 2 * get_test_share_price("AAPL"))
        self.assertAlmostEqual(summary.total_account_value, 1000)
        self.assertAlmostEqual(summary.net_contributed_cash, 1000)
        self.assertAlmostEqual(summary.profit_loss, 0.0)

    def test_buy_shares_rejects_unsupported_symbol_insufficient_cash_and_bad_quantity(self):
        ledger = self.make_ledger()
        ledger.deposit(1000)
        with self.assertRaises(UnsupportedSymbolError):
            ledger.buy_shares("MSFT", 1)
        with self.assertRaises(InsufficientFundsError):
            ledger.buy_shares("TSLA", 1000)
        with self.assertRaises(InvalidTransactionError):
            ledger.buy_shares("AAPL", 0)
        with self.assertRaises(InvalidTransactionError):
            ledger.buy_shares("AAPL", -3)
        self.assertEqual(ledger.get_cash_balance(), 1000)
        self.assertEqual(ledger.get_transaction_history()[-1].tx_type, "deposit")

    def test_sell_shares_reduces_or_removes_position_and_updates_cash(self):
        ledger = self.make_ledger()
        ledger.deposit(1000)
        ledger.buy_shares("AAPL", 2)
        tx = ledger.sell_shares("AAPL", 1)
        self.assertEqual(tx.tx_type, "sell")
        self.assertEqual(tx.symbol, "AAPL")
        self.assertEqual(tx.quantity, 1)
        self.assertEqual(ledger.get_holding_quantity("AAPL"), 1)
        self.assertAlmostEqual(
            ledger.get_cash_balance(),
            1000 - get_test_share_price("AAPL")
        )
        tx2 = ledger.sell_shares("AAPL", 1)
        self.assertEqual(tx2.quantity, 1)
        self.assertEqual(ledger.get_holding_quantity("AAPL"), 0)
        self.assertEqual(ledger.get_holdings(), [])
        self.assertAlmostEqual(ledger.get_cash_balance(), 1000)
        self.assertAlmostEqual(ledger.get_profit_loss(), 0.0)

    def test_sell_shares_rejects_unsupported_symbol_oversell_and_bad_quantity(self):
        ledger = self.make_ledger()
        ledger.deposit(1000)
        ledger.buy_shares("AAPL", 1)
        with self.assertRaises(UnsupportedSymbolError):
            ledger.sell_shares("MSFT", 1)
        with self.assertRaises(InsufficientHoldingsError):
            ledger.sell_shares("AAPL", 2)
        with self.assertRaises(InvalidTransactionError):
            ledger.sell_shares("AAPL", 0)
        with self.assertRaises(InvalidTransactionError):
            ledger.sell_shares("AAPL", -1)
        self.assertEqual(ledger.get_holding_quantity("AAPL"), 1)

    def test_transaction_history_is_chronological_and_cash_balance_after_is_correct(self):
        ledger = self.make_ledger()
        ledger.deposit(1000)
        ledger.withdraw(100)
        ledger.buy_shares("AAPL", 1)
        ledger.sell_shares("AAPL", 1)
        history = ledger.get_transaction_history()
        self.assertEqual([tx.tx_id for tx in history], [1, 2, 3, 4])
        self.assertEqual([tx.tx_type for tx in history], ["deposit", "withdrawal", "buy", "sell"])
        self.assertEqual([tx.cash_balance_after for tx in history], [1000, 900, 900 - get_test_share_price("AAPL"), 900])
        self.assertEqual(history[-1].cash_balance_after, ledger.get_cash_balance())

    def test_get_holdings_returns_sorted_market_valued_records(self):
        ledger = self.make_ledger()
        ledger.deposit(5000)
        ledger.buy_shares("TSLA", 1)
        ledger.buy_shares("AAPL", 2)
        holdings = ledger.get_holdings()
        self.assertEqual([h.symbol for h in holdings], ["AAPL", "TSLA"])
        self.assertEqual(holdings[0].quantity, 2)
        self.assertEqual(holdings[0].current_price, get_test_share_price("AAPL"))
        self.assertEqual(holdings[0].market_value, 2 * get_test_share_price("AAPL"))
        self.assertEqual(holdings[1].quantity, 1)
        self.assertEqual(holdings[1].current_price, get_test_share_price("TSLA"))
        self.assertEqual(holdings[1].market_value, get_test_share_price("TSLA"))

    def test_profit_loss_accounts_for_withdrawals(self):
        ledger = self.make_ledger()
        ledger.deposit(1000)
        ledger.withdraw(250)
        self.assertAlmostEqual(ledger.get_profit_loss(), 0.0)
        summary = ledger.get_summary()
        self.assertAlmostEqual(summary.net_contributed_cash, 750)
        self.assertAlmostEqual(summary.total_account_value, 750)
        self.assertAlmostEqual(summary.profit_loss, 0.0)

    def test_validate_symbol_rejects_unknown_symbol(self):
        ledger = self.make_ledger()
        with self.assertRaises(UnsupportedSymbolError):
            ledger.validate_symbol("MSFT")


if __name__ == "__main__":
    unittest.main()