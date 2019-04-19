import socket                   # Import socket module
import pickle
import os
import json
import threading
import time
import math 
import sys
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-m", type=str, help="mode of operation")
args = vars(ap.parse_args())

PORT_ORIGIN = 10009
PORT_LBC = 20009
PORT_R = 40110
PORT_BACKUP = 10110
PORT_ORGIN_BACKUP = 50110


lock = threading.Lock()
lock2 = threading.Lock()

try:
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
except:
	pass

def serveOrigin():
	s = socket.socket()             # Create a socket object
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	host = socket.gethostname()     # Get local machine name
	s.bind(('', PORT_ORIGIN))            # Bind to the port
	s.listen(5)                     # Now wait for client connection.
	f = open('replica_ips.json', 'r')
	data = json.load(f)
	lis = data['replica_ips']
	lis = '&'.join(lis)
	print('Gateway Server listening on port %d....'%(PORT_ORIGIN))
	while(True):
		conn, addr = s.accept()

		f = open('origin_ips.json', 'r')
		data = json.load(f)
		f.close()

		if addr[0] not in data["origin_ips"]:
			data["origin_ips"].append(adr[0])

		with open('origin_ips.json', 'w') as fp:
			json.dump(data, fp)
			
		if(conn.recv(1024) == 'alive'):
			conn.send(lis)
		conn.close()
	s.close()

def serveClient ():
	s = socket.socket()             # Create a socket object
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	host = socket.gethostname()     # Get local machine name
	s.bind(('', PORT_LBC))            # Bind to the port
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
	print (load_dict)
	lock.release()

	lock2.acquire()
	f = open('replica_ips.json', 'r')
	data = json.load(f)
	f.close()
	if key not in data['replica_ips_h']:
		data['replica_ips_h'].append(key)
	new_key = key.replace('_3','_4')
	print ('New key in addInJson:', new_key)
	new_key = new_key.encode("utf-8")
	if new_key not in data['replica_ips']:
		data['replica_ips'].append(new_key)
	
	with open('replica_ips.json', 'w') as fp:
	    json.dump(data, fp)
	lock2.release()


def getRepHealth(ip_port):
	ip = ip_port.split('_')[0]
	with open('back_info.json', 'r') as f:
		ip_self = json.load(f)['ip_self']
	if(ip == ip_self):
		ip = socket.gethostname()
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
	p = socket.socket()
	p.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)             # Create a socket object
	host = socket.gethostname()     # Get local machine name
	p.bind(('', PORT_R))            # Bind to the port
	p.listen(5)                     # Now wait for client connection.
	print('Gateway listening on port %d for replicas that just recovered'%(PORT_R))
	while(True):
		print ('Ready to accept connections')
		conn, addr = p.accept()
		print ('connection received from', addr[0])
		rec = conn.recv (1024)
		if(rec == "Just Woke up Need data"):
			lock.acquire()
			min_load = None
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
		elif(rec == "Recovered Now add me to yr replica list"):

			conn.send("Ready to add Tell me yr replica id")
			idd = conn.recv(1024)
			key = addr[0]+"_" + idd
			key = key.encode("utf-8")
			addInJson(key, 0)
			conn.send("Sucessfully added")
			new_key = key.replace('_3', '_4')
			print (key, new_key)
			newreplicaThread = threading.Thread (target = getRepHealth, args= (key,))
			newreplicaThread.start()
		elif (rec == "Send replica list"):
			print("Sending replica list for replication to %s" %(addr[0]))
			f = open ('replica_ips.json', 'r')
			data = json.load (f)
			f.close()
			data = data['replica_ips']
			to_send = json.dumps ({"replica_ips": data})
			conn.send (to_send)
			print("Sent replica list for replication")
			msg = conn.recv(1024)
			print(msg)
			conn.close()

	p.close()


def handleBackup():
	s = socket.socket()             # Create a socket object
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	host = socket.gethostname()     # Get local machine name
	s.bind(('', PORT_BACKUP))            # Bind to the port
	s.listen(5)                     # Now wait for client connection.
	print('Gateway listening on port %d for backup'%(PORT_BACKUP))
	conn, addr = s.accept()
	while True:
		msg = conn.recv(1024)
		print ('msg:', msg)
		if (msg == "Please give snapshot"):
			to_send = json.dumps (load_dict)
			print ('to_send: ', to_send)
			conn.send (to_send)
			f = open ('origin_ips.json', 'r')
			origin_dict = json.load (f)
			f.close()
			to_send = json.dumps (origin_dict)
			if (conn.recv (1024) == 'received'):
				conn.send (to_send)
				if (conn.recv(1024) == 'Snapshot received'):
					print ('Snapshot sent successfully')

def loadBalancer ():
	clientThread = threading.Thread (target = serveClient)
	healthThread = threading.Thread (target = getHealth)
	walkingUpRepThread = threading.Thread (target = handleRepWakeUp)

	clientThread.start()
	healthThread.start()
	walkingUpRepThread.start()

	clientThread.join()
	healthThread.join()	
	walkingUpRepThread.join()





