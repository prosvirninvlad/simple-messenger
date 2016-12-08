import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from datetime import datetime

class View(Gtk.Window):
	def __init__(self, controller):
		title = "Simple Messenger"
		size = (480, 480)

		Gtk.Window.__init__(self, title = title)
		self.set_default_size(*size)
		self.connect("delete-event", Gtk.main_quit)

		self._controller = controller
		self._init_childs()

	def run_view(self):
		self.enable_disconnected_mode()
		Gdk.threads_init()
		self.show_all()
		Gtk.main()

	def _init_childs(self):
		self._make_main_container()
		self._make_messages_view()
		self._make_controls_container()
		self._make_message_entry()
		self._make_connection_controls()
		self._make_connection_config_menu()
		self._make_statusbar()

	def _make_main_container(self):
		self._main_container = Gtk.Box(orientation = Gtk.Orientation.VERTICAL,
			spacing = 10)
		self.add(self._main_container)

		change_margins(self._main_container, 10)

	def _make_messages_view(self):
		self._messages_view = Gtk.TextView()
		self._messages_view_buf = self._messages_view.get_buffer()
		messages_view = make_scrollable(self._messages_view)
		messages_view = place_in_frame(messages_view)
		self._main_container.pack_start(messages_view, True, True, 0)

		self._messages_view.set_wrap_mode(Gtk.WrapMode.WORD)
		self._messages_view.set_cursor_visible(False)
		self._messages_view.set_editable(False)

	def _make_controls_container(self):
		self._controls_container = Gtk.Box(
			orientation = Gtk.Orientation.HORIZONTAL,
			spacing = 10
		)
		self._main_container.pack_start(self._controls_container, False, True, 0)

	def _make_message_entry(self):
		self._message_entry = Gtk.Entry()
		self._message_entry.connect("activate", self._send_clicked)
		self._message_entry.connect("changed", self._message_entry_changed)
		self._message_entry.set_placeholder_text("Type your message here. Press \"Enter\" to send message.")
		self._controls_container.pack_start(self._message_entry, True, True, 0)

	def _make_connection_controls(self):
		controls_box = Gtk.ButtonBox(orientation = Gtk.Orientation.HORIZONTAL)
		self._controls_container.pack_end(controls_box, False, True, 0)
		controls_box.set_layout(Gtk.ButtonBoxStyle.EXPAND)

		self._send = Gtk.Button.new_with_label("Send")
		self._send.connect("clicked", self._send_clicked)
		controls_box.add(self._send)

		self._change_connection = Gtk.Button.new_with_label("Connect")
		self._change_connection.connect("clicked", self._change_connection_clicked)
		controls_box.add(self._change_connection)

		self._connection_config = Gtk.Button.new_with_label("Settings")
		self._connection_config.connect("clicked", self._connection_config_clicked)
		controls_box.add(self._connection_config)

	def _make_connection_config_menu(self):
		self._config_menu = Gtk.Popover.new(self._connection_config)
		config_menu_container = Gtk.Box(
			orientation = Gtk.Orientation.VERTICAL,
			spacing = 10
		)
		change_margins(config_menu_container, 10)
		self._config_menu.add(config_menu_container)

		server_addr = Gtk.Label("Address")
		server_addr.set_halign(Gtk.Align.START)
		config_menu_container.pack_start(server_addr, False, True, 0)
		self._server_addr_entry = Gtk.Entry()
		self._server_addr_entry.set_text("127.0.0.1")
		config_menu_container.pack_start(self._server_addr_entry, False, True, 0)

		server_port = Gtk.Label("Port")
		server_port.set_halign(Gtk.Align.START)
		config_menu_container.pack_start(server_port, False, True, 0)
		self._server_port_entry = Gtk.Entry()
		self._server_port_entry.set_text("3848")
		config_menu_container.pack_start(self._server_port_entry, False, True, 0)

	def _make_statusbar(self):
		statusbar_separator = Gtk.Separator(
			orientation = Gtk.Orientation.HORIZONTAL)
		self._main_container.pack_start(statusbar_separator, False, True, 0)

		self._statusbar = Gtk.Label("Ready")
		self._statusbar.set_halign(Gtk.Align.START)
		self._main_container.pack_end(self._statusbar, False, True, 0)

	def _send_clicked(self, sender):
		message = self._message_entry.get_text()
		if message:
			self._controller.send_message(message)
			self._push_own_message(message)
			self._message_entry.set_text("")
		else:
			self.run_message_dialog("Unable to send blank message.")

	def _change_connection_clicked(self, sender):
		try:
			server_addr = str(self._server_addr_entry.get_text())
			server_port = int(self._server_port_entry.get_text())
			self._controller.connect(server_addr, server_port)
		except ValueError as e:
			self._config_menu.show_all()

	def _connection_config_clicked(self, sender):
		self._config_menu.show_all()

	def _message_entry_changed(self, sender):
		if self._message_entry.get_text_length():
			self._controller.send_message_writing_begin()

	def _push_message(self, author, message):
		message_time = datetime.strftime(datetime.now(), "%H:%M:%S")
		message_fmt = "{0} ({1}):\n{2}\n\n".format(author, message_time, message)
		self._messages_view_buf.insert_at_cursor(message_fmt)

	def _push_own_message(self, message):
		self._push_message("You", message)

	def run_message_dialog(self, message):
		message_dialog = Gtk.MessageDialog(
			self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
			message
		)
		message_dialog.run()
		message_dialog.destroy()

	def push_new_message(self, message):
		self._push_message("Companion", message)

	def enable_connected_mode(self):
		self.push_statusbar_message("Click \"Send\" to send message.")
		self._change_connection.set_label("Disconnect")
		self._connection_config.set_sensitive(False)
		self._change_connection.set_sensitive(True)
		self._message_entry.set_sensitive(True)
		self._send.set_sensitive(True)

	def enable_disconnected_mode(self):
		self.push_statusbar_message("Click \"Connect\" to find companion.")
		self._change_connection.set_label("Connect")
		self._connection_config.set_sensitive(True)
		self._change_connection.set_sensitive(True)
		self._message_entry.set_sensitive(False)
		self._send.set_sensitive(False)

	def enable_connecting_mode(self):
		self.push_statusbar_message("Looking for companion.")
		self._change_connection.set_sensitive(False)
		self._connection_config.set_sensitive(False)
		self._message_entry.set_sensitive(False)
		self._send.set_sensitive(False)

	def push_statusbar_message(self, message):
		self._statusbar.set_label(message)

	def lock(self, method, *args):
		Gdk.threads_enter()
		method(*args)
		Gdk.threads_leave()

def change_margins(widget, margin):
	widget.set_margin_top(margin)
	widget.set_margin_end(margin)
	widget.set_margin_start(margin)
	widget.set_margin_bottom(margin)

def place_in_frame(widget):
	frame = Gtk.Frame(label = None)
	frame.add(widget)
	return frame

def make_scrollable(widget):
	scrolled_window = Gtk.ScrolledWindow()
	scrolled_window.add(widget)
	return scrolled_window