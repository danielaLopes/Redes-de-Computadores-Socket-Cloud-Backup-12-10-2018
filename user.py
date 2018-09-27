import socket
import sys
import argparse
import os

BUFFER_SIZE = 1024

class User:

	commands = ['login', 'deluser', 'backup', 'restore', 'dirlist', 'filelist', 'delete', 'logout', 'exit']
	replies = ['AUT', 'AUR', 'DLU', 'DLR', 'BCK', 'BKR', 'RST', 'LSD', 'LDR', 'LSF', 'LFD', 'DEL', 'DDR']

	def __init__(self, CSname, CSport):
		self.TCPsocket = None
		self.username = None
		self.password = None
		self.CSname = CSname
		self.CSport = CSport

	def set_username(self, username):
		self.username = username

	def set_password(self, password):
		self.password = password

	def connect(self):
		try:
			self.TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error:
			print('User failed to create socket')
			sys.exit(1)

		try:
			self.TCPsocket.connect((CSname, CSport))
		except socket.error:
			print('User failed to connect')
			sys.exit(1)

	def sendData(self, data):
		try:
			self.TCPsocket.sendall(data.encode('ascii'))
		except socket.error:
			print('User failed to send data to Central Server')
			sys.exit(1)

	def receiveData(self, n_bytes):
		try:
			return self.TCPsocket.recv(n_bytes)
		except socket.error:
			print('User failed to receive data from Central Server')
			sys.exit(1)

	def closeSocket(self):
		self.TCPsocket.close()


if __name__ == "__main__":

	# Parse arguments
	parser = argparse.ArgumentParser()

	parser.add_argument('-n', action='store', metavar='CSname', type=str, required=False, default='194.210.231.52',
	help='CSname is the name of the machine where the central server (CS) runs. This is \
	an optional argument. If this argument is omitted, the CS should be running on the same\
	machine.')

	parser.add_argument('-p', action='store', metavar='CSport', type=int, required=False, default=58018,
	help='CSport is the well-known port where the CS server accepts user requests, in  TCP. \
	This  is  an  optional  argument.  If  omitted,  it  assumes  the  value 58000+GN, where\
	GN is the group number.')

	FLAGS = parser.parse_args()
	CSname = FLAGS.n
	CSport = FLAGS.p

	user = User(CSname, CSport)

	# Handle input
	input = input()
	fields = input.split()

	if fields[0] in user.commands:
		user.connect()
		if fields[0] == 'login':
			username = fields[1]
			password = fields[2]
			if len(username) == 5 and int(username) and len(password) == 8 and str.isalnum(password):
				user.sendData(f'{user.replies[0]} {username} {password}')
				print(user.receiveData(1024).decode())
				user.set_username(username)
				user.set_password(password)
				user.closeSocket()
		#elif fields[0] == 'exit':
        	#disconnect()
            #os._exit(0)
