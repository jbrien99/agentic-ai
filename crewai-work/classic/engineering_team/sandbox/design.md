# Detailed Design: Trading Simulation Account Management System

## 1. Goal

Build a simple account management system for a trading simulation platform that supports:

- Account creation
- Cash deposits and withdrawals
- Recording buy/sell share transactions with quantities
- Calculating portfolio value
- Calculating profit/loss from initial deposit
- Reporting holdings at any point in time
- Reporting profit/loss at any point in time
- Listing all transactions over time
- Preventing invalid withdrawals, unaffordable buys, and overselling

The system has access to:

- `get_share_price(symbol)` returning the current price for a share symbol
- A test implementation that returns fixed prices for `AAPL`, `TSLA`, `GOOGL`

All files live in the same directory. No subdirectories/packages. No external third-party libraries beyond `gradio` are available.

---

## 2. Architecture Overview

### Recommended file layout

- `models.py` — core domain dataclasses
- `ledger.py` — account/portfolio engine and validation logic
- `app.py` — Gradio UI
- `test_ledger.py` — unit tests for backend logic
- `prices.py` — price lookup abstraction and test implementation stub
- `main.py` — optional small entrypoint if desired, but not required

Because there is no directory structure, each file should import from the others by filename only.

---

## 3. Domain Model

The backend should use a small, explicit domain model. Keep the business logic independent of Gradio.

### 3.1 Core concepts

- **Account**
  - Identified by account ID or username
  - Has starting cash balance from deposits
  - Has current cash balance
  - Has share holdings by symbol
  - Has transaction history

- **Transaction**
  - Represents one user action:
    - deposit
    - withdrawal
    - buy
    - sell
  - Contains timestamp/order index, symbol if applicable, quantity if applicable, and cash amount involved

- **Holding**
  - Symbol
  - Quantity owned
  - Current market value
  - Cost basis tracking is optional unless needed for clearer profit/loss calculations
    - For this system, profit/loss is based on current portfolio value + cash - initial deposits

- **Portfolio Snapshot**
  - Cash balance
  - Holdings
  - Total market value of holdings
  - Total account value
  - Profit/loss vs initial deposits

---

## 4. Business Rules

### 4.1 Deposits
- Deposit amount must be positive
- Deposit increases cash balance
- Deposit increases total deposited capital
- Deposit is recorded as a transaction

### 4.2 Withdrawals
- Withdrawal amount must be positive
- Withdrawal cannot exceed available cash balance
- Withdrawal decreases cash balance
- Withdrawal is recorded as a transaction

### 4.3 Buy shares
- Symbol must be supported by `get_share_price(symbol)`
- Quantity must be positive integer
- Total cost = current share price × quantity
- User must have enough cash to cover the buy
- Buy reduces cash balance
- Buy increases holdings quantity for that symbol
- Buy is recorded as a transaction

### 4.4 Sell shares
- Symbol must be supported by `get_share_price(symbol)`
- Quantity must be positive integer
- User must own at least that quantity
- Sell increases cash balance by current market proceeds
- Sell reduces holdings quantity
- If quantity becomes zero, the holding may be removed from the holdings map
- Sell is recorded as a transaction

### 4.5 Portfolio value
- Current portfolio value = cash balance + sum(current price × holding quantity for each symbol)

### 4.6 Profit/loss
- Profit/loss = current total account value − total deposits + total withdrawals?  
  **Recommended definition:** Profit/loss from initial deposit should be based on net external cash flow:
  - `net_contributed_cash = total_deposits - total_withdrawals`
  - `profit_loss = current_total_value - net_contributed_cash`
- This definition ensures withdrawals reduce the invested capital base accordingly
- If the product owner wants P/L strictly against initial deposit only, the engine should support both:
  - `profit_loss_vs_initial_deposit`
  - `profit_loss_vs_net_contributions`
- For the requested requirement, expose the net-contributions version as the default, and also keep `initial_deposit_total` available for reporting

### 4.7 Holdings report
- Must return current quantity per symbol
- Must optionally include current market value per symbol

### 4.8 Transaction history
- Must return all transactions in chronological order
- Each transaction should include enough detail for auditability:
  - sequence number / timestamp
  - type
  - symbol
  - quantity
  - unit price
  - total cash impact
  - resulting cash balance after transaction

---

## 5. Backend Design

## 5.1 File: `prices.py`

This file defines the share price abstraction used by the backend and test implementation.

