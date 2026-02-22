
class TemperatureConverter:
    """Converts temperatures between Celsius, Fahrenheit, and Kelvin."""

    @staticmethod
    def celsius_to_fahrenheit(celsius):
        """Convert Celsius to Fahrenheit."""
        return celsius * 9 / 5 + 32

    @staticmethod
    def fahrenheit_to_celsius(fahrenheit):
        """Convert Fahrenheit to Celsius."""
        return (fahrenheit - 32) * 5 / 9

    @staticmethod
    def celsius_to_kelvin(celsius):
        """Convert Celsius to Kelvin."""
        return celsius + 273.15

    @staticmethod
    def kelvin_to_celsius(kelvin):
        """Convert Kelvin to Celsius."""
        return kelvin - 273.15

    @staticmethod
    def fahrenheit_to_kelvin(fahrenheit):
        """Convert Fahrenheit to Kelvin."""
        celsius = TemperatureConverter.fahrenheit_to_celsius(fahrenheit)
        return TemperatureConverter.celsius_to_kelvin(celsius)

    @staticmethod
    def kelvin_to_fahrenheit(kelvin):
        """Convert Kelvin to Fahrenheit."""
        celsius = TemperatureConverter.kelvin_to_celsius(kelvin)
        return TemperatureConverter.celsius_to_fahrenheit(celsius)


class Temperature:
    """Represents a temperature value."""

    def __init__(self, value, unit='celsius'):
        """Initialize the temperature with value and unit."""
        self.value = value
        self.unit = unit.lower()
        if self.unit not in ['celsius', 'fahrenheit', 'kelvin']:
            raise ValueError("Invalid unit. Must be 'celsius', 'fahrenheit', or 'kelvin'.")

    def to_celsius(self):
        """Convert to Celsius."""
        if self.unit == 'celsius':
            return self.value
        elif self.unit == 'fahrenheit':
            return TemperatureConverter.fahrenheit_to_celsius(self.value)
        else:
            return TemperatureConverter.kelvin_to_celsius(self.value)

    def to_fahrenheit(self):
        """Convert to Fahrenheit."""
        if self.unit == 'fahrenheit':
            return self.value
        elif self.unit == 'celsius':
            return TemperatureConverter.celsius_to_fahrenheit(self.value)
        else:
            return TemperatureConverter.kelvin_to_fahrenheit(self.value)

    def to_kelvin(self):
        """Convert to Kelvin."""
        if self.unit == 'kelvin':
            return self.value
        elif self.unit == 'celsius':
            return TemperatureConverter.celsius_to_kelvin(self.value)
        else:
            return TemperatureConverter.fahrenheit_to_kelvin(self.value)


if __name__ == '__main__':
    temp = Temperature(25, 'celsius')
    print(f'25°C = {temp.to_fahrenheit():.2f}°F')
    print(f'25°C = {temp.to_kelvin():.2f}K')
