import socket                   # Import socket module
import pickle
import os
import threading
import time 
import json

port_client = 50010
PORT_ORGIN_BACKUP = 50110

def listenClient():
  s = socket.socket()             # Create a socket object
  host = socket.gethostname()     # Get local machine name
  port = port_client
  s.bind(('', port)) 
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  s.listen(5)
  print("Listening ..")
  while(True):
   conn, addr = s.accept()
   print("Got a connection from client")
   conn.recv(1024)
   f = open('gateway_LB.json', 'r')
   data = json.load(f)
   f.close()
   conn.send(data["gateway_ip"])
   conn.close()

def listenReplica():
  print("listening for replica for pull requests")


def backupGateway():
  s = socket.socket()             # Create a socket object
  host = socket.gethostname()     # Get local machine name
  port = PORT_ORGIN_BACKUP
  s.bind(('', port)) 
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  s.listen(5)
  print("Listening ..")
  while(True):
    conn, addr = s.accept()
    if(conn.recv(1024) == "I am the new gateway cum load balancer"):
      conn.send("Sure")
      ip = conn.recv(1024)
      data = {"gateway_ip" : ip}
      with open('gateway_LB.json', 'w') as fp:
        json.dump(data, fp)
      conn.send("Updated the Gateway")



def main():
  repThread = threading.Thread (target=listenReplica)
  cliThread = threading.Thread (target=listenClient)
  backupThread = threading.Thread (target = backupGateway)

  repThread.start()
  cliThread.start()

  repThread.join()
  cliThread.join()

  print ("This will never get printed...")

if __name__ == "__main__":
  main ()