### Responsibilities
- Provide a single place to look up prices
- Allow easy swapping between production and test price providers

### Functions
#### `get_share_price(symbol: str) -> float`
- Existing external function contract
- Returns current price for `symbol`

#### `get_test_share_price(symbol: str) -> float`
- Test implementation with fixed prices for:
  - `AAPL`
  - `TSLA`
  - `GOOGL`

#### `is_supported_symbol(symbol: str) -> bool`
- Returns whether the symbol can be priced
- Recommended for pre-validation before buy/sell actions

---

## 5.2 File: `models.py`

Use dataclasses for plain data objects. These are simple containers; keep logic out of them.

### Classes

#### `TransactionRecord`
Represents one action in the ledger.

**Fields**
- `tx_id: int`
- `account_id: str`
- `tx_type: str`  
  Allowed values: `"deposit"`, `"withdrawal"`, `"buy"`, `"sell"`
- `symbol: str | None`
- `quantity: int | None`
- `unit_price: float | None`
- `cash_amount: float`
- `timestamp: str`
- `cash_balance_after: float`

#### `HoldingRecord`
Represents a current position.

**Fields**
- `symbol: str`
- `quantity: int`
- `current_price: float`
- `market_value: float`

#### `AccountSummary`
Represents a portfolio summary.

**Fields**
- `account_id: str`
- `cash_balance: float`
- `net_contributed_cash: float`
- `holdings_market_value: float`
- `total_account_value: float`
- `profit_loss: float`

#### `AccountState`
Internal state object for an account.

**Fields**
- `account_id: str`
- `cash_balance: float`
- `total_deposits: float`
- `total_withdrawals: float`
- `holdings: dict[str, int]`
- `transactions: list[TransactionRecord]`
- `next_tx_id: int`

---

## 5.3 File: `ledger.py`

This is the core backend module. It should contain the business logic and validation.

### Class: `TradingAccountLedger`

A single object manages one account. If multi-account support is desired later, a registry can be added, but the requirements are satisfied with one account object per user.

#### Constructor
`__init__(self, account_id: str, price_lookup: callable = get_share_price) -> None`

- Initializes a new account ledger
- `price_lookup` allows dependency injection for tests
- Must not perform any I/O

#### Methods

##### `deposit(self, amount: float) -> TransactionRecord`
- Validates positive amount
- Updates cash balance
- Records transaction
- Returns transaction

##### `withdraw(self, amount: float) -> TransactionRecord`
- Validates positive amount
- Raises error if amount exceeds cash balance
- Updates cash balance
- Records transaction
- Returns transaction

##### `buy_shares(self, symbol: str, quantity: int) -> TransactionRecord`
- Validates symbol
- Validates quantity > 0
- Resolves current share price
- Raises error if cash balance insufficient
- Updates holdings and cash balance
- Records transaction
- Returns transaction

##### `sell_shares(self, symbol: str, quantity: int) -> TransactionRecord`
- Validates symbol
- Validates quantity > 0
- Validates owned quantity is sufficient
- Resolves current share price
- Updates holdings and cash balance
- Records transaction
- Returns transaction

##### `get_holdings(self) -> list[HoldingRecord]`
- Returns current holdings, one record per symbol
- Values should include current market price and value

##### `get_transaction_history(self) -> list[TransactionRecord]`
- Returns full chronological transaction list

##### `get_portfolio_value(self) -> float`
- Returns cash + holdings market value

##### `get_profit_loss(self) -> float`
- Returns current value - net contributed cash

##### `get_summary(self) -> AccountSummary`
- Returns complete snapshot

##### `get_cash_balance(self) -> float`
- Returns current liquid cash

##### `get_holding_quantity(self, symbol: str) -> int`
- Returns current quantity for a symbol, or 0 if not held

##### `validate_symbol(self, symbol: str) -> None`
- Validates price availability
- Raises a clear exception if unsupported

##### `validate_quantity(self, quantity: int) -> None`
- Validates quantity > 0

#### Suggested internal helpers

##### `_record_transaction(...) -> TransactionRecord`
- Internal method to create and append transaction records

##### `_current_holding_value(self) -> float`
- Internal helper for portfolio value calculation

##### `_get_current_price(self, symbol: str) -> float`
- Internal price access wrapper

---

## 5.4 Backend error handling

Use clear, standard exception types or small custom exceptions.

### Recommended exceptions
- `ValueError` for invalid input
- `LookupError` or `KeyError` for unsupported symbols
- `RuntimeError` or `ValueError` for insufficient funds/holdings

