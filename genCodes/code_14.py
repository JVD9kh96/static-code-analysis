
class Observer:
    """Base observer class."""

    def update(self, event_data):
        """Receive updates from the subject."""
        pass


class Subject:
    """Subject class that notifies observers."""

    def __init__(self):
        """Initialize with an empty list of observers."""
        self._observers = []
        self._state = None

    def attach(self, observer):
        """Attach an observer."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        """Detach an observer."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event_data=None):
        """Notify all observers."""
        for observer in self._observers:
            observer.update(event_data or self._state)

    def set_state(self, state):
        """Set state and notify observers."""
        self._state = state
        self.notify()


class StockPriceObserver(Observer):
    """Observer for stock price changes."""

    def __init__(self, name):
        """Initialize with a name to identify the observer."""
        super().__init__()
        self.name = name
        self.last_price = None

    def update(self, event_data):
        """Handle stock price update."""
        if isinstance(event_data, dict) and 'price' in event_data:
            price = event_data['price']
            symbol = event_data.get('symbol', 'Unknown')
            if self.last_price is not None:
                change = price - self.last_price
                change_pct = change / self.last_price * 100
                print(
                    f'{self.name}: {symbol} changed from ${self.last_price:.2f} to ${price:.2f} ({change_pct:+.2f}%)'
                )
            else:
                print(f'{self.name}: {symbol} is now ${price:.2f}')
            self.last_price = price


class StockMarket(Subject):
    """Stock market that notifies observers of price changes."""

    def __init__(self, symbol):
        """Initialize with a stock symbol."""
        super().__init__()
        self.symbol = symbol
        self.price = 0

    def update_price(self, new_price):
        """Update stock price and notify observers."""
        if new_price != self.price:
            self.price = new_price
            self.notify({'symbol': self.symbol, 'price': new_price})


if __name__ == '__main__':
    market = StockMarket('AAPL')
    observer1 = StockPriceObserver('Trader1')
    observer2 = StockPriceObserver('Trader2')
    market.attach(observer1)
    market.attach(observer2)
    market.update_price(150.0)
    market.update_price(152.5)
    market.update_price(151.75)
