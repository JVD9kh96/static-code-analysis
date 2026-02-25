import random
import string

def generate_token(length=32):
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print(generate_token(16))
