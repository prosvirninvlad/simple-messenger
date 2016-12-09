from messenger.gui.view import View
from messenger.protocol import Response
from messenger.frontend.client import Client
from messenger.frontend.exceptions import *

class Controller:
	def __init__(self):
		self._view = View(self)
		self._client = Client(self)

	def process_conn_response(self, response):
		if response.resl == Response.OKAY:
			self._view.lock(self._view.clear_messages_window)
			self._view.lock(self._view.enable_connected_mode)
		else:
			message_fmt = "Error: Unable to find companion.\n({0})"
			message = message_fmt.format(response.mesg.decode())
			self._view.lock(self._view.run_message_dialog, message)
			self._view.lock(self._view.enable_disconnected_mode)

	def process_dscn_response(self, response):
		message_fmt = "Error: Session suspended by companion.\n({0})"
		message = message_fmt.format(response.mesg.decode())
		self._view.lock(self._view.run_message_dialog, message)
		self._view.lock(self._view.enable_disconnected_mode)

	def process_mesg_response(self, response):
		message = response.mesg.decode()
		if response.resl == Response.OKAY:
			message = message.rstrip("\x00")
			self._view.lock(self._view.push_new_message, message)
		else:
			self._view.lock(self._view.run_message_dialog, message)

	def process_tybe_response(self, response):
		message = "Companion is typing message..."
		self._view.lock(self._view.push_statusbar_message, message)

	def process_tyen_response(self, response):
		self._view.lock(self._view.enable_connected_mode)

	def connect(self, addr, port):
		try:
			self._view.enable_connecting_mode()
			self._client.connect(addr, port)
			self._client.begin_session()
		except SessionRunning:
			self._client.suspend_session()
		except InvalidServerAddress as e:
			message = "Error: Invalid server address: {0}:{1}".format(addr, port)
			self._view.run_message_dialog(message)
			self._view.enable_disconnected_mode()

	def echo(self, message):
		self._client.echo(message)

	def send_message(self, message):
		self._client.send_message(message)

	def send_message_writing_begin(self):
		self._client.send_message_writing_begin()
	
	def run(self):
		self._view.run_view()