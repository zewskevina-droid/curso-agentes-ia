
from datetime import datetime


def get_share_price(symbol: str) -> float:
    """Returns the current price of a share identified by its ticker symbol.
    
    Args:
        symbol: The ticker symbol of the share (e.g., 'AAPL', 'TSLA', 'GOOGL').
        
    Returns:
        The current price of the share as a float.
        
    Raises:
        ValueError: If the symbol is not recognized.
    """
    prices = {
        'AAPL': 190.00,
        'TSLA': 250.00,
        'GOOGL': 140.00,
    }
    symbol_upper = symbol.upper()
    if symbol_upper not in prices:
        raise ValueError(f"Unknown symbol: {symbol}. Recognized symbols are: {list(prices.keys())}")
    return prices[symbol_upper]


class Transaction:
    """A data container representing a single transaction performed by the user."""

    def __init__(
        self,
        transaction_type: str,
        amount: float,
        balance_after: float,
        symbol: str = None,
        quantity: float = None,
        price_per_share: float = None
    ):
        """
        Args:
            transaction_type: Type of transaction. One of: 'DEPOSIT', 'WITHDRAWAL', 'BUY', 'SELL'.
            amount: The cash amount involved.
            balance_after: The cash balance immediately after this transaction.
            symbol: Ticker symbol (only for BUY/SELL).
            quantity: Number of shares (only for BUY/SELL).
            price_per_share: Price per share at transaction time (only for BUY/SELL).
        """
        self.transaction_type = transaction_type
        self.timestamp = datetime.now().isoformat(timespec='seconds')
        self.symbol = symbol
        self.quantity = quantity
        self.price_per_share = price_per_share
        self.amount = amount
        self.balance_after = balance_after

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the transaction."""
        return {
            'transaction_type': self.transaction_type,
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price_per_share': self.price_per_share,
            'amount': self.amount,
            'balance_after': self.balance_after,
        }


class Account:
    """Represents a single user account in the stock market simulation."""

    def __init__(self, owner: str, initial_deposit: float):
        """
        Creates a new account for a user with an initial cash deposit.

        Args:
            owner: The name of the account owner.
            initial_deposit: The initial amount of cash deposited. Must be > 0.

        Raises:
            ValueError: If initial_deposit is <= 0.
        """
        if initial_deposit <= 0:
            raise ValueError("Initial deposit must be greater than zero.")

        self._owner = owner
        self._balance = 0.0
        self._initial_deposit = initial_deposit
        self._total_deposited = 0.0
        self._holdings = {}
        self._transactions = []

        # Record the initial deposit
        self._balance += initial_deposit
        self._total_deposited += initial_deposit
        transaction = Transaction(
            transaction_type='DEPOSIT',
            amount=initial_deposit,
            balance_after=self._balance
        )
        self._transactions.append(transaction)

    def deposit(self, amount: float) -> float:
        """
        Adds funds to the user's cash balance.

        Args:
            amount: The amount of cash to deposit. Must be > 0.

        Returns:
            The new cash balance after the deposit.

        Raises:
            ValueError: If amount <= 0.
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")

        self._balance += amount
        self._total_deposited += amount
        transaction = Transaction(
            transaction_type='DEPOSIT',
            amount=amount,
            balance_after=self._balance
        )
        self._transactions.append(transaction)
        return self._balance

    def withdraw(self, amount: float) -> float:
        """
        Removes funds from the user's cash balance.

        Args:
            amount: The amount of cash to withdraw. Must be > 0.

        Returns:
            The new cash balance after the withdrawal.

        Raises:
            ValueError: If amount <= 0.
            ValueError: If withdrawal would result in a negative balance.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")
        if amount > self._balance:
            raise ValueError(
                f"Insufficient funds. Cannot withdraw {amount:.2f}. "
                f"Current balance: {self._balance:.2f}."
            )

        self._balance -= amount
        transaction = Transaction(
            transaction_type='WITHDRAWAL',
            amount=amount,
            balance_after=self._balance
        )
        self._transactions.append(transaction)
        return self._balance

    def buy_shares(self, symbol: str, quantity: float) -> dict:
        """
        Registers the purchase of a specified quantity of shares.

        Args:
            symbol: The ticker symbol of the stock to buy.
            quantity: The number of shares to buy. Must be > 0.

        Returns:
            A dictionary summarizing the transaction.

        Raises:
            ValueError: If quantity <= 0.
            ValueError: If the user cannot afford the purchase.
            ValueError: If the symbol is not recognized.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        price_per_share = get_share_price(symbol)
        symbol_upper = symbol.upper()
        total_cost = quantity * price_per_share

        if total_cost > self._balance:
            raise ValueError(
                f"Insufficient funds. Cannot buy {quantity} shares of {symbol_upper} "
                f"at {price_per_share:.2f} each (total cost: {total_cost:.2f}). "
                f"Current balance: {self._balance:.2f}."
            )

        self._balance -= total_cost
        self._holdings[symbol_upper] = self._holdings.get(symbol_upper, 0.0) + quantity

        transaction = Transaction(
            transaction_type='BUY',
            amount=total_cost,
            balance_after=self._balance,
            symbol=symbol_upper,
            quantity=quantity,
            price_per_share=price_per_share
        )
        self._transactions.append(transaction)

        return {
            'symbol': symbol_upper,
            'quantity': quantity,
            'price_per_share': price_per_share,
            'total_cost': total_cost,
            'balance_after': self._balance,
        }

    def sell_shares(self, symbol: str, quantity: float) -> dict:
        """
        Registers the sale of a specified quantity of shares.

        Args:
            symbol: The ticker symbol of the stock to sell.
            quantity: The number of shares to sell. Must be > 0.

        Returns:
            A dictionary summarizing the transaction.

        Raises:
            ValueError: If quantity <= 0.
            ValueError: If the user does not hold enough shares.
            ValueError: If the symbol is not recognized.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        symbol_upper = symbol.upper()
        held_quantity = self._holdings.get(symbol_upper, 0.0)

        if held_quantity == 0.0:
            raise ValueError(
                f"Cannot sell {symbol_upper}: you do not hold any shares of this stock."
            )
        if quantity > held_quantity:
            raise ValueError(
                f"Cannot sell {quantity} shares of {symbol_upper}. "
                f"You only hold {held_quantity} shares."
            )

        price_per_share = get_share_price(symbol)
        total_proceeds = quantity * price_per_share

        self._balance += total_proceeds
        self._holdings[symbol_upper] -= quantity

        if self._holdings[symbol_upper] == 0.0:
            del self._holdings[symbol_upper]

        transaction = Transaction(
            transaction_type='SELL',
            amount=total_proceeds,
            balance_after=self._balance,
            symbol=symbol_upper,
            quantity=quantity,
            price_per_share=price_per_share
        )
        self._transactions.append(transaction)

        return {
            'symbol': symbol_upper,
            'quantity': quantity,
            'price_per_share': price_per_share,
            'total_proceeds': total_proceeds,
            'balance_after': self._balance,
        }

    def get_holdings(self) -> dict:
        """
        Returns the user's current share holdings.

        Returns:
            A dictionary mapping ticker symbol to quantity held.
        """
        return dict(self._holdings)

    def get_portfolio_value(self) -> float:
        """
        Calculates the total value of the user's portfolio.

        Returns:
            Total portfolio value = cash balance + market value of all held shares.
        """
        shares_value = sum(
            quantity * get_share_price(symbol)
            for symbol, quantity in self._holdings.items()
        )
        return self._balance + shares_value

    def get_balance(self) -> float:
        """
        Returns the current cash balance of the account.

        Returns:
            The current cash balance.
        """
        return self._balance

    def get_profit_loss(self) -> float:
        """
        Calculates the profit or loss since the account was opened.

        Returns:
            The difference between current portfolio value and total funds deposited.
            Positive = gain, Negative = loss.
        """
        return self.get_portfolio_value() - self._total_deposited

    def get_transactions(self) -> list:
        """
        Returns the full transaction history for the account.

        Returns:
            A list of dictionaries representing each transaction, ordered chronologically.
        """
        return [t.to_dict() for t in self._transactions]

    def get_account_summary(self) -> dict:
        """
        Returns a complete summary of the account's current state.

        Returns:
            A dictionary with owner, cash_balance, holdings, portfolio_value,
            total_deposited, profit_loss, and transaction_count.
        """
        return {
            'owner': self._owner,
            'cash_balance': self._balance,
            'holdings': self.get_holdings(),
            'portfolio_value': self.get_portfolio_value(),
            'total_deposited': self._total_deposited,
            'profit_loss': self.get_profit_loss(),
            'transaction_count': len(self._transactions),
        }
