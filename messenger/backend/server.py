from socket import socket
from select import select
from threading import Thread

from messenger.secure import *
from messenger.protocol import Command
from messenger.protocol import Response
from messenger.backend.companion import Companion
from messenger.backend.exceptions import *

class Server:
	DEFAULT_PORT = 3848
	DEFAULT_ADDRESS = "127.0.0.1"
	ACCEPT_TIMEOUT = 8
	MAX_CLIENTS = 32

	def __init__(self):
		self._sock = None
		self._sessions = set()
		self._thread = None
		self._thread_running = False

	def run(self, addr = DEFAULT_ADDRESS, port = DEFAULT_PORT):
		if self._thread_running:
			raise ServerAlreadyRunning

		self._configure(addr, port)
		self._thread_running = True
		self._thread = Thread(target = self._loop)
		self._thread.start()

	def stop(self):
		if not self._sock:
			raise ServerInvalidConfiguration

		if not self._thread_running:
			raise ServerAlreadyStopped

		self._thread_running = False
		for session in self._sessions:
			session.join()
		self._sessions.clear()

		self._thread.join()
		self._sock.close()

	def is_running(self):
		return self._thread_running

	def _configure(self, addr, port):
		try:
			self._sock = socket()
			self._sock.bind((addr, port))
			self._sock.listen(Server.MAX_CLIENTS)
		except OSError as e:
			self._sock.close()
			raise ServerException(str(e))

	def _loop(self):
		companion_a = companion_b = None
		while self._thread_running:
			if select_recv(self._sock, timeout = Server.ACCEPT_TIMEOUT):
				sock, addr = self._sock.accept()
				if companion_a:
					companion_b = Companion(sock)
				else:
					companion_a = Companion(sock)
				if (companion_a and companion_b):
					self._begin_session(companion_a, companion_b)
					companion_a = companion_b = None
			elif companion_a:
				process_conn_command(companion_a)
				companion_a.close()
				companion_a = None

	def _begin_session(self, companion_a, companion_b):
		companion_a.companion = companion_b
		companion_b.companion = companion_a
		process_conn_command(companion_a)
		process_conn_command(companion_b)
		
		session = Thread(target = self._session_loop, 
			args = (companion_a, companion_b))
		self._sessions.add(session)
		session.start()

	def _session_loop(self, companion_a, companion_b):
		try:
			while self._thread_running:
				for companion in Companion.select_recv(
					companion_a, companion_b, timeout = Server.ACCEPT_TIMEOUT):
					process_command(companion)
		except SuspendSession:
			pass
		companion_a.close()
		companion_b.close()

def process_command(companion):
	try:
		command = companion.receive_command()
	except CompanionDisconnected:
		suspend_session(companion.companion)
	command_processor = {
		Command.CONN: process_conn_command,
		Command.DSCN: process_dscn_command,
		Command.SEND: process_send_command,
		Command.ECHO: process_echo_command,
		Command.TYBE: process_tybe_command,
		Command.TYEN: process_tyen_command,
		Command.AESK: process_aesk_command,
		Command.UNKN: process_unkn_command
	}.get(command.iden, process_unkn_command)
	command_processor(companion, command)

def process_conn_command(companion):
	response = None
	if companion.companion:
		response_message = b"CHAT_SUCCESSFULLY_STARTED" 
		response = Response(Command.CONN, mesg = response_message)
	else:
		response_message = b"COMPANION_ACCEPT_TIME_EXPIRED"
		response = Response(Command.CONN, Response.FAIL, response_message)
	companion.send_response(response)

def process_dscn_command(companion, command):
	suspend_session(companion)
	suspend_session(companion.companion)
	raise SuspendSession

def process_send_command(companion, command):
	message = companion.aes.decode(command.mesg)
	message = companion.companion.aes.encode(message)
	response = Response(Command.SEND)
	companion.send_response(response)
	response = Response(Command.MESG, mesg = message)
	companion.companion.send_response(response)

def process_echo_command(companion, command):
	response = Response(Command.ECHO, mesg = command.mesg)
	companion.send_response(response)

def process_tybe_command(companion, command):
	response = Response(Command.TYBE)
	companion.companion.send_response(response)

def process_tyen_command(companion, command):
	response = Response(Command.TYEN)
	companion.companion.send_response(response)

def process_aesk_command(companion, command):
	response = None
	if companion.aes:
		response_message = b"AES_SECURE_ALREADY_ENABLED"
		response = Response(Command.AESK, Response.FAIL, response_message)
	else:
		aes_handler = Aes()
		companion.aes = aes_handler
		response_message = Rsa.quick_encode(command.mesg, aes_handler.export_key())
		response = Response(Command.AESK, mesg = response_message)
	companion.send_response(response)

def process_unkn_command(companion, command):
	response_message = b"ERROR_UNKNOWN_COMMAND"
	response = Response(Command.UNKN, Response.FAIL, response_message)
	companion.send_response(response)

def suspend_session(companion):
	try:
		response_mesg = b"CHAT_STOPPED_BY_COMPANION"
		response = Response(Command.DSCN, mesg = response_mesg)
		companion.send_response(response)
	except CompanionDisconnected:
		pass

def select_recv(*sock_list, timeout):
	sock_r, sock_e, sock_w = select(
		sock_list,
		[],
		[],
		timeout
	)
	return sock_r