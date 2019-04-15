# client.py

import socket                   # Import socket module
import pickle
import os
import threading
import time 

lock = threading.Lock()
load = 0

REPLICA_ID = 2
OS_PORT = 40012
LB_PORT = 30012
C_PORT = 50012


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


def sendFile (conn, filename):
   print ('Inside sendFile with filename =', filename)
   conn.send ("000")
   res = conn.recv (1024)
   if (res != '1'):
      print ('Got', res, 'instead of 1')
      return
   filesize = os.path.getsize (filename)
   conn.send (filename + '||||' + str (filesize))
   if (conn.recv (1024) != '11'):
      return
   f = open(filename,'rb')

   l = f.read(1024)
   while (l):
      conn.send(l)
      #  print('Sent ',repr(l))
      l = f.read(1024)
   f.close()
   if (conn.recv (1024) == '111'):
      print ('Done sending ' + filename)
   else:
      print ('Error in sending ' + filename)

def share_dir(conn, dir_name):
   lis = os.listdir(dir_name)
   for i in lis:
      if(os.path.isdir(os.path.join(dir_name, i)) == 1):
         print ('Directory to share:', os.path.join(dir_name, i))
         share_dir(conn, os.path.join(dir_name, i))
      else:
         print ('File to send: ', os.path.join(dir_name, i))
         sendFile(conn, os.path.join(dir_name, i))
   print ('Almost Done sending all dirs')
   
   print ('Done sending dir : ', dir_name)




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
    fname = conn.recv(1024)
    try:
      fh = open(fname, 'r')
      fh.close()
      conn.send("File Found")
      sendFile(conn, fname)
    except FileNotFoundError:
      conn.send("File Not Found")



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



