from Crypto.Cipher import AES
import json, base64, hashlib

BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)

class Encryption:
    def __init__(self, iv_key, secret_key):
        self.iv_key = iv_key
        self.secret_key = secret_key
        self.algorithm = AES.MODE_CBC

    def encrypt(self, payload):

        secret = hashlib.sha256(self.secret_key.encode()).hexdigest()[:32]
        iv = hashlib.sha256(self.iv_key.encode()).hexdigest()[:16]

        cipher = AES.new(secret.encode('utf-8'), self.algorithm, iv.encode('utf-8'))
        crypt = cipher.encrypt(pad(payload).encode())

        return base64.b64encode(base64.b64encode(crypt)).decode('utf-8')
