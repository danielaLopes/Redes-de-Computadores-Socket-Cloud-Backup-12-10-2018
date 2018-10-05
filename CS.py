import socket
import sys
import argparse
import os
import multiprocessing
import signal

BUFFER_SIZE = 1024

CSname = 'localhost'#socket.gethostname()


class CS:

	BS_commands = ['REG','RGR', 'UNR', 'UAR', 'LSF', 'LFD N', 'LSU', 'LUR', 'DLB', 'DBR']
	user_commands = ['AUT', 'AUR', 'DLU', 'DLR', 'BCK', 'BKR', 'RST', 'LSD', 'LDR', 'LSF', 'LFD', 'DEL', 'DDR']

	registered_users = {} # username: password
	current_user = None #username

	
	def __init__(self, CSport):
		self.CSport = CSport
	

	def createBackupFile(self):
		# Creating the backup_list file
		f = open("backup_list.txt", "w")
		f.write("RC\n")
		f.write("OLA\n")
		f.close()


	# Interface related methods
	def userAuthentication(self, connection, username, password):
		if username in self.registered_users:
			if password == self.registered_users[username]:
				connection.sendall('AUR OK\n'.encode('ascii'))
				self.current_user = username
				print('User: "{}"'.format(self.current_user))
			else:
				connection.sendall('AUR NOK\n'.encode('ascii'))
				print('Incorrect password')
		else:
			print('username: "{}"'.format(username))
			connection.sendall('AUR NEW\n'.encode('ascii'))
			self.registered_users[username] = password
			self.current_user = username
			print('New user: "{}"'.format(self.current_user))

			for x, y in self.registered_users.items():
				print('username: {} pass: {}'.format(username, password))

	
	def delUser(self, connection):
		print(self.current_user)
		#if (current_user.information().isempty()):
		try:
			del self.registered_users[self.current_user]
			self.current_user = None
			connection.sendall('DLR OK\n'.encode('ascii'))
		except KeyError:
			print('This user is not registered')
		#else:
			#connection.sendall('DLR NOK\n'.encode('ascii')


	def dirList(self, connection):
		f = open("backup_list.txt", "r")
		N = 0
		dirnames = ""

		for line in f:
			N += 1
			dirnames = dirnames + " " + line

		message = "LDR " + str(N) + " " + dirnames + "\n"
		connection.sendall(message.encode('ascii'))



	def udp_connect(self):
		try:
			udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		except socket.error:
			print('CS failed to create UDP socket')
			sys.exit(1)

		# Reuse port
		udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			udp_socket.bind((CSname, CSport))
		except socket.error:
			print('CS failed to bind with BS')
			sys.exit(1)

		return udp_socket



	def udp_server(self):
		udp_socket = self.udp_connect()

		try:
			# Runs server indefinitely to attend BS registrations
			while True:
				print('Waiting for a connection with a BS')
				data, client_address = udp_socket.recvfrom(BUFFER_SIZE)
					
				if data:
					fields = data.decode().split()

					if(fields[0] == 'REG'):
						IPBS = fields [1]
						portBS = fields [2]
						print('{} {} {}'.format(fields[0], IPBS, portBS))
						udp_socket.sendto('RGR OK\n'.encode('ascii'), client_address)

					#QUANDO FAZER RGR ERR?????
					else:
						udp_socket.sendto('RGR NOK\n'.encode('ascii'), client_address)

		except socket.error:
			print('CS failed to trade data with BS')
			sys.exit(1)

		finally:
			udp_socket.close()


	def tcp_connect(self):
		try:
			tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error:
			print('CS failed to create TCP socket')
			sys.exit(1)

		# Reuse port
		tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	

		try:
			tcp_socket.bind((CSname, CSport))
		except socket.error:
			print('CS failed to bind with user')
			sys.exit(1)

		tcp_socket.listen(5)

		return tcp_socket


	def tcp_accept(self, tcp_socket):
		# waits for connection with an user
		print('Waiting for a connection with an user')
		try:
			connection, client_addr = tcp_socket.accept()
		except socket.error:
			print('CS failed to establish connection')
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
						if command == 'AUT':
							self.userAuthentication(connection,fields[1], fields[2])
							logged = True

						#LEMBRAR DE NO FIM DE CADA SESSAO TCP APAGAR current_user
						elif (logged == True):
							if(command == 'DLU'):
								self.delUser(connection)

							elif (command == 'LSD'):
								self.dirList(connection)
							logged = False

						else:
							print('User authentication needed')
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
		tcp_socket = self.tcp_connect()	

		# Runs server indefinitely to attend user requests
		while True:
			connection, client_addr = self.tcp_accept(tcp_socket)

			# Avoid child process zombies
			signal.signal(signal.SIGCHLD, signal.SIG_IGN)

			# Creating new process to attend new user requests
			try:
				pid = os.fork()
			except OSError:
				exit('CS was unnable to create child process')

			# Child process attending new user, father process continues waiting for new connections with users
			if pid == 0:
				self.userRequest(connection)



if __name__ == "__main__":

	# Parse argument
	parser = argparse.ArgumentParser()
	parser.add_argument('-p', action='store', metavar='CSport', type=int, required=False, default=58018,
	help='CSport is the well-known port where the CS server accepts user requests, in  TCP. \
	This  is  an  optional  argument.  If  omitted,  it  assumes  the  value 58000+GN, where\
	GN is the group number.')

	FLAG = parser.parse_args()
	CSport = FLAG.p

	cs = CS(CSport)
	cs.createBackupFile()
	# Avoid child process zombies
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	# Creating new process to run UDP server
	try:
		pid = os.fork()
	except OSError:
		exit('CS was unnable to create child process')

	# Child process running UDP server
	if pid == 0:
		cs.udp_server()

	# Parent process running TCP server
	else:
		cs.tcp_server()
