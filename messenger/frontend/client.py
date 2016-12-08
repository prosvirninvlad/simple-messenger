from time import time
from socket import socket
from select import select
from threading import Thread

from messenger.protocol import Command
from messenger.protocol import Response
from messenger.frontend.exceptions import *

class Client:
	DEFAULT_PORT = 3848
	DEFAULT_ADDRESS = "127.0.0.1"
	ACCEPT_TIMEOUT = 2

	def __init__(self, controller):
		self._sock = None
		self._session = None
		self._session_running = False
		self._controller = controller

		self._message_writing = False
		self._message_writing_time = self._epoch_time()

	def connect(self, addr = DEFAULT_ADDRESS, port = DEFAULT_PORT):
		if self._session_running:
			raise SessionRunning
		try:
			self._sock = socket()
			self._sock.connect((addr, port))
		except ConnectionRefusedError:
			raise InvalidServerAddress

	def disconnect(self):
		self._sock.close()

	def begin_session(self):
		if self._session_running:
			raise SessionRunning
		self._session_running = True
		self._session = Thread(target = self._session_loop)
		self._session.start()

	def end_session(self):
		if not self._session_running:
			raise SessionAlreadyStopped
		self._session_running = False
		self._session.join()

	def _session_loop(self):
		try:
			while True:
				if select_recv(self._sock, timeout = Client.ACCEPT_TIMEOUT):
					self._process_response()
				self._send_message_writing_end()
		except SuspendConnection:
			self._session_running = False
			self.disconnect()

	def _epoch_time(self):
		return int(time())
			
	def _recv(self, recv_len):
		try:
			buf = self._sock.recv(recv_len)
			if buf:
				return buf
			raise ServerDisconnected
		except BrokenPipeError:
			raise ServerDisconnected

	def _send(self, buf):
		try:
			return self._sock.send(buf)
		except BrokenPipeError:
			raise ServerDisconnected

	def _send_command(self, command):
		self._send(command.in_raw())

	def _receive_response(self):
		sign, response = self._recv(Response.SIGN_SIZE), None
		try:
			response = Response.unpack_sign(sign)
			if response.mesg_len:
				response.mesg = self._recv(response.mesg_len)
		except ValueError:
			response = Response(Command.UNKN, Response.FAIL)
		
		return response

	def _process_response(self):
		try:
			response = self._receive_response()
		except ServerDisconnected:
			raise SuspendSession
		response_processor = {
			Command.CONN: self._process_conn_response,
			Command.DSCN: self._process_dscn_response,
			Command.SEND: self._ignore_response,
			Command.MESG: self._process_mesg_response,
			Command.UNKN: self._process_unkn_response,
			Command.ECHO: self._ignore_response,
			Command.TYBE: self._process_tybe_response,
			Command.TYEN: self._process_tyen_response
		}.get(response.iden, self._process_unkn_response)
		response_processor(response)

	def _process_conn_response(self, response):
		self._controller.process_conn_response(response)
		if response.resl == Response.FAIL:
			raise SuspendConnection

	def _process_dscn_response(self, response):
		self._controller.process_dscn_response(response)
		raise SuspendConnection

	def _process_mesg_response(self, response):
		self._controller.process_mesg_response(response)

	def _process_unkn_response(self, response):
		raise SuspendConnection

	def _process_tybe_response(self, response):
		self._controller.process_tybe_response(response)

	def _process_tyen_response(self, response):
		self._controller.process_tyen_response(response)

	def _ignore_response(self, response):
		pass

	def echo(self, message):
		command = Command(Command.ECHO, message.encode())
		self._send_command(command)

	def send_message(self, message):
		command = Command(Command.SEND, message.encode())
		self._send_command(command)

	def send_message_writing_begin(self):
		delta = self._epoch_time() - self._message_writing_time
		if delta > 2:
			self._message_writing = True
			command = Command(Command.TYBE)
			self._send_command(command)
		self._message_writing_time = self._epoch_time()

	def _send_message_writing_end(self):
		delta = self._epoch_time() - self._message_writing_time
		if delta > 1 and self._message_writing:
			self._message_writing = False
			command = Command(Command.TYEN)
			self._send_command(command)

	def suspend_session(self):
		command = Command(Command.DSCN)
		self._send_command(command)

def select_recv(*sock_list, timeout):
	sock_r, sock_e, sock_w = select(
		sock_list,
		[],
		[],
		timeout
	)
	return sock_r