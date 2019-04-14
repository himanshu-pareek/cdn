import socket                   # Import socket module
import pickle
import os
import json
import threading
import time 


PORT_ORIGIN = 10009
PORT_LBC = 20009



lock = threading.lock()

load_dict = {}
f = open('replica_ips.json', 'r')
data = json.load(f)
lis = data['replica_ips']
for replica in lis:
	load_dict[replica] = 0


h_dict = {}
f = open('replica_ips.json', 'r')
data = json.load(f)
h_lis = data['replica_ips_h']


port_gateway = 50009                   # Reserve a port for your service.
s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
s.bind((host, port_gateway))            # Bind to the port
s.listen(5)                     # Now wait for client connection.

def serveOrigin():
	s = socket.socket()             # Create a socket object
	host = socket.gethostname()     # Get local machine name
	s.bind((host, PORT_ORIGIN))            # Bind to the port
	s.listen(5)                     # Now wait for client connection.
	f = open('replica_ips.json', 'r')
	data = json.load(f)
	lis = data['replica_ips']
	lis = '&'.join(lis)
	print('Gateway Server listening on port %d....'%(port_gateway))
	while(True):
		conn, addr = s.accept()
		if(conn.recv(1024) == 'alive'):
			conn.send(lis)
		conn.close()
	s.close()

def serveClient ():
	s = socket.socket()             # Create a socket object
	host = socket.gethostname()     # Get local machine name
	s.bind((host, PORT_LBC))            # Bind to the port
	s.listen(5)                     # Now wait for client connection.
	print('Load balancer listening on port %d for client request'%(PORT_LBC))
	while(True):
		conn, addr = s.accept()
		strng = s.recv(1024)
		if(strng = "Allot me a replica")
		min_key = ""
		min_load = None
		for key, value in enumerate(load_dict):
			if(min_load is None or min_load > int(value)):
				min_load = int(value)
				min_key = key
		lock.acquire()
		conn.send(min_key)
		lock.release()
		conn.close()
		
def getRepHealth(ip_port):
	ip = ip_port.split('_')[0]
	port = int(ip_port.split('_')[1])
	s = socket.socket()
	while(True):
		s.connect((ip, port))
		s.send("What is your health?")
		health = int(s.recv(1024))
		key = ip + "_5" + str(port)[1:]
		lock.acquire()
		load_dict[key] = health
		lock.release()
		time.sleep(30)
		s.close()



def getHealth():
	threadLis = []
	for value in h_lis:
		replicaThread = threading.Thread (target = getRepHealth, args= (value))
		threadLis.append(replicaThread)

	for i in threadLis:
		i.join()

def loadBalancer ():
	clientThread = threading.Thread (target = serveClient)
	healthThread = threading.Thread (target = getHealth)

	clientThread.start()
	healthThread.start()

	clientThread.join()
	healthThread.join()	



# lis = os.listdir("../replica_servers")

