# client.py

import socket                   # Import socket module
import pickle
import os
import threading
import time 

lock = threading.Lock()
load = 0

REPLICA_ID = 0
OS_PORT = 40010
LB_PORT = 30010
C_PORT = 50010


def receiveFile (s, addr):
  host = addr[0]
  s.send ('1')
  file_size = s.recv(1024)
  (filename, size) = file_size.split ('||||')
  size = int(size)
  print ("File size =", size)
  s.send ('11')
  full_path = os.path.join (host, filename)
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

def health ():
  s = socket.socket()             # Create a socket object
  host = socket.gethostname()     # Get local machine name
  port = LB_PORT
  s.bind(('', port))            # Bind to the port
  s.listen(1)                 # Reserve a port for your service.
  print ('Replica %d listening on port %d for LB' %(REPLICA_ID, port))
  while True:
    conn, addr = s.accept ()
    if (conn.recv (1024) == "What is your health?"):
      # Send load to LB
      lock.acquire()
      conn.send (str(load))
      lock.release()
      conn.close()

def receiveFromOrigin ():
  s = socket.socket()             # Create a socket object
  host = socket.gethostname()     # Get local machine name
  port = OS_PORT
  s.bind(('', port))            # Bind to the port
  s.listen(5)                 # Reserve a port for your service.
  print ('Replica %d listening on port %d for origin server' %(REPLICA_ID, port))

  while True:
    conn, addr = s.accept()
    host = addr[0]
    print ('Connected to origin')
    while True:
      res = conn.recv (1024)
      # print ('res from origin =', res)
      if (res == '000'):
        receiveFile (conn, addr)
      elif (res == '###'):
        conn.close()
        break

  s.close()
  print('connection closed')

def serveClient ():
  s = socket.socket()             # Create a socket object
  host = socket.gethostname()     # Get local machine name
  port = C_PORT
  s.bind(('', port))            # Bind to the port
  s.listen(5)                 # Reserve a port for your service.
  print ('Replica %d listening on port %d for client' %(REPLICA_ID, port))
  # Serve client
  while(True):
    conn, addr = s.accept()
    conn.send("Welcome to the world of CDN")
    

def main():
  lbThread = threading.Thread (target=health)
  osThread = threading.Thread (target=receiveFromOrigin)
  cliThread = threading.Thread (target=serveClient)

  lbThread.start()
  osThread.start()
  cliThread.start()

  lbThread.join()
  osThread.join()
  cliThread.join()

  print ("This will never get printed...")

if __name__ == "__main__":
  main ()



