"""Gradio UI for the trading simulation account manager."""
from __future__ import annotations

import gradio as gr

from ledger import TradingAccountLedger

PALETTE = {
    "gold": "#ecad0a",
    "blue": "#209dd7",
    "purple": "#753991",
    "bg_light": "#f7f8fb",
    "bg_dark": "#0f1117",
    "panel_light": "#ffffff",
    "panel_dark": "#171a21",
    "text_light": "#1f2937",
    "text_dark": "#e5e7eb",
    "muted_light": "#6b7280",
    "muted_dark": "#9ca3af",
}

CSS = """
#app-shell { max-width: 1200px; margin: 0 auto; }
#hero {
    border-radius: 24px;
    padding: 24px 28px;
    background: linear-gradient(135deg, rgba(32,157,215,0.14), rgba(117,57,145,0.10));
    border: 1px solid rgba(32,157,215,0.18);
    margin-bottom: 16px;
}
#hero h1 { margin-bottom: 0.35rem; }
#hero p { margin: 0; color: var(--body-text-color); opacity: 0.85; }
.panel {
    border-radius: 20px;
    border: 1px solid rgba(128,128,128,0.18);
    background: var(--block-background-fill);
    box-shadow: 0 6px 24px rgba(0,0,0,0.06);
    padding: 18px;
}
.panel h3 { margin-top: 0; }
.small-note { color: var(--body-text-color); opacity: 0.72; font-size: 0.95rem; }
.gr-button {
    border-radius: 999px !important;
    font-weight: 600 !important;
}
#status { font-size: 1rem; }
"""


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def format_summary(summary) -> dict:
    return {
        "account_id": summary.account_id,
        "cash_balance": round(summary.cash_balance, 2),
        "net_contributed_cash": round(summary.net_contributed_cash, 2),
        "holdings_market_value": round(summary.holdings_market_value, 2),
        "total_account_value": round(summary.total_account_value, 2),
        "profit_loss": round(summary.profit_loss, 2),
    }


def format_holdings(holdings) -> list[dict]:
    return [
        {
            "symbol": h.symbol,
            "quantity": h.quantity,
            "current_price": round(h.current_price, 2),
            "market_value": round(h.market_value, 2),
        }
        for h in holdings
    ]


def format_transactions(transactions) -> list[dict]:
    return [
        {
            "tx_id": t.tx_id,
            "account_id": t.account_id,
            "tx_type": t.tx_type,
            "symbol": t.symbol,
            "quantity": t.quantity,
            "unit_price": None if t.unit_price is None else round(t.unit_price, 2),
            "cash_amount": round(t.cash_amount, 2),
            "timestamp": t.timestamp,
            "cash_balance_after": round(t.cash_balance_after, 2),
        }
        for t in transactions
    ]


def _empty_views():
    return {}, [], []


def _render_views(ledger):
    if ledger is None:
        return {}, [], []
    return (
        format_summary(ledger.get_summary()),
        format_holdings(ledger.get_holdings()),
        format_transactions(ledger.get_transaction_history()),
    )


def _status_text(kind: str, message: str) -> str:
    return f"### {kind}\n{message}"


def create_account_handler(account_id: str, initial_deposit: float | None):
    ledger = TradingAccountLedger(account_id or "account-1")
    status = f"Created account **{ledger.get_summary().account_id}**."
    if initial_deposit is not None and float(initial_deposit) != 0.0:
        ledger.deposit(float(initial_deposit))
        status = (
            f"Created account **{ledger.get_summary().account_id}** with an initial deposit of "
            f"**{_format_money(float(initial_deposit))}**."
        )
    summary, holdings, transactions = _render_views(ledger)
    return ledger, summary, holdings, transactions, _status_text("Account ready", status)


def deposit_handler(ledger, amount: float):
    tx = ledger.deposit(float(amount))
    summary, holdings, transactions = _render_views(ledger)
    return ledger, summary, holdings, transactions, _status_text("Deposit complete", f"Added **{_format_money(tx.cash_amount)}** cash.")


def withdraw_handler(ledger, amount: float):
    tx = ledger.withdraw(float(amount))
    summary, holdings, transactions = _render_views(ledger)
    return ledger, summary, holdings, transactions, _status_text("Withdrawal complete", f"Removed **{_format_money(abs(tx.cash_amount))}** cash.")


def buy_handler(ledger, symbol: str, quantity: int):
    tx = ledger.buy_shares(symbol, int(quantity))
    summary, holdings, transactions = _render_views(ledger)
    return ledger, summary, holdings, transactions, _status_text("Trade complete", f"Bought **{tx.quantity} {tx.symbol}** shares at **{_format_money(tx.unit_price or 0.0)}** each.")


