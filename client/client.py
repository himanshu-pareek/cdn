import socket                   # Import socket module
import pickle
import os
import threading
import time 

def receiveFile (s, addr):
  host = addr[0]
  if(s.recv(1024) != "000"):
  	return
  s.send ('1')
  file_size = s.recv(1024)
  (filename, size) = file_size.split ('||||')
  size = int(size)
  print ("File size =", size)
  s.send ('11')
  full_path = os.path.join (filename)
  fname = full_path.split('/')[-1]
  dir_path = '/'.join(full_path.split('/')[:-1])
  os.system("mkdir -p " + dir_path)

  with open(full_path, 'wb') as f:
    print ('file opened')
    chunks = size / 1024
    last_size = size - chunks * 1024
    print ('(chunks, last_size) -> (%d, %d)' %(chunks, last_size))
    received = 0
    while received < size:
      data = s.recv (size - received)
      f.write (data)
      received += len (data)
  print ('file closed:', full_path)
  s.send ('111')


def connectOrigin():
	s = socket.socket()
	host = "localhost"
	# host = socket.gethostbyname("127.0.0.1")
	port = 50010
	if host == "localhost" or host == "127.0.0.1":
		host = socket.gethostname()
	s.connect((host, port))
	s.send("a/get-pip.py")
	LB = s.recv(1024)
	s.close()
	return LB

def connectLB(LB):
	LB_ip = LB.split('_')[0]
	if LB_ip == "localhost" or LB_ip == "127.0.0.1":
		LB_ip = socket.gethostname()
	LB_port = int(LB.split('_')[1])
	print (LB_ip, LB_port)
	s = socket.socket()
	s.connect((LB_ip, LB_port))
	s.send("Allot me a replica")
	replica = s.recv(1024)
	s.close()
	return replica


def connectReplica(replica, fname):

	replica_ip = replica.split('_')[0]
	replica_port = int(replica.split('_')[1])
	print (replica_ip, replica_port)
	s = socket.socket()
	s.connect((replica_ip, replica_port))
	strng = s.recv(1024)
	print("Message from the replica server : ", strng)
	if(strng == "Welcome to the world of CDN"):
		s.send("Give me this file")
		if(s.recv(1024) != "Ready"):
			s.close()
			return
		s.send(fname)
		if(s.recv(1024) == "File Found"):
			receiveFile (s, replica_ip)
		else:
			print("Error 404 File Not Found")

		s.close()
	
	


def main():
	threshold = 5
	LB = connectOrigin()
	replica  = connectLB(LB)
	st  = time.time()
	while(True):
		fname = raw_input("Enter filename to fetch\n")
		print(fname)
		connectReplica(replica, fname)
		if((time.time() - st) > threshold):
			main()





if __name__ == "__main__":
	main()
