import socket
import sys
import argparse
import os
import signal
import shutil
import time
import datetime
from datetime import datetime
import select


BUFFER_SIZE = 1024

BSname = 'localhost'#socket.gethostname()

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
		self.current_user = None

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


	def restoreDir(self, connection, dir):
		user = self.current_user
		dirPath = os.getcwd() + "/user_" + user + "/" + dir
		if os.path.exists(dirPath):
			dirNames = os.listdir(dirPath)
			N = len(dirNames)
			fileInf = ""

			connection.sendall('RBR {}\n'.format(N).encode('ascii'))

			for file in dirNames:
				fileSize = int(os.stat(dirPath + "/" + file).st_size)
				bytes_read = 0
				fileInf = ' ' + file + ' ' + time.strftime('%m.%d.%Y %H:%M:%S',
				time.gmtime(os.path.getmtime(dirPath + "/" + file))) + ' ' + str(int(os.stat(dirPath + "/" + file).st_size)) + ' '
				connection.sendall('{}'.format(fileInf).encode('ascii'))
				currentFile = open(dirPath + "/" + file, 'rb')
				while bytes_read <= fileSize:
					data = currentFile.read(1024)
					bytes_read += fileSize
					connection.send(data)

		else:
			connection.sendall('RBR EOF\n'.encode('ascii'))
			print('The requested directory was not found')


	def deleteDir(self, connection, user, dir):
		dirPath = os.getcwd() + "/user_" + user + "/" + dir
		userPath = os.getcwd() + "/user_" + user
		if os.path.isdir(dirPath):
			shutil.rmtree(dirPath)
			if len(os.listdir(userPath)) == 0:
				shutil.rmtree(userPath)
				os.remove(userPath + ".txt")
			self.udp_socket2.sendto('DBR OK\n'.encode('ascii'), connection)
		else:
			print('It was not possible to remove the requested directory')
			self.udp_socket2.sendto('DBR NOK\n'.encode('ascii'), connection)


	def LSF(self, connection, user, dir):
		userPath = os.getcwd() + "/user_" + user
		dirPath = userPath + "/" + dir
		fileList = os.listdir(dirPath)
		fileInf = ""

		for file in fileList:
			fileInf = fileInf + " " + file + " " + time.strftime('%m.%d.%Y %H:%M:%S',
			time.gmtime(os.path.getmtime(dirPath + "/" + file))) + " " + str(int(os.stat(dirPath + "/" + file).st_size))

		message = "LFD " + str(len(fileList)) + fileInf + "\n"
		self.udp_socket2.sendto(message.encode('ascii'), connection)


	def LSU(self, connection, username, password):
		filename = "user_" + username + ".txt";
		userFile = open(filename, 'w+')
		userFile.write(password + '\n')
		userFile.close()

		# Create new directory for that use
		if not os.path.exists('user_' + username):
			try:
				os.mkdir('user_' + username)
			except OSError:
				print('Not possible to create directory for this user')

			self.udp_socket2.sendto("LUR OK".encode('ascii'), connection)
		else:
			print('directory already exists')

	def UPL (self, connection, dir, N, data):
		user = self.current_user
		userPath = os.getcwd() + "/user_" + user

		dirList = os.listdir(userPath)
		path = userPath + "/" + dir

		if dir not in dirList:
			os.mkdir(path)


		files = self.makeFile(data[6 + len(dir) + len(N):], path)

		while files != '':
			try:
				files = self.makeFile(files, path)
			except OSError:
				connection.sendall("UPR NOK".encode('ascii'))

		connection.sendall("UPR OK".encode('ascii'))


	def makeFile (self, files, path):
		content = files.split()
		fileName = content[0]
		date = content[1] + " " + content[2]
		#NAO ESQUECER MUDAR DATA PARA A ANTIGA GIGANTE
		size = int(content[3])

		lens = len(fileName) + len(date) + len(str(size)) + 3

		userFile = open(path+"/"+fileName, 'w')
		userFile.write(files[lens:lens + size])
		userFile.close()

		dateTime = time.strptime(content[1] + " " + content[2], '%m.%d.%Y %H:%M:%S')
		epoch = time.mktime(dateTime) + 60*60

		os.utime(path+"/"+fileName, (epoch,epoch))

		return files[lens+size:]



	def userRequest(self, connection):
		try:
			logged = False

			while True:
				data = connection.recv(BUFFER_SIZE)

				if data:
					fields = data.decode().split()
					command = fields[0]

					if command in self.user_commands:
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

						elif command == 'UPL':
							self.UPL(connection, fields[1], fields[2], data.decode())

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
			print('BS failed to trade data with user')
			sys.exit(1)

		finally:
			connection.close()


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
				self.userRequest(connection)


	def udp_client(self):
		try:
			# create a UDP socket for initial communication with CS (as client)
			try:
				self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			except socket.error:
				print('BS unable to create UDP socket')
			# send data
			self.udp_socket.sendto(('{} {} {}\n'.format('REG', BSname, self.BSport)).encode('ascii'), (self.CSname, self.CSport))
			data = ""
			# receive response
			data, server = UDPfailHandler(self.udp_socket, self.CSname, self.CSport, '{} {} {}\n'.format('REG', BSname, self.BSport), data)

			fields = data.decode().split();
			command = fields[0]
			status = fields[1]

			if data and command == 'RGR':
				if status == 'OK':
					print("Registry accepted")
				elif status == 'NOK':
					print("Registry declined")
				elif status == 'ERR':
					print('Wrong protocol message received from CS')
					sys.exit(1)

			else:
				data = ""
				self.udp_socket.sendto(('REG {} {}\n'.format(BSname, self.BSport)).encode(), (self.CSname, self.CSport))
				data, server = UDPfailHandler(self.udp_socket, self.CSname, self.CSport, 'REG {} {}\n'.format(BSname, self.BSport), data)

		except socket.error:
			print('BS failed to trade data')
			sys.exit(1)
		finally:
			self.udp_socket.close()


	def udp_server(self):
		# Running UDP server to receive requests from CS

		try:
			self.udp_socket2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		except socket.error:
			print('BS unable to create UDP socket')

		# Reuse port
		self.udp_socket2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		try:
			self.udp_socket2.bind((BSname, self.BSport))
		except socket.error:
			print('BS failed to bind with CS')
			sys.exit(1)

		def sigIntHandler(num, frame):
			data = ""
			self.udp_socket2.sendto(('UNR {} {}\n'.format(BSname, self.BSport)).encode('ascii'), (self.CSname, self.CSport))
			data, server = UDPfailHandler(self.udp_socket2, self.CSname, self.CSport, 'UNR {} {}\n'.format(BSname, self.BSport), data)
			fields = data.decode().split()
			if fields[0] == 'UAR':
				if fields[1] == 'OK':
					print('BS succefully unregistered')
				elif fields[1] == 'NOK':
					print('BS not succefully unregistered')
				elif fields[1] == 'ERR':
					print('Protocol syntax error')
			else:
				print('Protocol syntax error')

			sys.exit(0)

		# Captures signal from Cntrl-C
		signal.signal(signal.SIGINT, sigIntHandler)

		try:
			while(True):
				print('BS waiting for a connection with a CS')
				data, client_addr = self.udp_socket2.recvfrom(1024)
				fields = data.decode().split()
				command = fields[0]
				if command == 'DLB':
					self.deleteDir(client_addr, fields[1], fields[2])

				if command == 'LSF': # CS response: AUR status
					self.LSF(client_addr, fields[1], fields[2])

				if command == 'LSU': # CS response: AUR status
					self.LSU(client_addr, fields[1], fields[2])

		except socket.error:
			print('BS failed to trade data with CS')

		finally:
			self.udp_socket2.close()

def UDPfailHandler(socket, CSname, CSport, message, data):
	n_trials = 3
	while n_trials > 0:
		n_trials -= 1

		socket.setblocking(0)
		ready = select.select([socket], [], [], 2)
		client_addr = None
		# If there is a message to receive
		if ready[0]:
			data, client_addr = socket.recvfrom(1024)
			break
		# If no response from BS is obtained, it resends message
		elif n_trials > 0:
			socket.sendto(message.encode('ascii'), (BSname, BSport))

	return data, client_addr


if __name__ == "__main__":

	parser = argparse.ArgumentParser()

	parser.add_argument('-b', action='store', metavar='BSport', type=int, required=False, default=59000,
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
