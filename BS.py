import socket
import sys
import argparse

BUFFER_SIZE = 1024

BSname = 'localhost'


if __name__ == "__main__":

	commands = ['REG', 'RGR']

	parser = argparse.ArgumentParser()

	parser.add_argument('-b', action='store', metavar='BSport', type=str, required=False, default=59000,
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

	# create a UDP socket for initial communication with CS (as client)
	udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	server_address = (BSname, BSport)
		
	try:
	# send data
		udp_socket.sendto(('{} {} {}\n'.format('REG', BSname, BSport)).encode(), server_address)
		# receive response
		data, server = udp_socket.recvfrom(BUFFER_SIZE).decode()
		fields = data.split();
		command = fields[0]
		status = fields[1]
		if data and command == 'RGB':
			if status == 'OK':
				print(data)
			elif status == 'NOK':
				#fazer algo
		    elif status == 'ERR':
		    	print('Wrong protocol message received from CS')
				sys.exit(1)
		#repeat information trade to assure everything is received
		else:
			udp_socket.sendto(('{} {} {}\n'.format('REG', BSname, BSport)).encode(), server_address)
			data, server = udp_socket.recvfrom(BUFFER_SIZE).decode()
			print(data)

	except socket.error:
		print('closing')
		udp_socket.close()
		print('BS failed to trade data')
		sys.exit(1)

	#BS Server is ready for initiating TCP and UDP servers
	# Avoid child process zombies
	signal.signal(signal.SIGCHLD, signal.SIG_IGN)

	# Creating new process to run both TCP and UDP servers
	#try:
		#pid = os.fork()
	#except OSError:
		#exit('BS was unnable to create child process')

	# Child process running TCP server to receive requests from users
	#if pid == 0:
		

	# Parent process running UDP server to receive requests from CS
	#else:
	try:
		udp_socket.bind((CSname, BSport))
	except socket.error:
		print('BS failed to bind with CS')
		sys.exit(1)
	try:
		while(True): #TEMOS DE SABER O NUMERO DE BYTES A RECEBER????
			data = udp_socket.recvfrom(1024).decode()
	
	except socket.error:
		print('BS failed to trade data with CS')
	finally:
		udp_socket.close()




