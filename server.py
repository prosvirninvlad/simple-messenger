#! /usr/bin/env python3

from messenger.backend.server import Server
from messenger.backend.exceptions import *

def main():
	try:
		print("Enter \"Y\" to suspend server.")
		server = Server()
		server.run()
		while (input() != "y"):
			pass
		server.stop()
	except ServerException as e:
		print(e)

if __name__ == "__main__":
	main()