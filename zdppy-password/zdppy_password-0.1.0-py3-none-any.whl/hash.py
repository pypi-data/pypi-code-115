import hashlib
from typing import Union


def hash_password(htype: str, data: Union[str, bytes], salt: str = None):
    """
    使用sha1加密算法加密数据
    :param htype: 加密类型
    :param data: 要加密的数据
    :param salt: 盐值
    :return: 加密后的字符串
    """
    # 校验类型
    if htype not in ["md5", "sha1", "sha256", "sha512"]:
        # TODO: 抛出异常
        print("不支持的加密类型")
        return

    # 创建加密对象
    m = None
    if salt is not None:
        m = hashlib.new(htype, salt.encode())
    else:
        m = hashlib.new(htype)

    # 加密
    if isinstance(data, str):
        m.update(data.encode())
    elif isinstance(data, bytes):
        m.update(data)
    else:
        # TODO：抛出异常
        print("参数错误，data应该是str类型或者bytes类型")

    # 转换为16进制字符串
    result = m.hexdigest()

    # 返回加密后的字符串
    return result


def md5(data: Union[str, bytes], salt: str = None):
    """
    使用md5算法对数据进行加密
    :param data: 要加密的数据
    :param salt: 增加安全性的盐值
    :return: 加密后的字符串
    """
    return hash_password("md5", data, salt)


def md5_verify(data, md5_str, salt: str = None):
    """
    校验数据和md5加密后的字符串是否一致
    :param data: 数据
    :param md5_str: md5加密后的字符串
    :param salt: 增加安全性的盐值
    :return: 校验结果
    """
    result = md5(data, salt)
    return result == md5_str


def sha1(data: Union[str, bytes], salt: str = None):
    """
    使用sha1加密算法加密数据
    :param data: 要加密的数据
    :param salt: 盐值
    :return: 加密后的字符串
    """
    return hash_password("sha1", data, salt)


def sha1_verify(data, password, salt: str = None):
    result = sha1(data, salt)
    return result == password


def sha256(data: Union[str, bytes], salt: str = None):
    """
    使用sha256加密算法加密数据
    :param data: 要加密的数据
    :param salt: 盐值
    :return: 加密后的字符串
    """
    return hash_password("sha256", data, salt)


def sha256_verify(data, password, salt: str = None):
    result = sha256(data, salt)
    return result == password


def sha512(data: Union[str, bytes], salt: str = None):
    """
    使用sha512加密算法加密数据
    :param data: 要加密的数据
    :param salt: 盐值
    :return: 加密后的字符串
    """
    return hash_password("sha512", data, salt)


def sha512_verify(data, password, salt: str = None):
    result = sha512(data, salt)
    return result == password


if __name__ == '__main__':
    # 不加盐
    print(md5("123456"))
    print(md5_verify("123456", md5("123456")))

    # 加盐
    print(md5("123456", "salt"))
    print(md5_verify("123456", md5("123456", "salt"), "salt"))

    # 不加盐
    print(sha1("abc"))
    print(sha1_verify("123456", sha1("123456")))

    # 加盐
    print(sha1("123456", "salt"))
    print(sha1_verify("123456", sha1("123456", "salt"), "salt"))

    # 不加盐
    print(sha256("abc"))
    print(sha256_verify("123456", sha256("123456")))

    # 加盐
    print(sha256("123456", "salt"))
    print(sha256_verify("123456", sha256("123456", "salt"), "salt"))

    # 不加盐
    print(sha512("abc"))
    print(sha512_verify("123456", sha512("123456")))

    # 加盐
    print(sha512("123456", "salt"))
    print(sha512_verify("123456", sha512("123456", "salt"), "salt"))
