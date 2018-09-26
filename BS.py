import socket
import sys

UDP_IP = 'localhost'
UDP_PORT = 58018
MESSAGE = "Hello, World!"
BUFFER_SIZE = 1024

'''
BSname = 'localhost'

if __name__ == "__main__":

	parser = argparse.ArgumentParser()

	parser.add_argument('-b', action='store', metavar='BSport', type=str, required=False, default='58018',
	help='BSport is the well-known port where the BS server accepts TCP requests
	from the user application. This is an optional argument. If omitted, it assumes
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
	BSsport = FLAGS.b
	CSname = FLAGS.n
	CSport = FLAGS.p
'''

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
	while True:
	    print('waiting to receive')
	    data, client_address = udp_socket.recvfrom(BUFFER_SIZE)
	  	    
	    if data:
	        sent = udp_socket.sendto(data, client_address)
	        print('enviar')
	    else:
	    	break

except socket.error:
	print('BS failed to trade data')
	sys.exit(1)