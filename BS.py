import socket
import sys
import argparse

BUFFER_SIZE = 1024

BSname = 'localhost'


if __name__ == "__main__":

	commands = ['REG', 'RGR']

	parser = argparse.ArgumentParser()

	parser.add_argument('-b', action='store', metavar='BSport', type=str, required=False, default=58018,
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

	# CLIENT FOR UDP TO COMMUNICATE WITH CS

	# create a UDP socket
	udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	server_address = (BSname, BSport)

	while True:
		
		try:
		# send data
			udp_socket.sendto(('{} {} {}'.format(commands[0], BSname, BSport)).encode(), server_address)

			# receive response
			data, server = udp_socket.recvfrom(BUFFER_SIZE)
			print(data.decode())

		except socket.error:
			print('closing')
			udp_socket.close()
			print('BS failed to trade data')
			sys.exit(1)
