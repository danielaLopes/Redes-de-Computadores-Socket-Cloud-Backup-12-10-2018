import socket
import sys
import argparse
import os

BUFFER_SIZE = 1024

class User:

	commands = ['login', 'deluser', 'backup', 'restore', 'dirlist', 'filelist', 'delete', 'logout', 'exit']
	CS_replies = ['AUT', 'AUR', 'DLU', 'DLR', 'BCK', 'BKR', 'RST', 'LSD', 'LDR', 'LSF', 'LFD', 'DEL', 'DDR']

	current_user = [] # [username, password]

	def __init__(self, CSname, CSport):
		self.TCPsocket = None
		self.CSname = CSname
		self.CSport = CSport

	def set_currentUser(self, username, password):
		self.current_user.insert(0, username)
		self.current_user.insert(1, password)

	def del_currentUser(self, username, password):
		self.current_user= []

	# Socket related methods
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

	def closeSocket(self):
		self.TCPsocket.close()

	# Interface related methods
	def sendAuthentication(self, username, password):
		self.sendData('AUT {} {}\n'.format(username, password))
		data = self.receiveData(1024)
		fields = data.split()
		CS_response = fields[0]
		status = fields[1]

		if CS_response == 'AUR':
			if(status == 'NEW'):
				print('User "{}" created'.format(username))
				self.set_currentUser(username, password)
			elif(status == 'OK'):
				self.set_currentUser(username, password)
			elif(status == 'NOK'):
				print('Incorrect password')
			else:
				print('Wrong protocol message received from CS')
				sys.exit(1)
		else:
			print('Wrong protocol message received from CS')
			sys.exit(1)

	# E PRECISO FECHAR O SOCKET ANTES DE FAZER SYS.EXIT() ?????????
	def login(self, username, password):
		# verify user input
		if len(username) == 5 and int(username) and len(password) == 8 and str.isalnum(password):
			self.connect()
			self.sendAuthentication(username, password)
			self.closeSocket()

	def deluser(self):
		self.connect()
		self.sendAuthentication(user.current_user[0], user.current_user[1])
		self.sendData('DLU\n')
		data = self.receiveData(1024)
		fields = data.split()
		CS_response = fields[0]
		status = fields[1]
		self.closeSocket()

		if CS_response == 'DLR':
			if(status == 'OK'):
				self.current_user = []
				print('User successfully deleted')
			elif(status == 'NOK'):
				print('User cannot be deleted because it still has information stored')
			else:
				print('Wrong protocol message received from CS')
				sys.exit(1)
		else:
			print('Wrong protocol message received from CS')
			sys.exit(1)

	def backupDir(self, dir):
		self.connect()
		self.sendAuthentication(user.current_user[0], user.current_user[1])

	def restoreDir(self, dir):
		self.connect()
		self.sendAuthentication(user.current_user[0], user.current_user[1])

	def dirlist(self):
		self.connect()
		self.sendAuthentication(user.current_user[0], user.current_user[1])

	def filelistDir(self, dir):
		self.connect()
		self.sendAuthentication(user.current_user[0], user.current_user[1])

	def deleteDir(self, dir):
		self.connect()
		self.sendAuthentication(user.current_user[0], user.current_user[1])

	def logout(self):
		self.del_currentUser()


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


	# Handle input
	while True:
		fields = input().split()
		input_command = fields[0]
		# verifies if the input command exists
		#E PRECISO VERIFICAR SE OS ARGUMENTOS DADOS COM OS COMANDOS ESTAO CERTOS???
		#E PRECISO VERIFICAR SE OS COMANDOS DOS PROTOCOLOS TERMINAM EM \n??????
		if input_command in user.commands:
			if (len(fields) == 3):
				if input_command == 'login':
					user.login(fields[1], fields[2]);
			#User input commands in which login is needed
			elif user.current_user != []:
				if (len(fields) == 1):
					if input_command == 'deluser':
						user.deluser();

					elif input_command == 'logout':
						user.logout()

					elif input_command == 'dirlist':
						user.dirlist()

				elif (len(fields) == 2):
					if input_command == 'backup':
						user.backupDir(fields[1])

					elif input_command == 'restore':
						user.restoreDir(fields[1])

					elif input_command == 'delete':
						user.deleteDir(fields[1])

			elif input_command == 'exit' and len(fields) == 1:
				os._exit(0) #ESTAMOS A USAR A CENA CERTA??

			elif user.current_user == []:
				print('User authentication needed')
		else:
			print('Invalid command')
