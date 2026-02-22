
class Calculator:
    """A simple calculator class."""

    def __init__(self):
        """Initialize the calculator with a result of 0."""
        self.result = 0

    def add(self, a, b):
        """Add two numbers.

        Args:
            a: The first number.
            b: The second number.

        Returns:
            The sum of a and b.
        """
        return a + b

    def subtract(self, a, b):
        """Subtract two numbers.

        Args:
            a: The first number.
            b: The second number.

        Returns:
            The difference between a and b (a - b).
        """
        return a - b

    def multiply(self, a, b):
        """Multiply two numbers.

        Args:
            a: The first number.
            b: The second number.

        Returns:
            The product of a and b.
        """
        return a * b

    def divide(self, a, b):
        """Divide two numbers.

        Args:
            a: The numerator.
            b: The denominator.

        Returns:
            The quotient of a divided by b.  Handles division by zero.
        """
        if b == 0:
            return "Cannot divide by zero"  # Or raise an exception
        else:
            return a / b


if __name__ == '__main__':
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.subtract(10, 4))
    print(calc.multiply(6, 7))
    print(calc.divide(20, 5))
