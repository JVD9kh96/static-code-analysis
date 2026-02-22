
class Book:
    """Represents a book in the library."""

    def __init__(self, title, author, isbn):
        """Initializes a new book with title, author and ISBN."""
        self.title = title
        self.author = author
        self.isbn = isbn
        self.is_available = True  # Initially, the book is available

    def borrow(self):
        """Borrow the book."""
        if not self.is_available:
            print("Book is already borrowed.")
            return
        self.is_available = False
        print(f"'{self.title}' has been borrowed.")

    def return_book(self):
        """Return the book."""
        self.is_available = True
        print(f"'{self.title}' has been returned.")

    def __str__(self):
        """Returns a string representation of the book."""
        status = 'Available' if self.is_available else 'Borrowed'
        return f'{self.title} by {self.author} - {status}'


class Library:
    """Manages a collection of books."""

    def __init__(self):
        """Initializes an empty library with an empty list of books."""
        self.books = []

    def add_book(self, book):
        """Add a book to the library."""
        self.books.append(book)
        print(f"'{book.title}' added to the library.")

    def find_book(self, isbn):
        """Find a book by ISBN."""
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None  # Book not found

    def list_available_books(self):
        """List all available books."""
        return [book for book in self.books if book.is_available]


if __name__ == '__main__':
    library = Library()
    book1 = Book('Python Basics', 'John Doe', 'ISBN001')
    book2 = Book('Advanced Python', 'Jane Smith', 'ISBN002')
    library.add_book(book1)
    library.add_book(book2)
    book1.borrow()
    print(book1)
    print(f'Available books: {len(library.list_available_books())}')
