from pathlib import Path

def read_user_file(filename: str) -> str:
    base = Path("uploads")
    target = base / filename
    with target.open("r", encoding="utf-8") as fh:
        return fh.read()

if __name__ == "__main__":
    print(read_user_file("example.txt"))