def normal_mode():
  originThread = threading.Thread (target=serveOrigin)
  LBThread = threading.Thread (target=loadBalancer)
  backupThread = threading.Thread (target = handleBackup)

  originThread.start()
  LBThread.start()
  backupThread.start()

  originThread.join()
  LBThread.join()
  backupThread.join()

  print ("This will never get printed...")

def getSnapshot(s):
	s.send ("Please give snapshot")
	msg = s.recv(1024)
	print (msg)
	s.send ('received')
	msg2 = s.recv (1024)
	s.send ('Snapshot received')
	load_dict = json.loads (msg)
	data = {
		'replica_ips_h': [],
		'replica_ips': []
	}
	for key in load_dict:
		data['replica_ips_h'].append (key)
		new_key = key.replace ('_3', '_4')
		data['replica_ips'].append (new_key)
	print ('Trying to write data into file')
	with open('replica_ips.json', 'w') as fp:
	    json.dump(data, fp)

	origin_dict = json.loads (msg2)
	with open('origin_ips.json', 'w') as fp:
	    json.dump(origin_dict, fp)
	print ('Successfully written')

def pingOriginFunc(ip):
	s = socket.socket()
	with open('back_info.json', 'r') as f:
		ip_self = json.load(f)['ip_self']
	if(ip == ip_self):
		ip = socket.gethostname()
	s.connect((ip, PORT_ORGIN_BACKUP))
	s.send("I am the new gateway cum load balancer")
	if(s.recv(1024) == "Sure"):
		f = open('back_info.json', 'r')
		data = json.load(f)
		f.close()
		s.send(data['ip_self'])
		if(s.recv(1024) == "Updated the Gateway"):
			print("Sucessfully updated the gateway ip in the origin")
			s.close()
			# sys.exit()

def pingReplicaFunc(ip_port):

	f = open ('back_info.json', 'r')
	data = json.load (f)
	f.close()
	ip_to_send = data['ip_self']
	ip_port = ip_port.replace('_4', '_3')
	s = socket.socket()
	ip = ip_port.split('_')[0]
	port = int(ip_port.split('_')[1])
	print('Pinging Replica for the new Gateway server')
	with open('back_info.json', 'r') as f:
		ip_self = json.load(f)['ip_self']
	if(ip == ip_self):
		ip = socket.gethostname()
	s.connect((ip, port))
	s.send("I am the new gateway")
	if(s.recv(1024) == "received"):
		s.send(ip_to_send)
		if(s.recv(1024) == 'done'):
			s.close()
			# sys.exit()


def backup ():
	s = socket.socket()
	f = open ('back_info.json', 'r')
	data = json.load (f)
	f.close()
	main_server_ip = data['ip']
	main_server_port = data['port']
	with open('back_info.json', 'r') as f:
		ip_self = json.load(f)['ip_self']
	if(main_server_ip == ip_self):
		main_server_ip = socket.gethostname()
	s.connect ((main_server_ip, main_server_port))
	print ('Connected to main server')
	flag = 0
	while True:
		try:
			print ('Trying to get snapshot')
			getSnapshot(s)
			print ('Snapshot got in first attempt')
			# time.sleep (10)
		except:
			time.sleep(1)
			try:
				print ('Trying to get snapshot 2nd time')
				getSnapshot(s)
				print ('Snapshot got in second attempt')
			except:
				time.sleep(1)
				try:
					print ('Trying to get snapshot 3rd time')
					getSnapshot(s)
					print ('Snapshot got in third attempt')
				except:
					# Main server is crashed bro, do something
					print ('Main server is dead bro')
					s.close()
					flag =1
					break
		
		time.sleep(10)
	if(flag):
		f = open('origin_ips.json', 'r')
		data = json.load(f)
		f.close()
		origin_list = data["origin_ips"]
		originThreadLis = []
		for i in origin_list:
			pingOrigin =  threading.Thread (target=pingOriginFunc, args = (i,))
			originThreadLis.append(pingOrigin)

		f = open('replica_ips.json', 'r')
		data = json.load(f)
		f.close()
		replica_list = data["replica_ips"]
		replicaThreadLis = []
		for i in replica_list:
			pingReplica =  threading.Thread (target=pingReplicaFunc, args = (i,))
			replicaThreadLis.append(pingReplica)

		for i in originThreadLis:
			i.start()


		for i in replicaThreadLis:
			i.start()


		for i in originThreadLis:
			i.join()

		for i in replicaThreadLis:
			i.join()
		print("Running as Main Gateway Server")
		main('n')



def main(mode):
	if mode == 'n':
		normal_mode()
	else:
		backup()


if __name__ == "__main__":
	mode = args['m']
 	main (mode)
# lis = os.listdir("../replica_servers")

