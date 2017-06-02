#!/usr/bin/python
# This is a simple port-forward / proxy, written using only the default python
# library. If you want to make a suggestion or fix something you can contact-me
# at voorloop_at_gmail.com
# Distributed over MIT license
import socket
import select
import time
import sys
import getopt

buffer_size = 4096
forward_to = ('www.voorloopnul.com', 80)

FORWARD_IP = ''
FORWARD_PORT = ''
FORWARD_IP_VERSION = 'IPv4'

class Forward:
    def __init__(self, ip_version):
        if ip_version == 'IPv4':
	    self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	else:
	    self.forward = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as inst:
            print("[exception] - {0}".format(inst.strerror))
            return False    

class TheServer:
    input_list = []
    channel = {}

    def __init__(self, host, port, ip_version):
        if ip_version == 'IPv4':
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	else:
            self.server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def main_loop(self):
        self.input_list.append(self.server)
        while 1:
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for s in inputready:
                if s == self.server:
                    self.on_accept(s)
                    break

                self.data = s.recv(buffer_size)
                if len(self.data) == 0:
                    self.on_close(s)
                    break
                else:
                    self.on_recv(s)

    def on_accept(self, s):
	global FORWARD_IP
	global FORWARD_PORT
	global FORWARD_IP_VERSION
	print "Will forward to IP " + FORWARD_IP + " Port " + FORWARD_PORT + " (" + FORWARD_IP_VERSION + ")"
        #forward = Forward(FORWARD_IP_VERSION).start(FORWARD_IP, int(FORWARD_PORT))
        forward = Forward(FORWARD_IP_VERSION).start(FORWARD_IP, FORWARD_PORT)
        clientsock, clientaddr = self.server.accept()
        if forward:
            print("{0} has connected".format(clientaddr))
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            print("Can't establish a connection with remote server. Closing connection with client side {0}".format(clientaddr))
            clientsock.close()

    def on_close(self, s):
        print("{0} has disconnected".format(s.getpeername()))
        #remove objects from input_list
        self.input_list.remove(s)
        self.input_list.remove(self.channel[s])
        out = self.channel[s]
        # close the connection with client
        self.channel[out].close()  
        # close the connection with remote server
        self.channel[s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[s]

    def on_recv(self, s):
        data = self.data
        # here we can parse and/or modify the data before send forward
        print(data)
        self.channel[s].send(data)

def display_usage():
    print 'python proxy.py -l ipaddr,port -f ipaddr:port'
    print 'Examples:'
    print 'python proxy.py -l 10.102.144.118,4995 -f 172.18.0.3,5995'
    print 'python proxy.py -l 172.18.0.3,5995 -f 128.0.0.16,6995'
    print 'python proxy.py -l 172.18.0.1,60051 -f 10.163.18.76,50051'
 

def main(argv):
    global FORWARD_IP
    global FORWARD_PORT
    global FORWARD_IP_VERSION
    listen_arg = ''
    forward_arg = ''
    try:
       opts, args = getopt.getopt(argv,"hl:f:",["listen=","forward="])
    except getopt.GetoptError:
       display_usage()
       sys.exit(2)
    for opt, arg in opts:
       if opt in ("-h", "?", "-?", "--help"):
          display_usage()
          sys.exit()
       elif opt in ("-l", "--listen"):
          listen_arg = arg
       elif opt in ("-f", "--forward"):
          forward_arg = arg
    #print 'listen_arg  :', listen_arg
    #print 'forward_arg :', forward_arg

    if listen_arg == '':
       display_usage()
       sys.exit(2)

    if forward_arg == '':
       display_usage()
       sys.exit(2)


    LISTEN_IP,LISTEN_PORT = listen_arg.split(",")
    if ':' in LISTEN_IP:
        LISTEN_IP_VERSION='IPv6'
    else:
        LISTEN_IP_VERSION='IPv4'

    FORWARD_IP,FORWARD_PORT = forward_arg.split(",")
    if ':' in FORWARD_IP:
        FORWARD_IP_VERSION='IPv6'
    else:
        FORWARD_IP_VERSION='IPv4'

    server = TheServer(LISTEN_IP, int(LISTEN_PORT), LISTEN_IP_VERSION)
    print "Listening on IP " + LISTEN_IP + " Port " + LISTEN_PORT + " (" + LISTEN_IP_VERSION + ")"
    print "Will forward to IP " + FORWARD_IP + " Port " + FORWARD_PORT + " (" + FORWARD_IP_VERSION + ")"
    try:
	server.main_loop()
    except KeyboardInterrupt:
	print "Ctrl C - Stopping server"
        sys.exit(1)


if __name__ == "__main__":
   main(sys.argv[1:])

