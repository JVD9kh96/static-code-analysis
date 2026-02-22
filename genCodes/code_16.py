
class Table:
    def __init__(self, name, columns):
        """Represents a database table."""
        self.name = name
        self.columns = columns
        self.rows = []
        self.column_index = {col: i for i, col in enumerate(columns)}

    def insert(self, row_data):
        """Insert a row into the table."""
        if len(row_data) != len(self.columns):
            raise ValueError("Row data length does not match column count.")
        self.rows.append(list(row_data))

    def select(self, columns=None, where=None):
        """Select rows with optional filtering."""
        if columns is None:
            columns = self.columns

        selected_indices = [self.column_index[col] for col in columns]
        result = []

        for row in self.rows:
            if where is None or where(row):
                selected_row = [row[i] for i in selected_indices]
                result.append(selected_row)

        return Table(f'{self.name}_result', columns).from_rows(result)

    def from_rows(self, rows):
        """Create table from existing rows."""
        self.rows = rows
        return self

    def where(self, condition_func):
        """Filter rows based on condition."""
        return self.select(where=condition_func)

    def join(self, other_table, on_column):
        """Join two tables on a column."""
        if on_column not in self.columns or on_column not in other_table.columns:
            raise ValueError("On column must exist in both tables.")

        self_idx = self.column_index[on_column]
        other_idx = other_table.column_index[on_column]
        new_columns = self.columns + [col for col in other_table.columns if col != on_column]
        result_rows = []

        for self_row in self.rows:
            for other_row in other_table.rows:
                if self_row[self_idx] == other_row[other_idx]:
                    new_row = self_row + [other_row[i] for i, col in enumerate(other_table.columns) if col != on_column]
                    result_rows.append(new_row)

        return Table(f'{self.name}_join_{other_table.name}', new_columns).from_rows(result_rows)

    def group_by(self, column, aggregate_func):
        """Group rows by column and apply aggregate function."""
        if column not in self.columns:
            raise ValueError("Column must exist in the table.")

        col_idx = self.column_index[column]
        groups = {}

        for row in self.rows:
            key = row[col_idx]
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        result = {}
        for key, group_rows in groups.items():
            result[key] = aggregate_func(group_rows)

        return result

    def count(self):
        """Get row count."""
        return len(self.rows)

    def __repr__(self):
        return f'Table({self.name}, {self.count()} rows, {len(self.columns)} columns)'


if __name__ == '__main__':
    employees = Table('employees', ['id', 'name', 'department'])
    employees.insert([1, 'Alice', 'Engineering'])
    employees.insert([2, 'Bob', 'Sales'])
    employees.insert([3, 'Charlie', 'Engineering'])

    salaries = Table('salaries', ['id', 'salary'])
    salaries.insert([1, 5000])
    salaries.insert([2, 4000])
    salaries.insert([3, 5500])

    eng_employees = employees.where(lambda row: row[employees.column_index['department']] == 'Engineering')
    print(f'Engineering employees: {eng_employees.count()}')

    joined = employees.join(salaries, 'id')
    print(f'Joined table: {joined}')
