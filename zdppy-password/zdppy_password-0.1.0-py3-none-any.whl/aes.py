import base64

from Crypto.Cipher import AES


def pkcs7padding(data):
    bs = AES.block_size
    padding = bs - len(data) % bs
    padding_text = chr(padding) * padding
    return data + padding_text.encode()


def pkcs7unpadding(data):
    lengt = len(data)
    unpadding = data[lengt - 1] if type(data[lengt - 1]) is int else ord(data[lengt - 1])
    return data[0:lengt - unpadding]


class Aes:
    """
        兼容Python和Golang的AES加密算法
        """

    def __init__(self, key: str = "_ZhangDapeng520%"):
        self.key = key.encode()

    def encrypt(self, data):
        """
        AES 加密， 加密模式ECB，填充：pkcs7padding，密钥长度：256
        :param data:
        :return:
        """
        data = pkcs7padding(data)
        cipher = AES.new(self.key, AES.MODE_ECB)
        encrypted = cipher.encrypt(data)
        return base64.b64encode(encrypted)

    def decrypt(self, data):
        """
        AES解密
        :param data: 要解密的数据
        :return: 解密后的数据
        """
        data = base64.b64decode(data)
        cipher = AES.new(self.key, AES.MODE_ECB)
        decrypted = cipher.decrypt(data)
        decrypted = pkcs7unpadding(decrypted)
        return decrypted.decode()


if __name__ == '__main__':
    aes = Aes()
    res = aes.encrypt(b'{"cmd": 3000, "msg": "ok"}').decode(encoding='utf-8')
    print(res)
    print(aes.decrypt(res))

    # 从go复制过来的
    print(aes.decrypt("0qg69fOjmE0oR59muWdXoWhr5d4Z0XyQaC69684mAsw="))
