import random
import string


def generate_random_string(length: int):
    """Return a random string with given length"""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))