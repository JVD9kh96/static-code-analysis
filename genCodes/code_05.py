
class Product:
    """Represents a product."""

    def __init__(self, product_id, name, price):
        """Initializes a new product."""
        self.product_id = product_id
        self.name = name
        self.price = price

    def __repr__(self):
        """Returns a string representation of the product."""
        return f"Product({self.name}, ${self.price:.2f})"


class ShoppingCart:
    """Manages a shopping cart."""

    def __init__(self):
        """Initializes an empty shopping cart."""
        self.items = {}  # Dictionary to store items (product_id: {'product': Product, 'quantity': int})

    def add_item(self, product, quantity=1):
        """Add items to the cart."""
        if quantity <= 0:
            return  # Invalid quantity

        if product.product_id in self.items:
            self.items[product.product_id]['quantity'] += quantity
        else:
            self.items[product.product_id] = {'product': product, 'quantity': quantity}

    def remove_item(self, product_id):
        """Remove an item from the cart."""
        if product_id in self.items:
            del self.items[product_id]

    def update_quantity(self, product_id, quantity):
        """Update quantity of an item."""
        if product_id in self.items:
            if quantity <= 0:
                self.remove_item(product_id)
            else:
                self.items[product_id]['quantity'] = quantity

    def get_total(self):
        """Calculate total price."""
        total = 0
        for item in self.items.values():
            total += item['product'].price * item['quantity']
        return total

    def get_item_count(self):
        """Get total number of items."""
        return sum(item['quantity'] for item in self.items.values())


if __name__ == '__main__':
    cart = ShoppingCart()
    product1 = Product('P001', 'Laptop', 999.99)
    product2 = Product('P002', 'Mouse', 29.99)
    cart.add_item(product1, 1)
    cart.add_item(product2, 2)
    print(f'Total: ${cart.get_total():.2f}')
    print(f'Items: {cart.get_item_count()}')
