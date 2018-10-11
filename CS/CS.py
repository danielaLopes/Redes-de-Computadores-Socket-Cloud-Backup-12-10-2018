import socket
import sys
import argparse
import os
import multiprocessing
import signal
import random
import shutil

BUFFER_SIZE = 1024

CSname = 'localhost'#socket.gethostname()


class CS:

	BS_commands = ['REG','RGR', 'UNR', 'UAR', 'LSF', 'LFD N', 'LSU', 'LUR', 'DLB', 'DBR']
	user_commands = ['AUT', 'AUR', 'DLU', 'DLR', 'BCK', 'BKR', 'RST', 'LSD', 'LDR', 'LSF', 'LFD', 'DEL', 'DDR']

	current_user = None #username


	def __init__(self, CSport):
		self.CSport = CSport
		self.tcp_socket = None
		self.udp_socket = None
		self.udp_socket2 = None


	# User communication methods
	#NAO ESQUECER DE IMPRIMIR AS INFORMACOES DO USER!!!!!!!!!!
	def createBSsFile(self):
		# If this file was not created yet, the CS creates it
		if not os.path.isfile('availableBS.txt'):
			try:
				# Overwrites existing file with this name
				availableBS = open('availableBS.txt', 'w')
				availableBS.close()
			except IOError:
				print('Not possible to create availableBS.txt')


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


	def backupDir(self, connection, dir, N, fileData):
		user = self.current_user
		userPath = os.getcwd() + "/user_" + user
		dirlist = os.listdir(userPath)

		print(user)

		#dirlen = len(dir)

		if dir not in dirlist:
			availableBS = open("availableBS.txt", "r")
			BSs = availableBS.readlines()

			BS = random.choice(BSs).split()
			IPBS = BS[0]
			portBS = BS[1]

			os.mkdir(userPath + "/" + dir)

			BSfile = open(userPath + "/" + dir + "/IP_port.txt", 'w')
			BSfile.write(IPBS + " " + portBS)
			BSfile.close()

			try:
				self.udp_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

				f = open("user_" + user + ".txt", "r")
				password = f.read(8)
				f.close()

				self.udp_socket2.sendto('LSU {} {}\n'.format(user, password).encode('ascii'), (IPBS, int(portBS)))

				print("mandei")

				data, client_addr = self.udp_socket2.recvfrom(BUFFER_SIZE)
				self.udp_socket2.close()


				fields = data.decode().split()
				command = fields[0]
				status = fields[1]
				info = fileData[5 + len(dir):]

				print(fileData)


				if command == "LUR":
					if status == "OK":
						message = "BKR " + IPBS + " " + portBS + ' ' + info;
						connection.sendall(message.encode('ascii'))

				else:
					print("oi")

			except socket.error:
				print('CS failed to create UDP socket')
				sys.exit(1)


	def restoreDir(self):
		print('ola')


	def dirList(self, connection):
		dirNames = os.listdir('.'+'/user_'+ self.current_user)
		info = "LDR"

		if not dirNames:
			info += " 0\n"	
			connection.sendall(info.encode())
		else:
			info += " " + str(len(dirNames))
			connection.sendall(info.encode())
			print(info)

			for dir in dirNames:
				message = " " + dir
				print(message)
				connection.send(message.encode('ascii'))


	def filelistDir(self, connection, dir):
		userPath = os.getcwd() + "/user_" + self.current_user
		dirPath = userPath + "/" + dir

		BSfile = open(dirPath + "/IP_port.txt", 'r')
		BS = BSfile.readline().split()
		BSfile.close()
		print(BS)

		IPBS = BS[0]
		portBS = int(BS[1])

		try:
			self.udp_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

			self.udp_socket2.sendto('LSF {} {}\n'.format(self.current_user, dir).encode('ascii'), (IPBS, portBS))

			data, client_addr = self.udp_socket2.recvfrom(BUFFER_SIZE)
			self.udp_socket2.close()

			decodedData = data.decode()
			fields = decodedData.split()
			command = fields[0]
			info = decodedData[3:]

			if command == "LFD":
				message = "LFD " + IPBS + " " + BS[1] + info;
				connection.sendall(message.encode('ascii'))

		except socket.error:
			print('CS failed to create UDP socket')
			sys.exit(1)


	def deleteDir(self, connection, dir):
		user = self.current_user
		bsPath = os.getcwd() + "/user_" + user + "/" + dir + "/IP_port.txt"
		bsFile = open(bsPath, 'r')
		BS = bsFile.readline().split()
		bsFile.close()

		print("li ficheiro bs")
		# Requests BS to delete dir
		try:
			self.udp_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			#ISTO NAO ESTA EM PYTHON2
			message = 'DLB ' + user + ' ' + dir + '\n'
			self.udp_socket2.sendto(message.encode('ascii'), (BS[0], int(BS[1])))
			print('antes de receber do BS')
			data, client_addr = self.udp_socket2.recvfrom(1024)
			print('depois de receber do BS')
			self.udp_socket2.close()
		except socket.error:
			print('CS failed to create UDP socket')
			sys.exit(1)

		# Deletes dir from CS
		deleteStatus = False
		dirPath = os.getcwd() + "/user_" + user + "/" + dir
		print("apaga diretoria user")
		if os.path.isdir(dirPath):
			shutil.rmtree(dirPath)
			deleteStatus = True
		else:
			print('It was not possible to remove the requested directory')

		fields = data.decode().split()
		command = fields[0]

		# Tells user if everything is ok
		if command == 'DBR':
			status = fields[1]
			if status == 'OK' and deleteStatus == True:
				connection.sendall('DDR OK'.encode('ascii'))
			elif status == 'NOK' and deleteStatus == False:
				connection.sendall('DDR NOK'.encode('ascii'))
			else:
				connection.sendall('ERR'.encode('ascii'))
		else:
			connection.sendall('ERR'.encode('ascii'))


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
			udp_socket.bind((CSname, self.CSport))
		except socket.error:
			print('CS failed to bind with BS')
			sys.exit(1)

		return udp_socket



	def udp_server(self):
		self.udp_socket = self.udp_connect()

		try:
			# Runs server indefinitely to attend BS registrations
			while True:
				print('Waiting for a connection with a BS')
				data, client_address = self.udp_socket.recvfrom(BUFFER_SIZE)

				if data:
					fields = data.decode().split()
					print('comando ' + fields[0])

					if fields[0] == 'REG' and len(fields) == 3:
						IPBS = fields[1]
						portBS = fields[2]

						# Register all available BS in a file
						try:
							availableBS = open('availableBS.txt', 'r+')
							BSs = availableBS.readlines()
							if BSs != []:
								print(BSs[0])

								BSregistered = False
								for i in range(0, len(BSs)):
									BSinfo = BSs[i].split()
									if IPBS == BSinfo[0] and portBS == BSinfo[1]:
										BSregistered = True

								if BSregistered == False:
									availableBS.write('{} {} A\n'.format(IPBS, portBS)) # A for available
							else:
								availableBS.write('{} {} A\n'.format(IPBS, portBS)) # A for available

							availableBS.close()
						except IOError:
							print('Not possible to append information in availableBS.txt')

						print('{} {} {}'.format(fields[0], IPBS, portBS))
						self.udp_socket.sendto('RGR OK\n'.encode('ascii'), client_address)

					#QUANDO FAZER RGR ERR?????

					elif fields[0] == 'UNR': 
						try:
							IPBS = fields[1]
							portBS = int(fields[2])

							availableBS = open('availableBS.txt', 'r')
							BSs = availableBS.readlines()
							availableBS.close()

							availableBS = open('availableBS.txt', 'w')

							for line in BSs:
								BSinfo = line.split()
								if IPBS != BSinfo[0] or str(portBS) != BSinfo[1]:
									availableBS.write(line)
							availableBS.close()

							udp_socket.sendto('UAR OK\n'.encode(), client_address)
						except IOError:
							udp_socket.sendto('UAR NOK\n'.encode(), client_address)


					else:
						self.udp_socket.sendto('RGR NOK\n'.encode('ascii'), client_address)

		except socket.error:
			print('CS failed to trade data with BS')
			sys.exit(1)

		finally:
			self.udp_socket.close()


	def tcp_connect(self):
		try:
			self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error:
			print('CS failed to create TCP socket')
			sys.exit(1)

		# Reuse port
		self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.tcp_socket.bind((CSname, self.CSport))
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

							#UPDATE!!!!
							# backup dir

							else:
								connection.sendall('ERR\n'.encode('ascii'))
								sys.exit(1)

						elif command == 'BCK': # CS response: BKR IPBS portBS N (filename date_time size)*
								if logged == True:
									print("vim")
									self.backupDir(connection, fields[1], fields[2], data.decode())
									logged = False

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
								    self.restoreDir(connection, fields[1])
								# filelist dir
								elif command == 'LSF': # CS response: LFD BSip BSport N (filename date_time size)*
								    self.filelistDir(connection, fields[1])
								# del dir
								elif command == 'DEL': # CS response: DDR status
								    self.deleteDir(connection, fields[1])

								else:
									connection.sendall('ERR\n'.encode('ascii'))
									sys.exit(1)

								logged = False

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
				exit('CS was unnable to create child process')

			# Child process attending new user, father process continues waiting for new connections with users
			if pid == 0:
				self.userRequest(connection)


def sigIntHandler(num, frame):
	open('availableBS.txt', 'w').close()
	sys.exit()


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
	cs.createBSsFile()

	signal.signal(signal.SIGINT, sigIntHandler)

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
