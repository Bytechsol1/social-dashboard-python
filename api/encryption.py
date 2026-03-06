"""AES-256-CBC encryption/decryption — binary-compatible with the Node.js implementation.

Format: hex(iv) + ":" + hex(ciphertext)
The secret is padded/truncated to exactly 32 bytes, exactly as the Node code does.
"""
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

_SECRET_RAW = (
    os.environ.get("ENCRYPTION_SECRET")
    or os.environ.get("APP_SECRET_KEY")
    or "f1e2d3c4b5a69788796a5b4c3d2e1f00"
)
# Pad to 32 chars then slice — mirrors Node's `.padEnd(32).slice(0, 32)`
_KEY = (_SECRET_RAW + " " * 32)[:32].encode("utf-8")


def encrypt(text: str) -> str:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # PKCS7 padding
    data = text.encode("utf-8")
    pad_len = 16 - (len(data) % 16)
    data += bytes([pad_len] * pad_len)

    encrypted = encryptor.update(data) + encryptor.finalize()
    return iv.hex() + ":" + encrypted.hex()


def decrypt(token: str) -> str:
    if not token:
        return ""
    # Handle old/plain format: if no ":" it might be stored as plain text or different encoding
    if ":" not in token:
        # Try to return as-is (might be a plain API key stored without encryption)
        return token if token.strip() else ""
    try:
        iv_hex, cipher_hex = token.split(":", 1)
        iv = bytes.fromhex(iv_hex)
        ciphertext = bytes.fromhex(cipher_hex)

        cipher = Cipher(algorithms.AES(_KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove PKCS7 padding
        pad_len = padded[-1]
        if pad_len > 16:  # Invalid padding
            return ""

        try:
            return padded[:-pad_len].decode("utf-8")
        except UnicodeDecodeError:
            return ""
    except (ValueError, Exception):
        # Last resort: return token as-is (it might be unencrypted)
        return token if len(token) > 10 else ""
