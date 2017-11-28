import socket
import sys
import re
RECV_BUFFER = 4096 

def start_client():
	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Connect the socket to the port on the server given by the caller
	server_address = ('0.0.0.0', 8000)
	print >>sys.stderr, 'connecting to %s port %s' % server_address
	sock.connect(server_address)

	message = getmessage('join3')
	clientinfo = re.search(r'CLIENT_NAME:\s*\w+', message).group()
	infoname = 'CLIENT_NAME:'
	clientname = clientinfo[clientinfo.index(infoname)+len(infoname):].strip()

	sock.sendall(message)

	# read message
	data=sock.recv(RECV_BUFFER)
	print 'received %s\n' % data 

	# extract roomref and join_id
	roominf = re.search(r'ROOM_REF:\s*.+', data).group()

	roomref = roominf[roominf.index('ROOM_REF:')+len('ROOM_REF:'):].strip()
	joininf = re.search(r'JOIN_ID:\s*.+', data).group()
	joinid = joininf[joininf.index('JOIN_ID:')+len('JOIN_ID:'):].strip()
	
	message = dict()
	message['roomref']=roomref
	message['joinid'] = joinid
	message['clientname'] = clientname
	message['message']='my name is '+clientname+'\n\n'

	chatmsg = loadfile(message, 'chat')
	chat(chatmsg, sock)

	try:
		# read message
		data=sock.recv(RECV_BUFFER)
		print 'received %s\n' % data 
		print 'leaving....'
		leavemsg = loadfile(message, 'leave')

		sock.send(leavemsg)
		data=sock.recv(RECV_BUFFER)
		print 'received %s\n' % data 

		print 'disconnecting....'
		disconn = loadfile(message, 'disconnect')
		sock.send(disconn)
	finally:
		print 'sock is closing due to exception'
		# sock.close()

# populate response files with var inputs
def loadfile(variables, filename):
    f = open("message/"+filename,"r")
    filestr = f.read()
    response = filestr.format(**variables)
    f.close()
    return response

def chat(message, sock):
	print 'chat message '+message
	sock.send(message)
def getmessage(filename):
	f = open('./message/'+filename,"r")
	filestr = f.read()
	f.close()
	return filestr

if __name__ == "__main__":
	sys.exit(start_client())