def sell_handler(ledger, symbol: str, quantity: int):
    tx = ledger.sell_shares(symbol, int(quantity))
    summary, holdings, transactions = _render_views(ledger)
    return ledger, summary, holdings, transactions, _status_text("Trade complete", f"Sold **{tx.quantity} {tx.symbol}** shares at **{_format_money(tx.unit_price or 0.0)}** each.")


def refresh_handler(ledger):
    summary, holdings, transactions = _render_views(ledger)
    message = "Refreshed current portfolio snapshot."
    return ledger, summary, holdings, transactions, _status_text("Snapshot updated", message)


def build_app() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown(
            """
            <div id="hero">
              <h1>Trading Simulation Account Manager</h1>
              <p>Manage one simulated trading account with deposits, withdrawals, buys, sells, holdings, and full transaction history.</p>
            </div>
            """
        )

        ledger_state = gr.State(None)

        with gr.Row(elem_classes=["panel"]):
            with gr.Column(scale=1):
                gr.Markdown("### Create account")
                gr.Markdown("<div class='small-note'>Start with a clean account or seed it with an opening deposit.</div>")
                account_id = gr.Textbox(label="Account ID", value="demo-account", placeholder="Enter an account id")
                initial_deposit = gr.Number(label="Initial deposit", value=0.0, precision=2)
                create_btn = gr.Button("Create account", variant="primary")
            with gr.Column(scale=1):
                gr.Markdown("### Cash actions")
                deposit_amount = gr.Number(label="Deposit amount", precision=2, placeholder="1000")
                withdraw_amount = gr.Number(label="Withdrawal amount", precision=2, placeholder="250")
                with gr.Row():
                    deposit_btn = gr.Button("Deposit", variant="primary")
                    withdraw_btn = gr.Button("Withdraw")

        with gr.Row():
            with gr.Column(elem_classes=["panel"]):
                gr.Markdown("### Trading")
                symbol = gr.Textbox(label="Symbol", value="AAPL", placeholder="AAPL")
                quantity = gr.Number(label="Quantity", value=1, precision=0)
                with gr.Row():
                    buy_btn = gr.Button("Buy shares", variant="primary")
                    sell_btn = gr.Button("Sell shares")
            with gr.Column(elem_classes=["panel"]):
                gr.Markdown("### Snapshot")
                gr.Markdown("<div class='small-note'>Refresh anytime to review current cash, holdings, and P/L.</div>")
                refresh_btn = gr.Button("Refresh snapshot")
                status = gr.Markdown(value="### Ready\nCreate an account to begin.", elem_id="status")

        with gr.Row():
            summary_out = gr.JSON(label="Summary")
            holdings_out = gr.JSON(label="Holdings")
        transactions_out = gr.Dataframe(
            label="Transactions",
            headers=["tx_id", "account_id", "tx_type", "symbol", "quantity", "unit_price", "cash_amount", "timestamp", "cash_balance_after"],
            datatype=["number", "str", "str", "str", "number", "number", "number", "str", "number"],
            interactive=False,
            wrap=True,
            show_row_numbers=False,
            elem_classes=["panel"],
        )

        def _tx_rows(data):
            return [
                [
                    row["tx_id"],
                    row["account_id"],
                    row["tx_type"],
                    row["symbol"],
                    row["quantity"],
                    row["unit_price"],
                    row["cash_amount"],
                    row["timestamp"],
                    row["cash_balance_after"],
                ]
                for row in data
            ]

        create_btn.click(
            create_account_handler,
            inputs=[account_id, initial_deposit],
            outputs=[ledger_state, summary_out, holdings_out, transactions_out, status],
        ).then(lambda rows: rows, inputs=transactions_out, outputs=transactions_out)
        deposit_btn.click(
            deposit_handler,
            inputs=[ledger_state, deposit_amount],
            outputs=[ledger_state, summary_out, holdings_out, transactions_out, status],
        )
        withdraw_btn.click(
            withdraw_handler,
            inputs=[ledger_state, withdraw_amount],
            outputs=[ledger_state, summary_out, holdings_out, transactions_out, status],
        )
        buy_btn.click(
            buy_handler,
            inputs=[ledger_state, symbol, quantity],
            outputs=[ledger_state, summary_out, holdings_out, transactions_out, status],
        )
        sell_btn.click(
            sell_handler,
            inputs=[ledger_state, symbol, quantity],
            outputs=[ledger_state, summary_out, holdings_out, transactions_out, status],
        )
        refresh_btn.click(
            refresh_handler,
            inputs=[ledger_state],
            outputs=[ledger_state, summary_out, holdings_out, transactions_out, status],
        )

        def _transactions_to_rows(rows):
            return _tx_rows(rows)

        transactions_out.change(
            _transactions_to_rows,
            inputs=[transactions_out],
            outputs=[transactions_out],
        )

    return demo


if __name__ == "__main__":
    build_app().launch(
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="purple",
            neutral_hue="gray",
        ),
        css=CSS,
    )
