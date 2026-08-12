from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Настраиваем Argon2
password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Хеширование открытого пароля."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка соответствия пароля хешу."""
    return password_hash.verify(plain_password, hashed_password)