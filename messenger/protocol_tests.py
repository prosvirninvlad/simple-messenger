#! /usr/bin/env python3

import unittest

from protocol import Command
from protocol import Response

class CommandUnpackSignTests(unittest.TestCase):
	def test_empty_sign(self):
		command_sign = b""
		self.assertRaises(ValueError, Command.unpack_sign, command_sign)

	def test_with_wrong_head_size(self):
		command_sign = b"0" * (Command.HEAD_SIZE + 1) + b"SEND"
		self.assertRaises(ValueError, Command.unpack_sign, command_sign)

	def test_with_wrong_head_data(self):
		command_sign = b"G" * Command.HEAD_SIZE + b"SEND"
		self.assertRaises(ValueError, Command.unpack_sign, command_sign)

	def test_with_wrong_iden(self):
		command_sign = b"0" * Command.HEAD_SIZE + b"####"
		self.assertRaises(ValueError, Command.unpack_sign, command_sign)

	def test_with_wrong_iden_size(self):
		command_sign = b"0" * Command.HEAD_SIZE + b"SENDSEND"
		self.assertRaises(ValueError, Command.unpack_sign, command_sign)

	def test_with_correct_sign_a(self):
		command_sign = b"0" * Command.HEAD_SIZE + b"SEND"
		command = Command.unpack_sign(command_sign)
		self.assertTrue(not command.mesg_len and command.iden == "SEND")

	def test_with_correct_sign_b(self):
		command_sign = b"F" * Command.HEAD_SIZE + b"SEND"
		command = Command.unpack_sign(command_sign)
		self.assertTrue(command.mesg_len == 0xFFF and command.iden == "SEND")

class ResponseUnpackTests(unittest.TestCase):
	def test_with_empty_sign(self):
		response_sign = b""
		self.assertRaises(ValueError, Response.unpack_sign, response_sign)

	def test_with_wrong_head_size(self):
		response_sign = b"0" * (Response.HEAD_SIZE + 1) + b"SENDOKAY"
		self.assertRaises(ValueError, Response.unpack_sign, response_sign)
	
	def test_with_wrong_head_data(self):
		response_sign = b"G" * Response.HEAD_SIZE + b"SENDOKAY"
		self.assertRaises(ValueError, Response.unpack_sign, response_sign)

	def test_with_wrong_iden(self):
		response_sign = b"0" * Response.HEAD_SIZE + b"####OKAY"
		self.assertRaises(ValueError, Response.unpack_sign, response_sign)

	def test_with_wrong_resl(self):
		response_sign = b"0" * Response.HEAD_SIZE + b"SEND####"
		self.assertRaises(ValueError, Response.unpack_sign, response_sign)

	def test_with_wrong_iden_size(self):
		response_sign = b"0" * Response.HEAD_SIZE + b"SENDSENDOKAY"
		self.assertRaises(ValueError, Response.unpack_sign, response_sign)

	def test_with_correct_sign_a(self):
		response_sign = b"0" * Response.HEAD_SIZE + b"SENDOKAY"
		response = Response.unpack_sign(response_sign)
		self.assertTrue(all((
			response.iden == "SEND",
			not response.mesg,
			not response.mesg_len,
			response.resl == "OKAY"
		)))

	def test_with_correct_sign_b(self):
		response_sign = b"F" * Response.HEAD_SIZE + b"SENDOKAY"
		response = Response.unpack_sign(response_sign)
		self.assertTrue(all((
			response.iden == "SEND",
			not response.mesg,
			response.mesg_len == 0xFFF,
			response.resl == "OKAY"
		)))

class CommandInstanceTests(unittest.TestCase):
	def test_with_blank_mesg(self):
		command = Command(Command.SEND)
		command_in_raw = b"0" * Command.HEAD_SIZE + b"SEND"
		self.assertEqual(command.in_raw(), command_in_raw)

	def test_with_very_long_mesg(self):
		mesg = b"A" * (Command.MESG_SIZE + 1)
		command = Command(Command.SEND, mesg)
		command_in_raw = b"F" * Command.HEAD_SIZE + b"SEND" + mesg[:-1]
		self.assertEqual(command.in_raw(), command_in_raw)

	def test_with_norm_mesg(self):
		mesg = "DEBUG"
		command = Command(Command.SEND, mesg.encode())
		command_in_raw = ("{0:0%dX}SEND{1}" % Command.HEAD_SIZE).format(
			len(mesg), mesg
		).encode()
		self.assertEqual(command.in_raw(), command_in_raw)

class ResponseInstanceTests(unittest.TestCase):
	def test_with_blank_mesg(self):
		response = Response(Command.SEND)
		response_in_raw = b"0" * Response.HEAD_SIZE + b"SENDOKAY"
		self.assertEqual(response.in_raw(), response_in_raw)

	def test_with_very_long_mesg(self):
		mesg = b"A" * (Response.MESG_SIZE + 1)
		response = Response(Command.SEND, mesg = mesg)
		response_in_raw = b"F" * Response.HEAD_SIZE + b"SENDOKAY" + mesg[:-1]
		self.assertEqual(response.in_raw(), response_in_raw)

	def test_with_norm_mesg(self):
		mesg = "DEBUG"
		response = Response(Command.SEND, mesg = mesg.encode())
		response_in_raw = ("{0:0%dX}SENDOKAY{1}" % Response.HEAD_SIZE).format(
			len(mesg), mesg
		).encode()
		self.assertEqual(response.in_raw(), response_in_raw)

if __name__ == "__main__":
	unittest.main()