### Suggested custom exceptions
If you prefer explicit error semantics, define these in `ledger.py`:

- `InsufficientFundsError`
- `InsufficientHoldingsError`
- `InvalidTransactionError`
- `UnsupportedSymbolError`

**Recommended signatures**
- `class InsufficientFundsError(Exception): ...`
- `class InsufficientHoldingsError(Exception): ...`
- `class InvalidTransactionError(Exception): ...`
- `class UnsupportedSymbolError(Exception): ...`

The implementation choice should be consistent across the module and tests.

---

## 6. Profit/Loss Definition

The system should compute profit/loss as:

`profit_loss = current_total_account_value - (total_deposits - total_withdrawals)`

Where:

- `current_total_account_value = cash_balance + holdings_market_value`
- `holdings_market_value = sum(quantity × current_price)`

This captures the true gain/loss of the account after all external cash flows.

### Optional additional reporting
If desired, also expose:
- `profit_loss_vs_initial_deposit`
- `net_contributed_cash`
- `initial_deposit_total`

This can help the UI display clearer audit information.

---

## 7. Public API Surface

The backend should expose a minimal, stable API. Recommended callable signatures:

### In `ledger.py`

- `class TradingAccountLedger:`
  - `def __init__(self, account_id: str, price_lookup: callable = get_share_price) -> None`
  - `def deposit(self, amount: float) -> TransactionRecord`
  - `def withdraw(self, amount: float) -> TransactionRecord`
  - `def buy_shares(self, symbol: str, quantity: int) -> TransactionRecord`
  - `def sell_shares(self, symbol: str, quantity: int) -> TransactionRecord`
  - `def get_holdings(self) -> list[HoldingRecord]`
  - `def get_transaction_history(self) -> list[TransactionRecord]`
  - `def get_portfolio_value(self) -> float`
  - `def get_profit_loss(self) -> float`
  - `def get_summary(self) -> AccountSummary`
  - `def get_cash_balance(self) -> float`
  - `def get_holding_quantity(self, symbol: str) -> int`

### Optional factory/helper functions
- `def create_ledger(account_id: str, price_lookup: callable = get_share_price) -> TradingAccountLedger`
- `def ledger_from_seed(account_id: str, initial_deposit: float, price_lookup: callable = get_share_price) -> TradingAccountLedger`

---

## 8. Frontend Design: Gradio App

The frontend should be a single Gradio app that lets a user manage one simulated account interactively.

## 8.1 File: `app.py`

### Responsibilities
- Create the Gradio Blocks UI
- Call backend methods
- Render summary, holdings, and transaction history
- Show errors cleanly
- Keep UI logic separate from business logic

---

## 8.2 UI layout

Recommended sections:

### Section A: Account setup
- Account ID textbox
- Optional initial deposit textbox
- Button: Create account

### Section B: Cash actions
- Deposit amount textbox + button
- Withdraw amount textbox + button

### Section C: Trading actions
- Symbol textbox or dropdown
- Quantity number input
- Buy button
- Sell button

### Section D: Reporting
- Summary output
- Holdings output
- Transaction history output
- Profit/loss output
- Refresh button

---

## 8.3 Gradio 6 API guidance for frontend engineer

### Important Gradio 6 change: app-level parameters moved to `launch()`
Do **not** pass `theme`, `css`, `js`, `head`, `css_paths`, or `head_paths` into `gr.Blocks(...)`.

Use:

- `with gr.Blocks() as demo:`
- `demo.launch(theme=..., css=..., js=..., head=...)`

### Example pattern
- Build UI inside `with gr.Blocks() as demo:`
- Put app-wide styling in `demo.launch(...)`

### Component and event usage
Use standard Gradio 6 event APIs:
- `button.click(fn=..., inputs=..., outputs=...)`
- `textbox.submit(fn=..., inputs=..., outputs=...)`
- `dropdown.change(fn=..., inputs=..., outputs=...)`

### Output update behavior
Event callbacks may:
- return raw values
- return tuples/lists matching outputs
- return dicts keyed by components for partial updates

If the UI needs to update multiple widgets, prefer straightforward tuple returns unless partial updates are required.

### State handling
Use `gr.State` to hold the backend `TradingAccountLedger` instance.

Important:
- `gr.State` is session-scoped
- backend state should live in `gr.State`, not global variables
- event handlers should take the state as input and return it as output when modified

