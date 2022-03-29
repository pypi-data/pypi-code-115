from .key import newkeys, PrivateKey, PublicKey
from .pkcs1 import (
    encrypt,
    decrypt,
    sign,
    verify,
    DecryptionError,
    VerificationError,
    find_signature_hash,
    sign_hash,
    compute_hash,
)

__author__ = "Sybren Stuvel, Barry Mead and Yesudeep Mangalapilly"
__date__ = "2021-11-24"
__version__ = "4.8"

# Do doctest if we're run directly
if __name__ == "__main__":
    import doctest

    doctest.testmod()

__all__ = [
    "newkeys",
    "encrypt",
    "decrypt",
    "sign",
    "verify",
    "PublicKey",
    "PrivateKey",
    "DecryptionError",
    "VerificationError",
    "find_signature_hash",
    "compute_hash",
    "sign_hash",
]
