# chat_server.py
 
import sys
import socket
import select
import uuid
from collections import defaultdict

HOST = '' 
SOCKET_LIST = []
RECV_BUFFER = 4096 
PORT = 8000 
studentId = 14325922

CHATROOM = dict()
ALIVE_SOCKETS = dict()
def chat_server():
    if sys.argv and len(sys.argv)>1 and sys.argv[1].isdigit():
        global PORT
        PORT = int(sys.argv[1])
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    
    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
    print "Chat server started on port " + str(PORT)
    while 1:

        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 2 : poll every 2 sec
        try: 
            ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],2)
            
            for sock in ready_to_read:
                
                # a new connection request recieved
                if sock == server_socket: 
                    sockfd, addr = server_socket.accept()
                    SOCKET_LIST.append(sockfd)
                    print "Client (%s, %s) connected" % addr

                    # broadcast(server_socket, sockfd, "[%s:%s] entered our chatting room\n" % addr)
                    
                # a message from a client, not a new connection
                else:
                    # process data recieved from client, 
                    try:
                        # receiving data from the socket.
                        data = sock.recv(RECV_BUFFER)
                        
                        if data:
                            # there is something in the socket
                            handlemsg(server_socket, sock, data)
                            # broadcast(server_socket, sock, "\r" + '[' + str(sock.getpeername()) + '] ' + data)  
                        else:
                            print sock, 'sock removed'
                            # remove the socket that's broken    
                            if sock in SOCKET_LIST:
                                SOCKET_LIST.remove(sock)
                            # at this stage, no data means probably the connection has been broken
                            broadcast(server_socket, sock, "Client ({}) is offline\n".format( addr)) 

                    # exception 
                    except Exception as e:
                        print e, 'error in connection with client'
        except Exception as e:
            print e, 'error occurred'

    server_socket.close()
def handlemsg(server_socket, sock, message):
    if message == 'HELO text\n':
        print message + 'IP:{}\nPort:{}\nStudentID:{}\n'.format(sock.getsockname()[0], sock.getsockname()[1], studentId)
    elif message == 'KILL_SERVICE\n':
        print 'chat server is shutting down'
        import os
        os._exit(1)
    # chat messages
    else:
        print '====',message, '===='
        import re
        matchjoin = re.search(r'JOIN_CHATROOM:\s*\w+', message)
        # join room case:
        if matchjoin:
            room = matchjoin.group()
            roomprefix = room.find('JOIN_CHATROOM:')
            roomname = room[roomprefix+len('JOIN_CHATROOM:'):].strip()

            user = re.search(r'CLIENT_NAME:\s*\w+', message)
            conn_info = dict() 
            conn_info['serverip'] = getserverIP()
            conn_info['roomname'] = roomname
            # create chat room if no room before
            if roomname not in CHATROOM:

                CHATROOM[roomname]= dict()
                
                CHATROOM[roomname]['id'] = roomname+str(uuid.uuid1())
                CHATROOM[roomname]['users'] = []
                CHATROOM[roomname]['socks'] = []
            conn_info['roomref'] = CHATROOM[roomname]['id']
            # add user associated socks in chatroom
            if user:
                user = user.group()
                name = user[user.find('CLIENT_NAME:')+len('CLIENT_NAME:'):].strip()
                if name not in CHATROOM[roomname]['users']:
                    # add user into chat room
                    CHATROOM[roomname]['users'].append(name)
                    # associate sockets 
                    CHATROOM[roomname]['socks'].append(sock)
                else:
                    # shouldn't allow this
                    print 'user already joined....' 

            conn_info['joinid']=str(uuid.uuid4())
            sock.send(getresponse(conn_info))
            broadcastSameRoom(sock, CHATROOM[roomname]['socks'], message)
            print CHATROOM

# broadcast chat messages to connected clients in same chat room
def broadcastSameRoom(server_socket, socklist, message):
    for socket in socklist:
        # send the message only to peer
        if socket != server_socket:
            try :
                socket.send(message)
            except Exception as e:
                # broken socket connection
                print 'broadcast error', e
                socket.close()
                # broken socket, remove it
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)   

# populate response files with var inputs
def getresponse(variables):
    f = open("response/join_response","r")
    filestr = f.read()
    response = filestr.format(**variables)
    f.close()

    return response
def getserverIP():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        s.close()
        return s.getsockname()[0]
    finally:
        return '127.0.0.1'

# broadcast chat messages to all connected clients
def broadcast (server_socket, sock, message):
    for socket in SOCKET_LIST:
        # send the message only to peer
        if socket != server_socket and socket != sock :
            try :
                socket.send(message)
            except Exception as e:
                print 'broadcast error', e
                # broken socket connection
                socket.close()
                # broken socket, remove it
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)
 
if __name__ == "__main__":
    sys.exit(chat_server())   
