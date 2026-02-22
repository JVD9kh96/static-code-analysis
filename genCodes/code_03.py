
class BankAccount:
    """Represents a bank account."""

    def __init__(self, account_number, initial_balance=0):
        """Initializes the bank account with an account number and optional initial balance.

        Args:
            account_number (str): The unique identifier for the account.
            initial_balance (float, optional): The starting amount in the account. Defaults to 0.
        """
        self.account_number = account_number
        self.balance = initial_balance
        self.transaction_history = []

    def deposit(self, amount):
        """Deposit money into the account.

        Args:
            amount (float): The amount to be deposited.

        Returns:
            float: The new balance after the deposit.
        """
        if amount <= 0:
            print("Invalid deposit amount. Amount must be positive.")  # Handle invalid input
            return self.balance
        self.balance += amount
        self.transaction_history.append(('deposit', amount))
        return self.balance

    def withdraw(self, amount):
        """Withdraw money from the account.

        Args:
            amount (float): The amount to be withdrawn.

        Returns:
            float: The new balance after the withdrawal.
        """
        if amount <= 0:
            print("Invalid withdrawal amount. Amount must be positive.")  # Handle invalid input
            return self.balance

        if amount > self.balance:
            print("Insufficient funds.")  # Handle insufficient funds
            return self.balance

        self.balance -= amount
        self.transaction_history.append(('withdraw', amount))
        return self.balance

    def get_balance(self):
        """Get current account balance.

        Returns:
            float: The current account balance.
        """
        return self.balance

    def get_transaction_count(self):
        """Get number of transactions.

        Returns:
            int: The total number of transactions made on the account.
        """
        return len(self.transaction_history)


if __name__ == '__main__':
    account = BankAccount('ACC001', 1000)
    account.deposit(500)
    account.withdraw(200)
    print(f'Balance: {account.get_balance()}')
    print(f'Transactions: {account.get_transaction_count()}')
