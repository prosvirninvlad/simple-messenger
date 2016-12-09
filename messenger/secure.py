from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA

class Secure:
	AES_KEY_SIZE = 16
	RSA_KEY_SIZE = 2048

	def __init__(self):
		self.gen_keys()

	def gen_keys(self):
		self._aes_key = Random.new().read(Secure.AES_KEY_SIZE)
		self._aes_handler = AES.new(self._aes_key)
		self._rsa_prv_key = RSA.generate(Secure.RSA_KEY_SIZE)
		self._rsa_pub_key = self._rsa_prv_key.publickey()

	def encode_aes_key(self):
		aes_key, *_ = self._rsa_pub_key.encrypt(self._aes_key, None)
		return aes_key

	def import_pub_rsa_key(self, pub_key):
		self._rsa_pub_key = RSA.importKey(key)

	def export_pub_rsa_key(self):
		return self._rsa_pub_key.exportKey("PEM")

	def encode_message(self, message):
		message_len = 16 * (len(message) // 16 + 1)
		message += "\x00" * (message_len - len(message))
		return self._aes_handler.encrypt(message.encode())

	def decode_message(self, message):
		message = self._aes_handler.decrypt(message).decode()
		return message.rstrip("\x00")

