import base64
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as crypto_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import hashes as hash_module
from cryptography.hazmat.backends import default_backend

import constants
from apps.user.exceptions import InvalidEncryptedData


async def create_password() -> str:
    """
    Create a random password.

    :return: A randomly generated password.
    """
    return secrets.token_urlsafe(15)


async def decrypt(
    rsa_key: rsa.RSAPrivateKey,
    enc_data: str,
    encrypt_key: str,
    iv_input: str,
    time_check: bool = False,
    timeout: int = 5,
) -> bytes:
    """Decrypts the given encrypted data.

    :param rsa_key: The RSA private key.
    :param enc_data: Encrypted Data
    :param encrypt_key: Encrypted Key
    :param iv_input: IV Input
    :param time_check: Whether to check the time of the encrypted data
    :param timeout: Timeout in seconds(5 by default)
    :return: Decrypted code
    """
    try:
        code_bytes = encrypt_key.encode("UTF-8")
        encoded_by = base64.b64decode(code_bytes)
        decrypted_key = rsa_key.decrypt(
            encoded_by,
            asym_padding.PKCS1v15()
        ).decode()

        iv = base64.b64decode(iv_input)
        enc = base64.b64decode(enc_data)
        cipher = Cipher(
            algorithms.AES(decrypted_key.encode("utf-8")),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(enc) + decryptor.finalize()
        unpadder = crypto_padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        payload = json.loads(plaintext.decode())
        if time_check:
            exp = datetime.fromisoformat(payload.get("timestamp"))
            if exp is None:
                raise InvalidEncryptedData
            current_time = datetime.now(timezone.utc)
            if (current_time - exp) > timedelta(seconds=timeout):
                raise InvalidEncryptedData
        return plaintext
    except Exception:
        raise InvalidEncryptedData
