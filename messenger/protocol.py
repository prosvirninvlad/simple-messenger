import re

class Command:
	DSCN = "DSCN"
	ECHO = "ECHO"
	UNKN = "UNKN"
	CONN = "CONN"
	SEND = "SEND"
	MESG = "MESG"
	SECR = "SECR"
	TYBE = "TYBE"
	TYEN = "TYEN"

	HEAD_SIZE = 3
	IDEN_SIZE = 4
	MESG_SIZE = 0xFFF
	SIGN_SIZE = sum((
		HEAD_SIZE,
		IDEN_SIZE,
	))

	regex_raw = r"([\da-fA-F]{%d})([a-zA-Z]{%d})" % (
		HEAD_SIZE,
		IDEN_SIZE
	)
	regex = re.compile(regex_raw)

	@staticmethod
	def unpack_sign(sign):
		sign = sign.decode()
		if len(sign) != Command.SIGN_SIZE:
			message = "Invalid command signature length."
			raise ValueError(message)

		regex_res = Command.regex.match(sign)
		if not regex_res:
			message = "Unable to recognize command."
			raise ValueError(message)
		
		head, iden = regex_res.groups()
		return Command(iden, mesg_len = int(head, 16))

	def __init__(self, iden, mesg = b"", mesg_len = 0):
		self._iden = iden
		self._mesg = mesg[:Command.MESG_SIZE]
		self._mesg_len = mesg_len if mesg_len else len(self._mesg)

	@property
	def iden(self):
		return self._iden

	@property
	def mesg(self):
		return self._mesg

	@property
	def mesg_len(self):
		return self._mesg_len

	@mesg.setter
	def mesg(self, mesg):
		self._mesg = mesg

	def in_raw(self):
		command_fmt = "{0:0%dX}{1}" % Command.HEAD_SIZE
		return b"".join((
			command_fmt.format(self._mesg_len, self._iden).encode(), 
			self._mesg
		))

class Response(Command):
	OKAY = "OKAY"
	FAIL = "FAIL"

	HEAD_SIZE = 3
	IDEN_SIZE = 4
	RESL_SIZE = 4
	MESG_SIZE = 0xFFF
	SIGN_SIZE = sum((
		HEAD_SIZE,
		IDEN_SIZE,
		RESL_SIZE
	))

	regex_raw = Command.regex_raw + r"({0}|{1})".format(OKAY, FAIL)
	regex = re.compile(regex_raw)

	@staticmethod
	def unpack_sign(sign):
		sign = sign.decode()
		if len(sign) != Response.SIGN_SIZE:
			message = "Invalid response signature length."
			raise ValueError(message)

		regex_res = Response.regex.match(sign)
		if not regex_res:
			message = "Unable to recognize response."
			raise ValueError(message)
		
		head, iden, resl = regex_res.groups()
		return Response(iden, resl, mesg_len = int(head, 16))

	def __init__(self, iden, resl = OKAY, mesg = b"", mesg_len = None):
		super().__init__(iden, mesg, mesg_len)
		self._resl = resl

	@property
	def resl(self):
		return self._resl

	def in_raw(self):
		response_fmt = "{0:0%dX}{1}{2}" % Response.HEAD_SIZE
		return b"".join((
			response_fmt.format(self._mesg_len, self._iden, self._resl).encode(), 
			self._mesg
		))