import socket
import sys
import argparse
import os

BUFFER_SIZE = 1024

class User:

	commands = ['login', 'deluser', 'backup', 'restore', 'dirlist', 'filelist', 'delete', 'logout', 'exit']
	CS_replies = ['AUT', 'AUR', 'DLU', 'DLR', 'BCK', 'BKR', 'RST', 'LSD', 'LDR', 'LSF', 'LFD', 'DEL', 'DDR']

	current_user = None # username: password

	def __init__(self, CSname, CSport):
		self.TCPsocket = None
		self.CSname = CSname
		self.CSport = CSport

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
			return self.TCPsocket.recv(n_bytes).decode()
		except socket.error:
			print('User failed to receive data from Central Server')
			sys.exit(1)

	#def processCSresponse(self, CS_response, status):


	def closeSocket(self):
		self.TCPsocket.close()


if __name__ == "__main__":

	# Parse arguments
	parser = argparse.ArgumentParser()

	parser.add_argument('-n', action='store', metavar='CSname', type=str, required=False, default='localhost',
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
	print(CSname)

	user.connect()
	# Handle input
	while True:
		fields = input().split()
		input_command = fields[0]
		# verifies if the input command exists
		if input_command in user.commands:
			if input_command == 'login':
				username = fields[1]
				password = fields[2]
				# verify user input
				if len(username) == 5 and int(username) and len(password) == 8 and str.isalnum(password):
					user.sendData('{} {} {}'.format(user.CS_replies[0], username, password)) # AUT
					data = user.receiveData(1024)
					fields = data.split()
					CS_response = fields[0]
					status = fields[1]

					if CS_response == 'AUR':
						if(status == 'NEW'):
							print('User "{}" created'.format(username))
							user.current_user = {username: password}
						elif(status == 'OK'):
							user.current_user = {username: password}
						elif(status == 'NOK'):
							print('Incorrect password')
						else:
							print('Wrong protocol message received from CS')
							sys.exit(1)
					else:
						print('Wrong protocol message received from CS')
						sys.exit(1)

			elif input_command == 'deluser':
				user.sendData(user.CS_replies[2]) # DLU
				data = user.receiveData(1024)
				fields = data.split()
				CS_response = fields[0]
				status = fields[1]

				if CS_response == 'DLR':
					if(status == 'OK'):
						user.current_user = None
						print('User successfully deleted')
					elif(status == 'NOK'):
						print('User cannot be deleted because it still has information stored')
					else:
						print('Wrong protocol message received from CS')
						sys.exit(1)
				else:
					print('Wrong protocol message received from CS')
					sys.exit(1)

			elif input_command == 'exit':
				user.closeSocket()
				os._exit(0)
		else:
			print('Comando invalido')
