import socket
import sys
RECV_BUFFER = 4096 

def start_client():
	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Connect the socket to the port on the server given by the caller
	server_address = ('0.0.0.0', 8000)
	print >>sys.stderr, 'connecting to %s port %s' % server_address
	sock.connect(server_address)

	message = getfile('join1')
	print 'sending:',message
	sock.sendall(message)

	while 1:
		try:
			data=sock.recv(RECV_BUFFER)
			print 'received %s' % data 
		except:
			sock.close()
def getfile(filename):
	f = open(filename,"r")
	filestr = f.read()
	f.close()
	return filestr

if __name__ == "__main__":
	sys.exit(start_client())