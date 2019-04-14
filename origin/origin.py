import socket                   # Import socket module
import pickle
import os
import threading
import time 

def listenClient():
  s = socket.socket()             # Create a socket object
  host = socket.gethostname()     # Get local machine name
  port = port_client
  s.bind(('', port)) 
  print("Listening ..")
  while(True):
   conn, addr = s.accept()
   conn.recv(1024)
   f = open('gateway_LB.json', 'r')
   data = json.load(f)
   f.close()
   conn.send(data["gateway_ip"])
   conn.close()

def listenReplica():
  print("listening for replica for pull requests")



def main():
  repThread = threading.Thread (target=listenReplica)
  cliThread = threading.Thread (target=listenClient)

  repThread.start()
  cliThread.start()

  repThread.join()
  cliThread.join()

  print ("This will never get printed...")

if __name__ == "__main__":
  main ()