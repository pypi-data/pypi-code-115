from cryptography.fernet import Fernet
from passlib.context import CryptContext
from decouple import config


class Verify:
    """ Encrypt and Verify keys
    To generate a Fernet Key use the following and store in a secure place:
    key = Fernet.generate_key().decode('utf-8')
    """
    def __init__(self, key_name: str = 'SECRET_KEY'):
        """ Initialize the class """
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.key = config(key_name)

    def generate_key(self) -> str:
        """ Generate a Fernet key"""
        return Fernet.generate_key().decode('utf-8')

    def encrypt(self, decrypted: str) -> str:
        """ Encrypt a message according to the secret key stored in your env variables
        :param decrypted: String variable to encrypt
        :return: Encrypted string
        """
        return Fernet(self.key).encrypt(decrypted.encode('utf-8')).decode('utf-8')

    def decrypt(self, encrypted: str) -> str:
        """ Decrypt a message according to the secret key stored in your env variables
        :param encrypted: String variable to decrypt
        :return: Decrypted string
        """
        return Fernet(self.key.encode('utf-8')).decrypt(encrypted.encode('utf-8')).decode('utf-8')

    def verify(self, first_encryption: str, second_encryption: str) -> bool:
        """ Comparing encrypted keys and returning the result
        :param first_encryption: First encrypted key to compare
        :param second_encryption: Second encrypted key to compare
        :return: Whether the two encrypted values are equal or not
        """
        return self.decrypt(first_encryption) == self.decrypt(second_encryption)
