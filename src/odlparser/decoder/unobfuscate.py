"""
Unobfuscation and AES decryption for OneDrive ODL logs.

This module provides:
- AES-CBC decryption of obfuscated tokens
- Tokenized replacement of words using the obfuscation map
- A clean OdlDecryptor class that integrates with Keystore + ObfuscationMap
"""

from __future__ import annotations

import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from .keystore import Keystore


class UnobfuscationError(Exception):
    """Raised when unobfuscation or decryption fails."""


class OdlDecryptor:
    """
    High-level decryptor for ODL obfuscated strings.

    Wraps:
    - AES key from Keystore
    - utf_type (utf16 or utf32)
    - obfuscation map (string replacements)

    Usage:
        decryptor = OdlDecryptor(keystore, mapping)
        plaintext = decryptor.unobfuscate("encrypted_or_mapped_token")
    """

    TOKEN_CHARS = r':\.\@%#&*\|{}!?<>;:~()/"\''

    def __init__(self, keystore: Keystore | None, mapping: dict[str, str]):
        self.keystore = keystore
        self.mapping = mapping

    def _decrypt_aes(self, token: str) -> str:
        """
        Attempt AES-CBC decryption of a base64-like token.

        Returns:
            plaintext string, or '' if decryption fails.
        """
        if not self.keystore:
            return ""

        key = self.keystore.key
        utf_type = self.keystore.utf_type

        # Too short to be encrypted
        if len(token) < 22:
            return ""

        # Fix base64 padding
        remainder = len(token) % 4
        if remainder == 1:
            return ""  # invalid base64
        elif remainder in (2, 3):
            token += "=" * (4 - remainder)

        # Replace URL-safe chars
        token = token.replace("_", "/").replace("-", "+")

        try:
            cipher_bytes = base64.b64decode(token)
        except Exception:
            return ""

        # Must be AES block aligned
        if len(cipher_bytes) % 16 != 0:
            return ""

        try:
            cipher = AES.new(key, AES.MODE_CBC, iv=b"\0" * 16)
            raw = cipher.decrypt(cipher_bytes)
        except Exception:
            return ""

        try:
            plain = unpad(raw, 16)
        except Exception:
            return ""

        try:
            return plain.decode(utf_type)
        except Exception:
            return ""

    def _tokenize(self, text: str):
        """
        Split text into (token, is_word) pairs.

        is_word=True → candidate for decryption or map lookup.
        """
        tokens = self.TOKEN_CHARS
        parts = []
        current = ""
        is_word = None

        for ch in text:
            if ch in tokens:
                # flush previous word
                if current and is_word:
                    parts.append((current, True))
                # flush previous token
                elif current and not is_word:
                    parts.append((current, False))

                current = ch
                is_word = False
            else:
                if current and is_word is False:
                    parts.append((current, False))
                    current = ch
                    is_word = True
                else:
                    if not current:
                        is_word = True
                    current += ch

        if current:
            parts.append((current, is_word))

        return parts

    def unobfuscate(self, text: str) -> str:
        """
        Replace obfuscated tokens using:
        - AES decryption (if possible)
        - obfuscation map lookup
        - fallback to original token
        """
        output = []

        for token, is_word in self._tokenize(text):
            if not is_word:
                output.append(token)
                continue

            # Try AES decrypt
            decrypted = self._decrypt_aes(token)
            if decrypted:
                output.append(decrypted)
                continue

            # Try map lookup
            if token in self.mapping:
                output.append(self.mapping[token])
                continue

            # Fallback
            output.append(token)

        return "".join(output)