### Recommended event patterns
- `create_account_button.click(create_account_handler, inputs=[...], outputs=[ledger_state, ...])`
- `deposit_button.click(deposit_handler, inputs=[ledger_state, deposit_amount], outputs=[ledger_state, summary_output, holdings_output, tx_output, status_output])`
- Similar patterns for withdraw/buy/sell

### Component suggestions
- `gr.Textbox` for account ID and symbol
- `gr.Number` for deposit/withdrawal amount
- `gr.Number` for share quantity
- `gr.JSON` for summary and holdings if structured data is preferred
- `gr.Dataframe` for transaction history if tabular display is preferred

### Dataframe migration guidance
Gradio 6 removed older `show_copy_button` / `show_fullscreen_button` kwargs on `gr.Dataframe`.
Use:
- `buttons=["copy", "fullscreen"]`

### Recommended simple display choices
- `gr.JSON` for summary and holdings
- `gr.Dataframe` for transactions
- `gr.Markdown` or `gr.Textbox` for status/error messages

---

## 8.4 Frontend function signatures

### `app.py`

#### `build_app() -> gr.Blocks`
- Constructs and returns the Gradio app

#### `create_account_handler(account_id: str, initial_deposit: float | None) -> tuple`
- Creates a new `TradingAccountLedger`
- Optionally performs initial deposit
- Returns:
  - ledger state
  - summary view
  - holdings view
  - transaction history view
  - status message

#### `deposit_handler(ledger: TradingAccountLedger, amount: float) -> tuple`
- Performs deposit and returns updated outputs

#### `withdraw_handler(ledger: TradingAccountLedger, amount: float) -> tuple`
- Performs withdrawal and returns updated outputs

#### `buy_handler(ledger: TradingAccountLedger, symbol: str, quantity: int) -> tuple`
- Performs buy and returns updated outputs

#### `sell_handler(ledger: TradingAccountLedger, symbol: str, quantity: int) -> tuple`
- Performs sell and returns updated outputs

#### `refresh_handler(ledger: TradingAccountLedger) -> tuple`
- Recomputes summary, holdings, and transaction history without mutating state

#### `format_summary(summary: AccountSummary) -> dict`
- Converts backend summary to a UI-friendly structure

#### `format_holdings(holdings: list[HoldingRecord]) -> list[dict]`
- Converts holdings to UI-friendly list/dicts

#### `format_transactions(transactions: list[TransactionRecord]) -> list[dict]`
- Converts transactions to UI-friendly table rows

---

## 9. Backend Implementation Notes

## 9.1 Data representation
Use simple Python data structures:
- `dict[str, int]` for holdings
- `list[TransactionRecord]` for history

## 9.2 Ordering
Maintain transaction history in append order with monotonically increasing `tx_id`.

## 9.3 Precision
Financial values should be rounded consistently for display, but internal logic should remain as precise as practical with floats.

Recommended:
- store floats internally
- round only for presentation
- backend tests should allow exact arithmetic where possible or use tolerance

## 9.4 Symbol validation
The system only needs to support symbols returned by the provided share price function. The test prices are fixed for:
- `AAPL`
- `TSLA`
- `GOOGL`

If an unsupported symbol is provided, raise a clear error before mutating state.

---

## 10. Test Design

## 10.1 File: `test_ledger.py`

The test engineer should write unit tests for the backend module only.

### Testing strategy
- Inject the test price function into `TradingAccountLedger`
- Validate normal flows
- Validate failure modes
- Validate portfolio and profit/loss calculations
- Validate transaction history integrity

### Test cases to include

#### Account creation
- New ledger starts with zero balance, no holdings, no transactions

#### Deposit
- Positive deposit increases cash
- Deposit transaction is recorded
- Negative or zero deposit is rejected

#### Withdrawal
- Valid withdrawal decreases cash
- Withdrawal transaction is recorded
- Withdrawal exceeding cash is rejected
- Negative or zero withdrawal is rejected

#### Buy shares
- Buying supported symbol with sufficient cash works
- Buy reduces cash and increases holdings
- Buying more than available cash is rejected
- Buying unsupported symbol is rejected
- Quantity zero/negative is rejected

#### Sell shares
- Selling owned shares works
- Selling reduces holdings and increases cash
- Selling more than owned is rejected
- Selling unsupported symbol is rejected
- Quantity zero/negative is rejected

