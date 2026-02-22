
class Node:
    def __init__(self, name):
        self.name = name

    def get_size(self):
        raise NotImplementedError


class File(Node):
    def __init__(self, name, size):
        super().__init__(name)
        self.size = size

    def get_size(self):
        return self.size

    def __repr__(self):
        return f'File({self.name}, {self.size} bytes)'


class Directory(Node):
    def __init__(self, name):
        super().__init__(name)
        self.children = {}

    def add_child(self, node):
        """Add a child node."""
        self.children[node.name] = node

    def get_child(self, name):
        """Get a child node by name."""
        return self.children.get(name)

    def get_size(self):
        """Get total size of directory and all children."""
        total = 0
        for child in self.children.values():
            total += child.get_size()
        return total

    def list_contents(self):
        """List all contents."""
        return list(self.children.keys())

    def find_file(self, filename):
        """Recursively find a file."""
        if filename in self.children:
            node = self.children[filename]
            if isinstance(node, File):
                return node
            else:
                for child in self.children.values():
                    if isinstance(child, Directory):
                        found = child.find_file(filename)
                        if found:
                            return found
                return None
        else:
            return None

    def __repr__(self):
        return f'Directory({self.name}, {len(self.children)} items)'


class FileSystem:
    def __init__(self):
        """Base class for file system nodes."""
        self.root = Directory('/')

    def create_file(self, path, size):
        """Create a file at given path."""
        parts = path.strip('/').split('/')
        current = self.root
        for part in parts[:-1]:
            if part:
                if part not in current.children:
                    current.add_child(Directory(part))
                current = current.children[part]
        filename = parts[-1]
        current.add_child(File(filename, size))

    def get_total_size(self):
        """Get total size of file system."""
        return self.root.get_size()


if __name__ == '__main__':
    fs = FileSystem()
    fs.create_file('/documents/file1.txt', 1024)
    fs.create_file('/documents/file2.txt', 2048)
    fs.create_file('/images/photo.jpg', 5120)
    print(f'Total size: {fs.get_total_size()} bytes')
    print(f'Root contents: {fs.root.list_contents()}')
