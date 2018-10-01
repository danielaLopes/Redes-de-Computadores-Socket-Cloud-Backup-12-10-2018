import socket
import sys
import argparse
import os
import multiprocessing
import signal

BUFFER_SIZE = 1024

CSname = 'localhost'#socket.gethostname()

if __name__ == "__main__":

	BS_commands = ['REG','RGR', 'UNR', 'UAR', 'LSF', 'LFD N', 'LSU', 'LUR', 'DLB', 'DBR']
	user_commands = ['AUT', 'AUR', 'DLU', 'DLR', 'BCK', 'BKR', 'RST', 'LSD', 'LDR', 'LSF', 'LFD', 'DEL', 'DDR']

	registered_users = {} # username: password
	current_user = None

	# Parse argument
	parser = argparse.ArgumentParser()
	parser.add_argument('-p', action='store', metavar='CSport', type=int, required=False, default=58018,
	help='CSport is the well-known port where the CS server accepts user requests, in  TCP. \
	This  is  an  optional  argument.  If  omitted,  it  assumes  the  value 58000+GN, where\
	GN is the group number.')

	FLAG = parser.parse_args()
	CSport = FLAG.p

	# Creating new process to run UDP server
	try:
		pid = os.fork()
	except OSError:
		exit('CS was unnable to create child process')

	# Child process running UDP server
	if pid == 0:
		print('Hello child')

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

		while True:
			print('Waiting for a connection with a BS')
			try:
				data, client_address = udp_socket.recvfrom(BUFFER_SIZE)

				if data:
				    fields = data.decode().split()

				    if(fields[0] == BS_commands[0]):
				    	IPBS = fields [1]
				    	portBS = fields [2]
				    	print('{} {} {}'.format(fields[0], IPBS, portBS))
				    	udp_socket.sendto('RGR OK'.encode('ascii'), client_address)

			except socket.error:
				print('CS failed to trade data with BS')
				sys.exit(1)


	# Parent process running TCP server
	else:
		# Avoid child process zombies
		signal.signal(signal.SIGCHLD, signal.SIG_IGN)
		print('Hello father')
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

		while True:
			# waits for connection
			print('Waiting for a connection with an user')
			try:
				connection, client_addr = tcp_socket.accept()
			except socket.error:
				print('CS failed to establish connection')
				sys.exit(1)

			try:
				while True:
					data = connection.recv(BUFFER_SIZE)

					if data:
						fields = data.decode().split()
						command = fields[0]

						if command in user_commands:
							if command == 'AUT':
								username = fields [1]
								password = fields [2]

								if username in registered_users.keys():
									if password == registered_users[username]:
										connection.sendall('AUR OK'.encode('ascii'))
										current_user = username
										print('User: "{}"'.format(username))
									else:
										connection.sendall('AUR NOK'.encode('ascii'))
										print('Incorrect password')
								else:
									connection.sendall('AUR NEW'.encode('ascii'))
									registered_users[username] = password
									current_user = username
									print('New user: "{}"'.format(username))
							# The following messages must be preceded by an AUT message within the same TCP session
							elif (current_user != None): #LEMBRAR DE NO FIM DE CADA SESSAO TCP APAGAR current_user
								if(command == 'DLU'):
									print(current_user)
									#if (current_user.information().isempty()):
									try:
										del registered_users[current_user]
										current_user = None
										connection.sendall('DLR OK'.encode('ascii'))
									except KeyError:
										print('This user is not registered')
									#else:
										#connection.sendall('DLR NOK'.encode('ascii'))
							else:
								print('User authentication needed')
						else:
							connection.sendall('ERR'.encode('ascii'))
							sys.exit(1)
					else:
						break
			except socket.error:
				print('CS failed to trade data with user')
				sys.exit(1)
			finally:
				connection.close()
