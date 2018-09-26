import socket
import sys
import argparse

BUFFER_SIZE = 1024

CSname = 'localhost'

if __name__ == "__main__":

	# Parse argument
	parser = argparse.ArgumentParser()
	parser.add_argument('-p', action='store', metavar='CSport', type=int, required=False, default=58018,
	help='CSport is the well-known port where the CS server accepts user requests, in  TCP. \
	This  is  an  optional  argument.  If  omitted,  it  assumes  the  value 58000+GN, where\
	GN is the group number.')

	FLAG = parser.parse_args()
	CSport = FLAG.p

	try:
		tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error:
		print('CS failed to create socket')
		sys.exit(1)

	try:
		tcp_socket.bind((CSname, CSport))
	except socket.error:
		print('CS failed to bind')
		sys.exit(1)

	tcp_socket.listen(5)

	try:
		connection, client_addr = tcp_socket.accept()
	except socket.error:
		print('CS failed to establish connection')
		sys.exit(1)

	try:
		while True:
			data = connection.recv(BUFFER_SIZE)
			print('recebeu')

			if data:
				connection.sendall(f'User {data.decode()} created!'.encode('ascii'))
				print('chegou')
			else:
				break
	except socket.error:
		print('CS failed to trade data')
		sys.exit(1)
	finally:
		connection.close()

