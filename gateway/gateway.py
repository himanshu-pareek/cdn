import socket                   # Import socket module
import pickle
import os
import json
import threading
import time 


PORT_ORIGIN = 10009
PORT_LBC = 20009



lock = threading.Lock()

load_dict = {}
f = open('replica_ips.json', 'r')
data = json.load(f)
lis = data['replica_ips_h']
for replica in lis:
	load_dict[replica] = 1
print("printing dict for first time")
for key in load_dict:
	key = key.encode("utf-8")
	print ('key =', key)
	print ('load_dict[key] =', load_dict[key])


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
		strng = conn.recv(1024)
		if(strng == "Allot me a replica"):
			min_key = ""
			min_load = None
			lock.acquire()
			for key in load_dict:
				key = key.encode("utf-8")
				print ('key =', key)
				print ('load_dict[key] =', load_dict[key])
				if(min_load is None or min_load > int(load_dict[key])):
					min_load = int(load_dict[key])
					min_key = key
			ip_rep = min_key.split('_')[0]
			port_rep = '_5'+min_key.split('_')[1][1:]
			conn.send(ip_rep + port_rep)
			lock.release()
		conn.close()
		
def getRepHealth(ip_port):
	ip = ip_port.split('_')[0]
	port = int(ip_port.split('_')[1])
	while(True):
		s = socket.socket()
		print("Trying to connect %s"%(ip_port))
		s.connect((ip, port))
		s.send("What is your health?")
		h = int(s.recv(1024))
		print("Health of %s is %s"%(ip_port, h))
		key = ip_port
		lock.acquire()
		load_dict[key] = h
		lock.release()
		# s.shutdown(socket.SHUT_RDWR)
		s.close()
		time.sleep(30)



def getHealth():
	threadLis = []
	for value in h_lis:
		replicaThread = threading.Thread (target = getRepHealth, args= (value,))
		threadLis.append(replicaThread)

	for i in threadLis:
		i.start()


	for i in threadLis:
		i.join()

def loadBalancer ():
	clientThread = threading.Thread (target = serveClient)
	healthThread = threading.Thread (target = getHealth)

	clientThread.start()
	healthThread.start()

	clientThread.join()
	healthThread.join()	



def main():
  originThread = threading.Thread (target=serveOrigin)
  LBThread = threading.Thread (target=loadBalancer)

  originThread.start()
  LBThread.start()

  originThread.join()
  LBThread.join()

  print ("This will never get printed...")

if __name__ == "__main__":
  main ()
# lis = os.listdir("../replica_servers")

