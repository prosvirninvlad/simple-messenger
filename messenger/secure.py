from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA

class Rsa:
	KEY_SIZE = 2048

	def __init__(self):
		self.gen_key()

	def gen_key(self):
		self._prv_key = RSA.generate(Rsa.KEY_SIZE)
		self._pub_key = self._prv_key.publickey()

	def encode(self, buf):
		buf, *_ = self._pub_key.encrypt(buf, None)
		return buf

	def decode(self, buf):
		return self._prv_key.decrypt(buf)

	def import_pub_key(self, pub_key):
		self._pub_key = RSA.importKey(pub_key)

	def export_pub_key(self):
		return self._pub_key.exportKey("PEM")

class Aes:
	KEY_SIZE = 16

	def __init__(self):
		self.gen_key()

	def gen_key(self):
		self._key = Random.new().read(Aes.KEY_SIZE)
		self._handler = AES.new(self._key)

	def encode(self, buf):
		buf_len = 16 * (len(buf) // 16 + 1)
		buf += b"\x00" * (buf_len - len(buf))
		return self._handler.encrypt(buf)

	def decode(self, buf):
		return self._handler.decrypt(buf)

	def import_key(self, key):
		self._key = key
		self._handler = AES.new(key)

	def export_key(self):
		return self._key