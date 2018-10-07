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
		self.tcp_socket = None
	

	# User communication methods
	def createBackupFile(self):
		# Creating the backup_list file
		f = open("backup_list.txt", "w")
		f.write("RC\n")
		f.write("OLA\n")
		f.close()

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
				# Create new file for new user
				userFile = open(filename, 'w+')
				userFile.write(password + '\n')
				userFile.close()

				# Create new directory for that user
				try:
					os.mkdir('user_' + username)
				except OSError:
					print('Not possible to create directory for this user')
				
				self.current_user = username
				connection.sendall('AUR NEW\n'.encode('ascii'))
				print('New user: "{}"'.format(self.current_user))

		except IOError:
			print('It was not possible to open the requested file')

	
	def delUser(self, connection):
		filename = 'user_' + self.current_user + '.txt'
		empty = False

		if os.path.exists(filename):
			try:
				os.rmdir('user_' + self.current_user)
				empty = True
			except OSError:
				empty = False
				connection.sendall('DLR NOK\n'.encode('ascii'))

			if empty == True:
				try:
					os.remove(filename)
					self.current_user = None
					connection.sendall('DLR OK\n'.encode('ascii'))
				except OSError:
					print('Not possible to delete user file')
		else:
			print('This user is not registered')


	def backupDir(self):
		print('ola')


	def restoreDir(self):
		print('ola')


	def dirList(self, connection):
		f = open("backup_list.txt", "r")
		N = 0
		dirnames = ""

		for line in f:
			N += 1
			dirnames = dirnames + " " + line

		message = "LDR " + str(N) + " " + dirnames + "\n"
		connection.sendall(message.encode('ascii'))


	def filelistDir(self):
		print('ola')


	def deleteDir(self):
		print('ola')


	# Socket related methods
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
			self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error:
			print('CS failed to create TCP socket')
			sys.exit(1)

		# Reuse port
		self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	

		try:
			self.tcp_socket.bind((CSname, CSport))
		except socket.error:
			print('CS failed to bind with user')
			sys.exit(1)

		self.tcp_socket.listen(5)


	def tcp_accept(self):
		# waits for connection with an user
		print('Waiting for a connection with an user')
		try:
			connection, client_addr = self.tcp_socket.accept()
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
						# login
						if len(fields) == 3:
							if command == 'AUT': # CS response: AUR status
								self.userAuthentication(connection,fields[1], fields[2])
								logged = True

							# backup dir
							elif command == 'BCK': # CS response: BKR IPBS portBS N (filename date_time size)*
								if logged == True:
									self.backupDir()
									logged = False
								# else

							else:
								connection.sendall('ERR\n'.encode('ascii'))
								sys.exit(1)

						elif len(fields) == 1:
							if logged == True:
								# deluser
								if command == 'DLU': # CS response: DLR status
									self.delUser(connection)

								# dirlist
								elif command == 'LSD': # CS response: LDR N (dirname)*
									self.dirList(connection)

								else:
									connection.sendall('ERR\n'.encode('ascii'))
									sys.exit(1)

								logged = False
							
						elif len(fields) == 2:
							if logged == True:
								# restore dir
								if command == 'RST': # CS response: RSR IPBS portBS
								    self.restoreDir()
								# filelist dir
								elif command == 'LSF': # CS response: LFD BSip BSport N (filename date_time size)*
								    self.filelistDir()
								# del dir
								elif command == 'DEL': # CS response: DDR status
								    self.deleteDir()

								else:
									connection.sendall('ERR\n'.encode('ascii'))
									sys.exit(1)

								logged = False
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


	def sig_handler(sig, frame):
		cs.tcp_socket.close()
		print("close")
	signal.signal(signal.SIGINT, sig_handler)

	
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
