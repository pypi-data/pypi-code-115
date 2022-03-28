import random
import string


def password_generator(size_pass: int = 8) -> str:
    letter = string.ascii_letters
    digits = string.digits
    character = '!@#$'
    general = ''.join(letter + digits + character)
    password = ''.join(random.choices(general, k=size_pass if size_pass >= 7 else 7))
    return password


def is_empty(items: tuple) -> bool:
    for n in items:
        if n is not None:
            if len(n.strip()) == 0:
                return True
        else:
            return True
    return False
