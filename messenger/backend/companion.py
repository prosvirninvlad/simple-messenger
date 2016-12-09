from select import select

from messenger.secure import * 
from messenger.protocol import Command
from messenger.protocol import Response
from messenger.backend.exceptions import *

class Companion:
	@staticmethod
	def select_recv(*companions, timeout):
		sock_r = [comp._sock for comp in companions]
		sock_r, sock_e, sock_w = select(
			sock_r,
			[],
			[],
			timeout
		)
		return (comp for comp in companions if comp._sock in sock_r)

	def __init__(self, sock, companion = None, aes = None):
		self._aes = aes
		self._sock = sock
		self._companion = companion

	def __del__(self):
		self._sock.close()

	def _recv(self, recv_len):
		try:
			buf = self._sock.recv(recv_len)
			if buf:
				return buf
			raise CompanionDisconnected
		except BrokenPipeError:
			raise CompanionDisconnected

	def _send(self, buf):
		try:
			return self._sock.send(buf)
		except BrokenPipeError:
			raise CompanionDisconnected

	def close(self):
		self._sock.close()

	def send_response(self, response):
		self._send(response.in_raw())

	def receive_command(self):
		sign, command = self._recv(Command.SIGN_SIZE), None
		try:
			command = Command.unpack_sign(sign)
			if command.mesg_len:
				command.mesg = self._recv(command.mesg_len)
		except ValueError:
			command = Command(Command.UNKN)

		return command

	@property
	def companion(self):
		return self._companion

	@companion.setter
	def companion(self, value):
		self._companion = value

	@property
	def has_rsa_key(self):
		return self._has_rsa_key

	@has_rsa_key.setter
	def has_rsa_key(self, value):
		self._has_rsa_key = value

	@property
	def has_aes_key(self):
		return self._has_aes_key

	@has_aes_key.setter
	def has_aes_key(self, value):
		self._has_aes_key = value

	@property
	def aes(self):
		return self._aes

	@aes.setter
	def aes(self, value):
		self._aes = value