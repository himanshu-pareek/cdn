import socket                   # Import socket module
import pickle
import os

port_gateway = 50010                   # Reserve a port for your service.
s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
s.bind((host, port_gateway))            # Bind to the port
s.listen(5)                     # Now wait for client connection.

lis = os.listdir("../replica_servers")
lis = '&'.join(lis)
print('Gateway Server listening on port %d....'%(port_gateway))
while(True):
	conn, addr = s.accept()
	if(conn.recv(1024) == 'alive'):
		conn.send(lis)
	conn.close()
s.close()	