#### Holdings report
- Holdings reflect current positions after buys/sells
- Zero-quantity positions are omitted or normalized away

#### Transaction history
- All actions appear in order
- Transaction records contain the expected fields

#### Portfolio value
- Cash + holdings market value is computed correctly using fixed prices

#### Profit/loss
- P/L is computed correctly after deposits, buys, sells, withdrawals

#### Edge cases
- Multiple transactions for same symbol
- Full liquidation
- Withdraw entire cash balance
- Sell entire position
- Attempt to overspend by one unit

---

## 10.2 Suggested test helper functions

#### `make_ledger() -> TradingAccountLedger`
- Returns a ledger wired to test prices

#### `assert_summary(...)`
- Optional helper to reduce repeated assertions

---

## 11. Suggested Implementation Contracts

The backend engineer and test engineer should align on exact exception behavior and function return shape.

### Recommended function return shape for transaction methods
Each mutating method should return the created transaction record:
- `deposit(amount) -> TransactionRecord`
- `withdraw(amount) -> TransactionRecord`
- `buy_shares(symbol, quantity) -> TransactionRecord`
- `sell_shares(symbol, quantity) -> TransactionRecord`

This makes UI updates and testing straightforward.

### Recommended summary shape
`get_summary()` should provide:
- cash balance
- holdings market value
- total account value
- net contributed cash
- profit/loss

### Recommended holdings shape
Each holding should show:
- symbol
- quantity
- current price
- market value

### Recommended transaction history shape
Each transaction should show:
- tx_id
- type
- symbol
- quantity
- unit price
- cash amount
- resulting cash balance
- timestamp

---

## 12. Work Assignment

## 12.1 `backend_engineer`
Build the backend engine.

### Deliverables
- `prices.py`
- `models.py`
- `ledger.py`

### Responsibilities
- Implement all domain models
- Implement validation and accounting logic
- Ensure all calculations are correct
- Keep code clean and testable
- No UI code

### Required function/method signatures to implement
- `get_test_share_price(symbol: str) -> float`
- `is_supported_symbol(symbol: str) -> bool`
- `class TransactionRecord`
- `class HoldingRecord`
- `class AccountSummary`
- `class AccountState`
- `class TradingAccountLedger`
  - `__init__(...)`
  - `deposit(...)`
  - `withdraw(...)`
  - `buy_shares(...)`
  - `sell_shares(...)`
  - `get_holdings(...)`
  - `get_transaction_history(...)`
  - `get_portfolio_value(...)`
  - `get_profit_loss(...)`
  - `get_summary(...)`
  - `get_cash_balance(...)`
  - `get_holding_quantity(...)`

---

## 12.2 `frontend_engineer`
Build the Gradio UI.

### Deliverables
- `app.py`

### Responsibilities
- Create a simple, clear Gradio app
- Hold ledger state in `gr.State`
- Wire UI controls to backend methods
- Display summary, holdings, and transactions
- Show readable error/status messages

### Gradio 6 guidance
- Use `with gr.Blocks() as demo:`
- Put app-level styling and theme in `demo.launch(...)`
- Use `gr.JSON` and/or `gr.Dataframe` for structured outputs
- Use `button.click(...)`, `textbox.submit(...)`, `dropdown.change(...)`
- Do not use removed `Dataframe` kwargs like `show_copy_button`; use `buttons=[...]` instead
- Do not put `theme=` on `Blocks(...)`

### Required function signatures to implement
- `build_app() -> gr.Blocks`
- `create_account_handler(account_id: str, initial_deposit: float | None) -> tuple`
- `deposit_handler(ledger, amount: float) -> tuple`
- `withdraw_handler(ledger, amount: float) -> tuple`
- `buy_handler(ledger, symbol: str, quantity: int) -> tuple`
- `sell_handler(ledger, symbol: str, quantity: int) -> tuple`
- `refresh_handler(ledger) -> tuple`
- `format_summary(summary) -> dict`
- `format_holdings(holdings) -> list[dict]`
- `format_transactions(transactions) -> list[dict]`

---

## 12.3 `test_engineer`
Write backend unit tests.

### Deliverables
- `test_ledger.py`

### Responsibilities
- Write focused unit tests for `ledger.py`
- Use the fixed test price function
- Cover happy paths and all failure cases
- Ensure transaction ordering and balances are correct

### Required test focus
- Deposits
- Withdrawals
- Buys
- Sells
- Holdings report
- Portfolio value
- Profit/loss
- Transaction history
- Validation errors

