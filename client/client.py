import socket                   # Import socket module
import pickle
import os
import threading
import time 


s = socket.socket()
host = "127.0.0.1"
port = 50010
s.connect((host, port))
s.send("a/get-pip.py")
LB = s.recv(1024)
s.close()
LB_ip = LB.split('_')[0]
LB_port = int(LB.split('_')[1])
s.connect((LB_ip, LB_port))
s.send("Allot me a replica")
replica = s.recv(1024)
s.close()
replica_ip = replica.split('_')[0]
replica_port = int(replica.split('_')[1])
s.connect((replica_ip, replica_port))
print(s.recv(1024))
