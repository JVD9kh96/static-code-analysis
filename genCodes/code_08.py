
class Employee:
    """Base class for employees."""

    def __init__(self, name, employee_id, base_salary):
        """Initialize an employee with name, ID and salary."""
        self.name = name
        self.employee_id = employee_id
        self.base_salary = base_salary

    def calculate_salary(self):
        """Calculate the basic salary of the employee."""
        return self.base_salary

    def get_info(self):
        """Get employee information."""
        return f'{self.name} (ID: {self.employee_id})'


class Manager(Employee):
    """Manager class inheriting from Employee."""

    def __init__(self, name, employee_id, base_salary, bonus):
        """Initialize a manager with name, ID, salary and bonus."""
        super().__init__(name, employee_id, base_salary)
        self.bonus = bonus

    def calculate_salary(self):
        """Calculate the salary of the manager with bonus."""
        return self.base_salary + self.bonus


class Developer(Employee):
    """Developer class inheriting from Employee."""

    def __init__(self, name, employee_id, base_salary, overtime_hours=0):
        """Initialize a developer with name, ID, salary and overtime hours."""
        super().__init__(name, employee_id, base_salary)
        self.overtime_hours = overtime_hours

    def calculate_salary(self):
        """Calculate the salary of the developer with overtime pay."""
        return self.base_salary + self.overtime_hours * 10  # Assuming $10 per hour as overtime rate

    def add_overtime(self, hours):
        """Add overtime hours to the developer's record."""
        if hours > 0:
            self.overtime_hours += hours


class SalesPerson(Employee):
    """Sales person class inheriting from Employee."""

    def __init__(self, name, employee_id, base_salary, commission_rate=0.1):
        """Initialize a salesperson with name, ID, salary and commission rate."""
        super().__init__(name, employee_id, base_salary)
        self.commission_rate = commission_rate
        self.sales_amount = 0

    def add_sale(self, amount):
        """Add a sale to the salesperson's record."""
        if amount > 0:
            self.sales_amount += amount

    def calculate_salary(self):
        """Calculate salary with commission."""
        return self.base_salary + self.sales_amount * self.commission_rate


if __name__ == '__main__':
    manager = Manager('Alice', 'E001', 5000, 1000)
    developer = Developer('Bob', 'E002', 4000, 10)
    salesperson = SalesPerson('Charlie', 'E003', 3000, 0.15)
    salesperson.add_sale(10000)
    employees = [manager, developer, salesperson]

    for emp in employees:
        print(f'{emp.get_info()}: ${emp.calculate_salary():.2f}')
