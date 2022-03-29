from struct import pack


def byte(num: int) -> bytes:
    """
    Converts a number between 0 and 255 (both inclusive) to a base-256 (byte)
    representation.

    :param num:
        An unsigned integer between 0 and 255 (both inclusive).
    :returns:
        A single byte.
    """
    return pack("B", num)


def xor_bytes(b1: bytes, b2: bytes) -> bytes:
    """
    Returns the bitwise XOR result between two bytes objects, b1 ^ b2.

    Bitwise XOR operation is commutative, so order of parameters doesn't
    generate different results. If parameters have different length, extra
    length of the largest one is ignored.

    :param b1:
        First bytes object.
    :param b2:
        Second bytes object.
    :returns:
        Bytes object, result of XOR operation.
    """
    return bytes(x ^ y for x, y in zip(b1, b2))
