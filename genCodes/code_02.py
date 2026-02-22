
class Student:
    """Represents a student."""

    def __init__(self, name, age, student_id):
        """Initialize the student with name, age, and ID."""
        self.name = name
        self.age = age
        self.student_id = student_id
        self.grades = []

    def add_grade(self, grade):
        """Add a grade to the student's record."""
        if 0 <= grade <= 100:
            self.grades.append(grade)

    def get_average(self):
        """Calculate and return the average grade."""
        if not self.grades:
            return 0
        return sum(self.grades) / len(self.grades)

    def get_info(self):
        """Return student information as a string."""
        return f'Student: {self.name}, ID: {self.student_id}, Average: {self.get_average():.2f}'


if __name__ == '__main__':
    student = Student('Alice', 20, 'S001')
    student.add_grade(85)
    student.add_grade(90)
    student.add_grade(78)
    print(student.get_info())
