import socket
import sys
import argparse
import os
import signal

BUFFER_SIZE = 1024

BSname = 'localhost'

class BS:

	user_commands = ['AUT', 'AUR', 'UPL', 'UPR', 'RSB', 'RBR']
	CS_commands = ['REG', 'RGR', 'UNR', 'UAR', 'LSF', 'LFD', 'LSU', 'LUR', 'DLB', 'DBR']

	def __init__(self, BSport, CSname, CSport):
		self.BSport = BSport
		self.CSname = CSname
		self.CSport = CSport
		self.tcp_socket = None
		self.udp_socket = None
		self.udp_socket2 = None

	# User communication methods
	def userAuthentication(self, connection, username, password):
		filename = "user_" + username + ".txt";
		try:
			#checks if file exists in given path
			if os.path.isfile(filename):
				userFile = open(filename, 'r')
				savedPassword = userFile.read(8)
				userFile.close()

				if savedPassword == password:
					connection.sendall('AUR OK\n'.encode('ascii'))
					self.current_user = username
					print('User: "{}"'.format(self.current_user))
				else:
					connection.sendall('AUR NOK\n'.encode('ascii'))
					print('Incorrect password')

			else:
				connection.sendall('AUR NOK\n'.encode('ascii'))
				print('No such user registered')

		except IOError:
			print('It was not possible to open the requested file')


	def tcp_connect(self):
		try:
			self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error:
			print('BS failed to create TCP socket')
			sys.exit(1)

		# Reuse port
		self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.tcp_socket.bind((BSname, BSport))
		except socket.error:
			print('BS failed to bind with user')
			sys.exit(1)

		self.tcp_socket.listen(5)


	def tcp_accept(self):
		# waits for connection with an user
		print('Waiting for a connection with an user')
		try:
			connection, client_addr = self.tcp_socket.accept()
		except socket.error:
			print('BS failed to establish connection')
			sys.exit(1)

		return connection, client_addr


	def userRequest(self, connection):
		try:
			logged = False

			while True:
				data = connection.recv(BUFFER_SIZE)

				if data:
					fields = data.decode().split()
					command = fields[0]

					if command in self.user_commands:
						print('command')
						if len(fields) == 3:
		 					if command == 'AUT':
								self.userAuthentication(connection, fields[1], fields[2])
								logged = True

						elif len(fields) == 2:
							if logged == True:
								# restore dir
								if command == 'RSB':
									self.restoreDir(connection, fields[1])

								logged = False

								else:
									connection.sendall('ERR\n'.encode('ascii'))
									sys.exit(1)

						#FALTA UPL
						else:
						connection.sendall('ERR\n'.encode('ascii'))
						sys.exit(1)

					else:
						connection.sendall('ERR\n'.encode('ascii'))
						sys.exit(1)
				else:
					break

		except socket.error:
			print('CS failed to trade data with user')
			sys.exit(1)

		finally:
			connection.close()


	def tcp_server(self):
		self.tcp_connect()

		# Runs server indefinitely to attend user requests
		while True:
			connection, client_addr = self.tcp_accept()

			# Avoid child process zombies
			signal.signal(signal.SIGCHLD, signal.SIG_IGN)

			# Creating new process to attend new user requests
			try:
				pid = os.fork()
			except OSError:
				exit('BS was unnable to create child process')

			# Child process attending new user, father process continues waiting for new connections with users
			if pid == 0:
				self.userRequest()


	def udp_client(self):
		try:
			# crete a UDP socket for initial communication with CS (as client)
			try:
				udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			except socket.error:
				print('BS unable to create UDP socket')
			# send data
			udp_socket.sendto(('{} {} {}\n'.format('REG', BSname, BSport)).encode(), CS_server_address)
			# receive response
			data, server = udp_socket.recvfrom(BUFFER_SIZE)
			
			fields = data.decode().split();
			command = fields[0]
			status = fields[1]
			
			if data and command == 'RGR':
				if status == 'OK':
					print(data.decode())
				elif status == 'NOK':
					#fazer algo
					print(ola)
				elif status == 'ERR':
					print('Wrong protocol message received from CS')
					sys.exit(1)
					#repeat information trade to assure everything is received
			else:
				udp_socket.sendto(('REG {} {}\n'.format(BSname, BSport)).encode(), CS_server_address)
				data, server = udp_socket.recvfrom(BUFFER_SIZE).decode()
				print(data)

		except socket.error:
			print('BS failed to trade data')
			sys.exit(1)
		finally:
			udp_socket.close()


	def udp_server(self):
		# Running UDP server to receive requests from CS
		try:
			udp_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		except socket.error:
			print('BS unable to create UDP socket')

		try:
			udp_socket2.bind(BS_server_address)
		except socket.error:
			print('BS failed to bind with CS')
			sys.exit(1)
		try:
			while(True): #TEMOS DE SABER O NUMERO DE BYTES A RECEBER????
				print('BS waiting for a connection with a CS')
				data = udp_socket2.recvfrom(1024).decode()

		except socket.error:
			print('BS failed to trade data with CS')
		finally:
			udp_socket2.close()


if __name__ == "__main__":

	commands = ['REG', 'RGR']

	parser = argparse.ArgumentParser()

	parser.add_argument('-b', action='store', metavar='BSport', type=str, required=False, default=59000,
	help='BSport is the well-known port where the BS server accepts TCP requests\
	from the user application. This is an optional argument. If omitted, it assumes\
	the value 59000.')

	parser.add_argument('-n', action='store', metavar='CSname', type=str, required=False, default='localhost',
	help='CSname is the name of the machine where the central server (CS) runs. This is \
	an optional argument. If this argument is omitted, the CS should be running on the same\
	machine.')

	parser.add_argument('-p', action='store', metavar='CSport', type=int, required=False, default=58018,
	help='CSport is the well-known port where the CS server accepts user requests, in  TCP. \
	This  is  an  optional  argument.  If  omitted,  it  assumes  the  value 58000+GN, where\
	GN is the group number.')

	FLAGS = parser.parse_args()
	BSport = FLAGS.b
	CSname = FLAGS.n
	CSport = FLAGS.p

	CS_server_address = (CSname, CSport)
	BS_server_address = (BSname, BSport)

	bs = BS(BSport, CSname, CSport)

	#BS Server is ready for initiating TCP and UDP servers
	# Avoid child process zombies
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	# Creating new process to run both TCP and UDP servers
	try:
		pid = os.fork()
	except OSError:
		exit('BS was unnable to create child process')

	# Child process running TCP server to receive requests from users
	if pid == 0:
		bs.tcp_server()

	# Parent process running UDP conneection with CS
	else:
		bs.udp_client()

		bs.udp_server()