from cryptography.fernet import Fernet


class ParamEncryption:
    encryption_class = Fernet

    def __init__(self, key):
        self.key = key
        self.crypt = self.encryption_class(self.key)

    def encrypt_params(self, param_string):
        return self.crypt.encrypt(param_string)

    def decrypt_params(self, encrypted_params):
        return self.crypt.decrypt(str(encrypted_params))
