import os
import base64

from Crypto import Random
from zdppy_log import Log
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto.Signature import PKCS1_v1_5 as PKCS1_signature
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher


def get_key(key_path: str):
    if not os.path.exists(key_path):
        return

    with open(key_path) as f:
        data = f.read()
        key = RSA.importKey(data)

    return key


def encrypt(
        data: str,
        public_key_path: str = "public_key.pem",
):
    public_key = get_key(public_key_path)
    cipher = PKCS1_cipher.new(public_key)
    encrypt_text = base64.b64encode(cipher.encrypt(bytes(data.encode("utf8"))))
    return encrypt_text.decode('utf-8')


def decrypt(
        data: str,
        private_key_path: str = "private_key.pem",
):
    private_key = get_key(private_key_path)
    cipher = PKCS1_cipher.new(private_key)
    back_text = cipher.decrypt(base64.b64decode(data), 0)
    return back_text.decode('utf-8')


def signer(data, private_key_path: str = "private.pem"):
    private_key = get_key(private_key_path)
    signer_obj = PKCS1_signature.new(private_key)
    digest = SHA.new()
    digest.update(data.encode("utf8"))
    sign = signer_obj.sign(digest)
    signature = base64.b64encode(sign)
    signature = signature.decode('utf-8')
    return signature


def verify(text, signature, public_key_path: str = "public.pem"):
    public_key = get_key(public_key_path)
    verifier = PKCS1_signature.new(public_key)
    digest = SHA.new()
    digest.update(text.encode("utf8"))
    return verifier.verify(digest, base64.b64decode(signature))


class Rsa:
    def __init__(
            self,
            key_length: int = 1024,
            log_file_path: str = "logs/zdppy/zdppy_password.log",
            debug: bool = True,
    ):
        """
        初始化Rsa加密对象
        :param key_length: 生成key的长度，长度越长越安全，但是速度也越慢。必须大于或等于1024。
        """
        random_generator = Random.new().read
        self.rsa = RSA.generate(key_length, random_generator)
        self.log = Log(log_file_path=log_file_path, debug=debug)
        self.get_key = get_key  # 获取key
        self.decrypt = decrypt  # 加密
        self.encrypt = encrypt  # 解密
        self.signer = signer  # 签名
        self.verify = verify  # 校验

    def generate_private_key(
            self,
            private_key_path: str = None,
            is_to_str: bool = True,
    ):
        """
        生成RSA私钥
        :param is_to_str: 是否转换为字符串
        :param private_key_path: 私钥文件保存的路径
        :return: 私钥
        """
        # 如果已存在，读取返回
        if private_key_path is not None and os.path.exists(private_key_path):
            with open(private_key_path, "rb") as f:
                result = f.read()
                if is_to_str:
                    result = result.decode()
                return result

        # 生成私钥
        result = self.rsa.exportKey()

        # 保存
        if private_key_path is not None and isinstance(private_key_path, str):
            with open(private_key_path, "wb") as f:
                f.write(result)

        # 转换为字符串
        if is_to_str:
            result = result.decode('utf-8')

        # 返回结果
        return result

    def generate_public_key(
            self,
            public_key_path: str = None,
            is_to_str: bool = True,
    ):
        """
        生成RSA公钥
        :param is_to_str: 是否转换为字符串
        :param public_key_path: 公钥文件保存的路径
        :return: 公钥
        """
        # 如果已存在，读取返回
        if public_key_path is not None and os.path.exists(public_key_path):
            with open(public_key_path, "rb") as f:
                result = f.read()
                if is_to_str:
                    result = result.decode()
                return result

        # 生成公钥
        result = self.rsa.publickey().exportKey()

        # 保存
        if public_key_path is not None and isinstance(public_key_path, str):
            with open(public_key_path, "wb") as f:
                f.write(result)

        # 转换为字符串
        if is_to_str:
            result = result.decode('utf-8')

        # 返回结果
        return result
