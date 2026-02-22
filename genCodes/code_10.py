
class Matrix:
    """Represents a matrix and provides operations."""

    def __init__(self, rows, cols, data=None):
        """Initializes the matrix with given dimensions and data."""
        self.rows = rows
        self.cols = cols
        if data is None:
            self.data = [[0 for _ in range(cols)] for _ in range(rows)]
        else:
            if len(data) != rows or any(len(row) != cols for row in data):
                raise ValueError("Invalid matrix dimensions.")
            self.data = data

    def __add__(self, other):
        """Add two matrices."""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrices must have the same dimensions for addition.")
        result_data = [[(self.data[i][j] + other.data[i][j]) for j in range(self.cols)] for i in range(self.rows)]
        return Matrix(self.rows, self.cols, result_data)

    def __mul__(self, other):
        """Multiply matrix by scalar or another matrix."""
        if isinstance(other, (int, float)):
            result_data = [[(self.data[i][j] * other) for j in range(self.cols)] for i in range(self.rows)]
            return Matrix(self.rows, self.cols, result_data)
        elif isinstance(other, Matrix):
            if self.cols != other.rows:
                raise ValueError("Number of columns in the first matrix must be equal to the number of rows in the second matrix.")
            result_data = [[sum(self.data[i][k] * other.data[k][j] for k in range(self.cols)) for j in range(other.cols)] for i in range(self.rows)]
            return Matrix(self.rows, other.cols, result_data)
        else:
            raise TypeError("Unsupported operand type for multiplication.")

    def transpose(self):
        """Transpose the matrix."""
        result_data = [[self.data[j][i] for j in range(self.rows)] for i in range(self.cols)]
        return Matrix(self.cols, self.rows, result_data)

    def determinant(self):
        """Calculate determinant (only for square matrices)."""
        if self.rows != self.cols:
            raise ValueError("Determinant can only be calculated for square matrices.")
        if self.rows == 1:
            return self.data[0][0]
        elif self.rows == 2:
            return self.data[0][0] * self.data[1][1] - self.data[0][1] * self.data[1][0]
        else:
            det = 0
            for j in range(self.cols):
                minor = Matrix(self.rows - 1, self.cols - 1, [[self.data[i][k] for k in range(self.cols) if k != j] for i in range(1, self.rows)])
                det += (-1) ** j * self.data[0][j] * minor.determinant()
            return det

    def __str__(self):
        """Return a string representation of the matrix."""
        return '\n'.join([' '.join(map(str, row)) for row in self.data])


if __name__ == '__main__':
    m1 = Matrix(2, 2, [[1, 2], [3, 4]])
    m2 = Matrix(2, 2, [[5, 6], [7, 8]])
    m3 = m1 + m2
    m4 = m1 * 2
    print(f'Sum:\n{m3}')
    print(f"Scalar multiplication:\n{m4}")
    print(f'Determinant of m1: {m1.determinant()}')
