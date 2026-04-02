"""
Хеширование и проверка паролей (bcrypt).

Пароли в открытом виде в хранилище не сохраняются.
"""

import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Возвращает строку с bcrypt-хешем пароля.

    Args:
        plain_password: пароль в открытом виде.

    Returns:
        Соль и хеш в виде строки ASCII (формат bcrypt).
    """
    salt: bytes = bcrypt.gensalt()
    hashed: bytes = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("ascii")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Проверяет пароль против сохранённого хеша.

    Args:
        plain_password: введённый пароль.
        password_hash: ранее сохранённый результат `hash_password`.

    Returns:
        True, если пароль совпадает.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("ascii"),
    )
