import socket
import sys

UDP_IP = 'localhost'
UDP_PORT = 58018
BUFFER_SIZE = 1024

# create a UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (UDP_IP, UDP_PORT)
message = 'This is the message.'

try:

    # send data
    print('sending')
    udp_socket.sendto(message.encode(), server_address)

    # receive response
    print('waiting')
    data, server = udp_socket.recvfrom(BUFFER_SIZE)
    print('received')

finally:
    print('closing')
    udp_socket.close()