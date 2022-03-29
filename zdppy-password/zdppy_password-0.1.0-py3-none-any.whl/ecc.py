import binascii

from tinyec import registry
from Crypto.Cipher import AES
import hashlib
import secrets
import base64
import json


class Ecc:
    def __init__(self):
        self.curve = registry.get_curve('brainpoolP256r1')
        self.private_key = secrets.randbelow(self.curve.field.n)
        self.public_key = self.private_key * self.curve.g

    @staticmethod
    def __encrypt_aes_gcm(data, secret_key):
        aes_cipher = AES.new(secret_key, AES.MODE_GCM)
        ciphertext, auth_tag = aes_cipher.encrypt_and_digest(data)
        return ciphertext, aes_cipher.nonce, auth_tag

    @staticmethod
    def __decrypt_aes_gcm(ciphertext, nonce, auth_tag, secret_key):
        aes_cipher = AES.new(secret_key, AES.MODE_GCM, nonce)
        plaintext = aes_cipher.decrypt_and_verify(ciphertext, auth_tag)
        return plaintext

    @staticmethod
    def __ecc_point_to_256_bit_key(point):
        sha = hashlib.sha256(int.to_bytes(point.x, 32, 'big'))
        sha.update(int.to_bytes(point.y, 32, 'big'))
        return sha.digest()

    def encrypt(self, data):
        """
        ecc加密
        :param data: 要加密的数据
        :return: 加密后的数据
        """
        cipher_text_private_key = secrets.randbelow(self.curve.field.n)
        shared_ecc_key = cipher_text_private_key * self.public_key
        secret_key = self.__ecc_point_to_256_bit_key(shared_ecc_key)
        ciphertext, nonce, auth_tag = self.__encrypt_aes_gcm(data, secret_key)
        cipher_text_public_key = cipher_text_private_key * self.curve.g

        # 转换为加密字符串
        print("============", ciphertext, type(ciphertext))
        # 转换为16进制
        ciphertext16 = binascii.hexlify(ciphertext)
        print("============", ciphertext16)
        print("============", ciphertext16.decode())
        _data = ciphertext, nonce, auth_tag, cipher_text_public_key
        return _data

    def decrypt(self, data):
        """
        ecc解密
        :param data: 要解密的数据
        :return: 解密后的数据
        """

        (cipher_text, nonce, auth_tag, ciphertext_public_key) = data
        shared_ecc_ey = self.private_key * ciphertext_public_key
        secret_key = self.__ecc_point_to_256_bit_key(shared_ecc_ey)
        _data = self.__decrypt_aes_gcm(cipher_text, nonce, auth_tag, secret_key)
        return _data


if __name__ == '__main__':
    data = b'Text to be encrypted by ECC public key and decrypted by its corresponding ECC private key'
    print("original data:", data)

    # 创建私钥
    ecc = Ecc()
    print("私钥：", ecc.private_key)

    # 创建公钥
    print("公钥：", ecc.public_key)

    # 加密内容
    encrypted_data = ecc.encrypt(data)
    print("encrypted data:", encrypted_data)

    # 解密内容
    decrypted_data = ecc.decrypt(encrypted_data)
    print("decrypted data:", decrypted_data)
