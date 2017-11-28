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
CHATROOMAP = dict()
SOCKETMAP = dict()
CLIENTROOMMAP = dict()
SOCKETCLIENTMAP = dict()


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
                                clientname = SOCKETCLIENTMAP[sock]
                                rooms = CLIENTROOMMAP[clientname]                            
                                # remove users/sockets from all chat rooms
                                
                                for room in rooms:
                                    CHATROOM[room]['socks'].remove(sock)
                                    CHATROOM[room]['users'].remove(clientname)
                                SOCKETCLIENTMAP.pop(sock,None)    
                                CLIENTROOMMAP.pop(clientname,None)
                                

                            
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
        print '====\n',message, '\n===='
        import re
        matchjoin = re.search(r'JOIN_CHATROOM:\s*.+', message)
        matchchat = re.search(r'CHAT:\s*.+', message)
        matchleave = re.search(r'LEAVE_CHATROOM:\s*.+', message)
        matchdiscon = re.search(r'DISCONNECT:\s*.+', message)
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
                CHATROOM[roomname]['id'] = str(len(CHATROOM))
                CHATROOM[roomname]['users'] = []
                CHATROOM[roomname]['socks'] = []
            # update roomref
            roomid = conn_info['roomref'] = CHATROOM[roomname]['id']
            CHATROOMAP[roomid] = roomname
            # add user associated socks in chatroom
            joinmsg = message
            if user:
                user = user.group()
                name = user[user.find('CLIENT_NAME:')+len('CLIENT_NAME:'):].strip()
                joinmsg = name + ' has joined this chatroom.'
                if name not in CHATROOM[roomname]['users']:
                    # add user into chat room
                    CHATROOM[roomname]['users'].append(name)
                    # add sockets 
                    CHATROOM[roomname]['socks'].append(sock)
                    # associate sockets and users
                    SOCKETMAP[name]=sock

                    SOCKETCLIENTMAP[sock]=name
                    # associate user and chatroom
                    if name not in CLIENTROOMMAP:
                        CLIENTROOMMAP[name] = []
                    CLIENTROOMMAP[name].append(roomname)

                else:
                    # shouldn't allow this
                    print 'user already joined....' 
            # update joinid
            conn_info['joinid']=len(CHATROOM[roomname]['socks'])
            sock.send(getresponse(conn_info,'join_response'))

            # broadcast join
            broadcastSameRoom(sock, roomid, joinmsg)
        elif matchchat:
            messageinfo = re.search(r'MESSAGE:\s*.+', message).group()
            messageinfo = messageinfo[messageinfo.index('MESSAGE:')+len('MESSAGE:'):].strip()
            roominfo = re.search(r'CHAT:\s*.+', message).group()
            roominfo = roominfo[roominfo.index('CHAT:')+len('CHAT:'):].strip()
            clientname = re.search(r'CLIENT_NAME:\s*.+', message).group()
            clientname = clientname[clientname.index('CLIENT_NAME:')+len('CLIENT_NAME:'):].strip()

            chatresponse=dict()
            chatresponse['message']=messageinfo
            chatresponse['roomref']=roominfo
            chatresponse['clientname']=clientname

            message = getresponse(chatresponse,'chat_response')

            print 'broadcasting chat message', message,'====='
            broadcastSameRoom(None, roominfo, message)
        elif matchleave:
            print 'responding leavinggggg'
            joinid = re.search(r'JOIN_ID:\s*.+', message).group()
            joinid = joinid[joinid.index('JOIN_ID:')+len('JOIN_ID:'):].strip()
            roominfo = re.search(r'LEAVE_CHATROOM:\s*.+', message).group()
            roominfo = roominfo[roominfo.index('LEAVE_CHATROOM:')+len('LEAVE_CHATROOM:'):].strip()
            clientname = re.search(r'CLIENT_NAME:\s*.+', message).group()
            clientname = clientname[clientname.index('CLIENT_NAME:')+len('CLIENT_NAME:'):].strip()

            leaveresponse=dict()
            leaveresponse['roomref']=roominfo
            leaveresponse['joinid']=joinid

            # remove socks
            if clientname in SOCKETMAP and roominfo in CHATROOMAP:
                sock = SOCKETMAP[clientname]
                roomname = CHATROOMAP[roominfo]
                CHATROOM[roomname]['socks'].remove(sock)
                CHATROOM[roomname]['users'].remove(clientname)
                CLIENTROOMMAP[clientname].remove(roomname)


                message = getresponse(leaveresponse,'leave_response')
                # repond leave
                
                sock.send(message)

                # broadcast
                leavemsg = clientname + ' has left this chatroom.'
                broadcastSameRoom(sock, roominfo, leavemsg)
            else:
                print 'client or room info does not exists'
        elif matchdiscon:
            clientname = re.search(r'CLIENT_NAME:\s*.+', message).group()
            clientname = clientname[clientname.index('CLIENT_NAME:')+len('CLIENT_NAME:'):].strip()
            # remove socks and users from chatroom
            scktorm = SOCKETMAP[clientname]
            rooms = CLIENTROOMMAP[clientname]

            print 'remove user/socks from chat room'
            print rooms

            for room in rooms:
                if clientname in CHATROOM[room]['users']:
                    CHATROOM[room]['users'].remove(clientname)
                if scktorm in CHATROOM[room]['socks']:
                    CHATROOM[room]['socks'].remove(scktorm)

            # close socket 
            if scktorm in SOCKET_LIST:
                SOCKET_LIST.remove(sock)
        else:
            print ' nothing matched', 
        print CHATROOM

# broadcast chat messages to connected clients in same chat room
def broadcastSameRoom(sock, roominfo, message):

    if roominfo in CHATROOMAP :
        socklist = CHATROOM[CHATROOMAP[roominfo]]['socks']

        for socket in socklist:
            # send the message only to peer
            if socket is not sock:
                try :
                    socket.send(message)
                except Exception as e:
                    # broken socket connection
                    print 'broadcast error', e
                    socket.close()
                    # broken socket, remove it
                    if socket in SOCKET_LIST:
                        SOCKET_LIST.remove(socket)   
    else:
        print 'no roominfo in chatroom', roominfo

# populate response files with var inputs
def getresponse(variables, name):
    f = open("response/"+name,"r")
    filestr = f.read()
    response = filestr.format(**variables)
    f.close()
    print 'response: '+ response
    return response

def getserverIP():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        s.close()
        return s.getsockname()[0]
    except:
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
