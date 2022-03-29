import base64


def encode(data):
    """
    base64编码
    :param data: 要编码的数据
    :return: 编码后的数据
    """
    t = base64.b64encode(data.encode()).decode()
    return t


def decode(data):
    """
    base64解码
    :param data: 要解码的数据
    :return: 解码后的数据
    """
    t = base64.b64decode(data.encode()).decode()
    return t


if __name__ == '__main__':
    d = "abc123张大鹏"
    print(encode(d))
    print(decode(encode(d)))
