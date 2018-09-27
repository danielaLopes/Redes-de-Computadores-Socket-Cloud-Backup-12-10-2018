import socket
import sys
import argparse

BUFFER_SIZE = 1024

CSname = 'localhost'#socket.gethostname()

if __name__ == "__main__":

	BS_commands = ['REG','RGR']
	user_commands = ['AUT', 'AUR', 'DLU', 'DLR', 'BCK', 'BKR', 'RST', 'LSD', 'LDR', 'LSF', 'LFD', 'DEL', 'DDR']

	# Parse argument
	parser = argparse.ArgumentParser()
	parser.add_argument('-p', action='store', metavar='CSport', type=int, required=False, default=58018,
	help='CSport is the well-known port where the CS server accepts user requests, in  TCP. \
	This  is  an  optional  argument.  If  omitted,  it  assumes  the  value 58000+GN, where\
	GN is the group number.')

	FLAG = parser.parse_args()
	CSport = FLAG.p


	UDP_IP = 'localhost'
	UDP_PORT = 58018

	try:
		udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error:
		print('BS failed to create socket')
		sys.exit(1)

	try:
		udp_socket.bind((UDP_IP, UDP_PORT))
	except socket.error:
		print('BS failed to bind')
		sys.exit(1)


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
		print('BS failed to trade data')
		sys.exit(1)

''' TCP CONNECTION '''

'''

	try:
		tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error:
		print('CS failed to create socket')
		sys.exit(1)

	try:
		tcp_socket.bind(("", CSport))
	except socket.error:
		print('CS failed to bind')
		sys.exit(1)

	tcp_socket.listen(5)

	while True:
		try:
			connection, client_addr = tcp_socket.accept()
		except socket.error:
			print('CS failed to establish connection')
			sys.exit(1)

		try:
			#corrigir cena de nao dar para recv mais do que uma vez
			data = connection.recv(BUFFER_SIZE)

			if data:
				fields = data.decode().split()
				
				if(fields[0] == user_commands[0]):
					username = fields [1]
					password = fields [2]
					connection.sendall('AUR NEW'.encode('ascii'))
					print('New user: "{}"'.format(username))
					#print(f'New user: {username}')
			else:
				break
		except socket.error:
			print('CS failed to trade data')
			sys.exit(1)
		finally:
			connection.close()
'''