---

## 13. Acceptance Criteria

The system is complete when:

- A user can create an account
- A user can deposit and withdraw cash
- A user can buy and sell shares using quantities
- The system prevents invalid balance/holdings states
- Holdings can be reported at any time
- Transactions can be listed at any time
- Portfolio value is computed from current share prices
- Profit/loss is computed correctly
- Backend tests pass
- Gradio app runs successfully in the uv environment

---

## 14. Implementation Notes for Engineers

### For backend_engineer
- Keep the module dependency graph simple:
  - `ledger.py` imports `models.py` and `prices.py`
  - `models.py` should have no project imports
  - `prices.py` should be standalone
- Avoid circular imports
- Keep functions small and explicit

### For frontend_engineer
- Keep UI logic thin
- Use backend objects for all calculations
- Handle exceptions and surface them in a status area rather than crashing the app
- Prefer structured components for clarity:
  - summary -> `gr.JSON`
  - holdings -> `gr.JSON` or `gr.Dataframe`
  - transactions -> `gr.Dataframe`

### For test_engineer
- Tests should not depend on Gradio
- Use direct method calls on `TradingAccountLedger`
- Validate that errors are raised before any state mutation occurs

---

## 15. Final Recommended Module Signatures

## `prices.py`
- `def get_test_share_price(symbol: str) -> float`
- `def is_supported_symbol(symbol: str) -> bool`

## `models.py`
- `@dataclass class TransactionRecord`
- `@dataclass class HoldingRecord`
- `@dataclass class AccountSummary`
- `@dataclass class AccountState`

## `ledger.py`
- `class InsufficientFundsError(Exception)`
- `class InsufficientHoldingsError(Exception)`
- `class InvalidTransactionError(Exception)`
- `class UnsupportedSymbolError(Exception)`
- `class TradingAccountLedger`
  - `def __init__(self, account_id: str, price_lookup: callable = get_share_price) -> None`
  - `def deposit(self, amount: float) -> TransactionRecord`
  - `def withdraw(self, amount: float) -> TransactionRecord`
  - `def buy_shares(self, symbol: str, quantity: int) -> TransactionRecord`
  - `def sell_shares(self, symbol: str, quantity: int) -> TransactionRecord`
  - `def get_holdings(self) -> list[HoldingRecord]`
  - `def get_transaction_history(self) -> list[TransactionRecord]`
  - `def get_portfolio_value(self) -> float`
  - `def get_profit_loss(self) -> float`
  - `def get_summary(self) -> AccountSummary`
  - `def get_cash_balance(self) -> float`
  - `def get_holding_quantity(self, symbol: str) -> int`

## `app.py`
- `def build_app() -> gr.Blocks`
- `def create_account_handler(account_id: str, initial_deposit: float | None) -> tuple`
- `def deposit_handler(ledger, amount: float) -> tuple`
- `def withdraw_handler(ledger, amount: float) -> tuple`
- `def buy_handler(ledger, symbol: str, quantity: int) -> tuple`
- `def sell_handler(ledger, symbol: str, quantity: int) -> tuple`
- `def refresh_handler(ledger) -> tuple`
- `def format_summary(summary) -> dict`
- `def format_holdings(holdings) -> list[dict]`
- `def format_transactions(transactions) -> list[dict]`

## `test_ledger.py`
- Unit test functions covering all backend behaviors

---

## 16. Recommended Build Order

1. `backend_engineer`
   - Implement `prices.py`
   - Implement `models.py`
   - Implement `ledger.py`

2. `test_engineer`
   - Write `test_ledger.py`
   - Validate all backend behaviors
   - Coordinate with backend engineer on exception types and data shapes

3. `frontend_engineer`
   - Implement `app.py`
   - Integrate backend API
   - Verify Gradio 6 launch/update patterns

---

## 17. Summary of Gradio 6 Guidance

For the frontend engineer, the most important Gradio 6 points are:

- `theme`, `css`, `js`, `head` moved from `gr.Blocks(...)` to `demo.launch(...)`
- Use `with gr.Blocks() as demo:`
- Use `button.click`, `textbox.submit`, `dropdown.change`
- Use `gr.State` for the backend ledger instance
- Prefer `gr.JSON` / `gr.Dataframe` for structured outputs
- For `gr.Dataframe`, use `buttons=[...]` instead of removed copy/fullscreen kwargs

This design is sufficient to implement the system successfully in the provided sandbox.