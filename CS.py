import socket
import sys
import argparse
import os
import multiprocessing
import signal

BUFFER_SIZE = 1024

class CS:

	BS_commands = ['REG','RGR', 'UNR', 'UAR', 'LSF', 'LFD N', 'LSU', 'LUR', 'DLB', 'DBR']
	user_commands = ['AUT', 'AUR', 'DLU', 'DLR', 'BCK', 'BKR', 'RST', 'LSD', 'LDR', 'LSF', 'LFD', 'DEL', 'DDR']

	registered_users = {} # username: password
	current_user = None

	def __init__(self, CSport):
		self.CSport = CSport

	# Socket related methods
	def connect(self):
		try:
			tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error:
			print('CS failed to create TCP socket')
			sys.exit(1)

		try:
			tcp_socket.bind((CSname, CSport))
		except socket.error:
			print('CS failed to bind with user')
			sys.exit(1)

		tcp_socket.listen(5)

	# Interface related methods
	def userAuthentication(self, username, password):

		if username in registered_users.keys():
			if password == registered_users[username]:
				connection.sendall('AUR OK\n'.encode('ascii'))
				self.current_user = username
				print('User: "{}"'.format(username))
			else:
				connection.sendall('AUR NOK\n'.encode('ascii'))
				print('Incorrect password')
		else:
			connection.sendall('AUR NEW\n'.encode('ascii'))
			self.registered_users[username] = password
			self.current_user = username
			print('New user: "{}"'.format(username))

	def delUser(self):
		print(current_user)
		#if (current_user.information().isempty()):
		try:
			del self.registered_users[current_user]
			self.current_user = None
			connection.sendall('DLR OK\n'.encode('ascii'))
		except KeyError:
			print('This user is not registered')
		#else:
			#connection.sendall('DLR NOK\n'.encode('ascii'))


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

	# Avoid child process zombies
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	# Creating new process to run UDP server
	try:
		pid = os.fork()
	except OSError:
		exit('CS was unnable to create child process')

	# Child process running UDP server
	if pid == 0:
		try:
			udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		except socket.error:
			print('CS failed to create UDP socket')
			sys.exit(1)

		try:
			udp_socket.bind((CSname, CSport))
		except socket.error:
			print('CS failed to bind with BS')
			sys.exit(1)

		print('Waiting for a connection with a BS')
		try:
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

	# Parent process running TCP server
	else:
		cs.connect()

		while True:
			# waits for connection
			print('Waiting for a connection with an user')
			try:
				connection, client_addr = tcp_socket.accept()
			except socket.error:
				print('CS failed to establish connection')
				sys.exit(1)

			try:
				logged = False
				while True:
					data = connection.recv(BUFFER_SIZE)

					if data:
						fields = data.decode().split()
						command = fields[0]

						if command in user_commands:
							if command == 'AUT':
								cs.userAuthentication(fields[1], fields[2])
								logged = True

							#LEMBRAR DE NO FIM DE CADA SESSAO TCP APAGAR current_user
							elif (logged == True):
								if(command == 'DLU'):
									cs.delUser()
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
