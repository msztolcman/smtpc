import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from smtpc.errors import InvalidPasswordKeyError


def encrypt(data: str, salt: str, key: str) -> str:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
    )
    fernet_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
    fernet = Fernet(fernet_key)
    encrypted = fernet.encrypt(data.encode()).decode()
    return f'enc:{encrypted}'


def decrypt(data: str, salt: str, key: str) -> str:
    if data.startswith('enc:'):
        data = data[4:]

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
    )
    fernet_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
    fernet = Fernet(fernet_key)

    try:
        decrypted = fernet.decrypt(data.encode())
    except InvalidToken:
        raise InvalidPasswordKeyError("Invalid decryption key") from None

    return decrypted.decode()
