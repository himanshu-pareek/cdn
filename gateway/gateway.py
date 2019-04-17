import socket                   # Import socket module
import pickle
import os
import json
import threading
import time
import math 


PORT_ORIGIN = 10009
PORT_LBC = 20009
PORT_R = 20010


lock = threading.Lock()
lock2 = threading.Lock()

load_dict = {}
f = open('replica_ips.json', 'r')
data = json.load(f)
f.close()
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
		

def removeFromDict(key):

	lock.acquire()
	print ('Removing %s from dict' %(key))
	load_dict.pop(key, None)
	lock.release()
	lock2.acquire()
	f = open('replica_ips.json', 'r')
	data = json.load(f)
	f.close()
	if key in data['replica_ips_h']:
		data['replica_ips_h'].remove(key)
	new_key = key.replace('300','400')
	if new_key in data['replica_ips']:
		data['replica_ips'].remove(new_key)
	
	with open('replica_ips.json', 'w') as fp:
	    json.dump(data, fp)
	lock2.release()

def addInJson(key, value):

	lock.acquire()
	load_dict[key] = value
	lock.release()

	lock2.acquire()
	f = open('replica_ips.json', 'r')
	data = json.load(f)
	f.close()
	if key not in data['replica_ips_h']:
		data['replica_ips_h'].append(key)
	new_key = key.replace('_3','_4')
	if new_key not in data['replica_ips']:
		data['replica_ips'].append(new_key)
	
	with open('replica_ips.json', 'w') as fp:
	    json.dump(data, fp)
	lock2.release()


def getRepHealth(ip_port):
	ip = ip_port.split('_')[0]
	port = int(ip_port.split('_')[1])
	key = ip_port
	while(True):

		s = socket.socket()
		print("Trying to connect %s"%(ip_port))
		try :
			s.connect((ip, port))
		except:

			removeFromDict(key)
			try :
				print("Trying second time to connect") 
				s.connect((ip, port))
			except :
				try :
					print("Trying third time to connect")
					s.connect((ip, port))
				except:
					print("Tried 3 times but no response")
					s.close()
					time.sleep(10)
					sys.exit()
					continue



		s.send("What is your health?")
		h = int(s.recv(1024))
		print("Health of %s is %s"%(ip_port, h))
		
		addInJson(key, h)
		# s.shutdown(socket.SHUT_RDWR)
		s.close()
		time.sleep(10)



def getHealth():
	threadLis = []
	for value in h_lis:
		replicaThread = threading.Thread (target = getRepHealth, args= (value,))
		threadLis.append(replicaThread)

	for i in threadLis:
		i.start()


	for i in threadLis:
		i.join()



def handleRepWakeUp():
	s = socket.socket()             # Create a socket object
	host = socket.gethostname()     # Get local machine name
	s.bind((host, PORT_R))            # Bind to the port
	s.listen(5)                     # Now wait for client connection.
	print('Load balancer listening on port %d for replicas that just recovered'%(PORT_R))
	while(True):
		conn, addr = s.accept()
		if(conn.recv(1024) == "Just Woke up Need data"):
			lock.acquire()
			for key in load_dict:
				key = key.encode("utf-8")
				print ('key =', key)
				print ('load_dict[key] =', load_dict[key])
				if(min_load is None or min_load > int(load_dict[key])):
					min_load = int(load_dict[key])
					min_key = key
			ip_rep = min_key.split('_')[0]
			port_rep = '_2'+min_key.split('_')[1][1:]
			conn.send(ip_rep + port_rep)
			lock.release()
			conn.close()
		elif(conn.recv(1024) == "Recovered Now add me to yr replica list"):
			conn.send("Ready to add Tell me yr replica id")
			idd = conn.recv(1024)
			addInJson(addr[0]+"_" + idd, 0)
			conn.send("Sucessfully added")



def loadBalancer ():
	clientThread = threading.Thread (target = serveClient)
	healthThread = threading.Thread (target = getHealth)
	walkingUpRepThread = threading.Thread (target = handleRepWakeUp)

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

