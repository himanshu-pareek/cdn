# client.py

import socket                   # Import socket module
import pickle
import os
import threading
import time 
import sys
import select
import argparse
import json
import fcntl
import struct

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

ap = argparse.ArgumentParser()
ap.add_argument("-m", type=str, help="mode of operation")
args = vars(ap.parse_args())

lock = threading.Lock()

REPLICA_ID = 0
OS_PORT = 40010
LB_PORT = 30010
C_PORT = 50010
PORT_R = 20010

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
  s.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  host = socket.gethostname()     # Get local machine name
  port = LB_PORT
  s.bind(('', port))            # Bind to the port
  s.listen(1)                 # Reserve a port for your service.
  print ('Replica %d listening on port %d for LB' %(REPLICA_ID, port))
  while True:
    conn, addr = s.accept ()
    msg = conn.recv (1024)
    if (msg == "What is your health?"):
      # Send load to LB
      lock.acquire()
      conn.send (str(load))
      lock.release()
      conn.close()
    elif (msg == "I am the new gateway"):
      print("Got info about new gateway")
      conn.send ("received")
      new_ip_gateway = conn.recv (1024)
      conn.send ('done')
      with open ('config.json', 'r') as f:
        if json.load (f)['ip_self'] == new_ip_gateway:
          new_ip_gateway = 'localhost'
      f = open ('gateway_ip.json', 'r')
      data_to_read = {
        'gateway': new_ip_gateway
      }
      with open ('gateway_ip.json', 'w') as f:
        json.dump (data_to_read, f)
      conn.close()

def receiveFromOrigin ():
  s = socket.socket()             # Create a socket object
  s.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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

def share_dir(conn, dir_name):
   if(os.path.isdir(os.path.join(dir_name)) != 1):
      sendFile(conn, dir_name)
      return 
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

# def share_dir(conn, dir_name):
#    lis = os.listdir(dir_name)
#    for i in lis:
#       if(os.path.isdir(os.path.join(dir_name, i)) == 1):
#          print ('Directory to share:', os.path.join(dir_name, i))
#          share_dir(conn, os.path.join(dir_name, i))
#       else:
#          print ('File to send: ', os.path.join(dir_name, i))
#          sendFile(conn, os.path.join(dir_name, i))
#    print ('Almost Done sending all dirs')
   
#    print ('Done sending dir : ', dir_name)

def serveClientThFunc(conn, addr):
  global load
  lock.acquire()
  load += 1
  lock.release()
  conn.send("Welcome to the world of CDN")
  if(conn.recv(1024) == "Give me this file"):
    conn.send("Ready")
    fname = conn.recv(1024)
    print (fname)
    try:
      fh = open(fname, 'r')
      fh.close()
      conn.send("File Found")
      try:
        sendFile(conn, fname)
      except:
        conn.close()
        lock.acquire()
        load -= 1
        lock.release()
        sys.exit()
    except:
      conn.send("File Not Found")
    conn.close()
    lock.acquire()
    load -= 1
    lock.release()
  sys.exit()

def serveClient ():
  s = socket.socket()             # Create a socket object
  s.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  host = socket.gethostname()     # Get local machine name
  port = C_PORT
  s.bind(('', port))            # Bind to the port
  s.listen(5)                 # Reserve a port for your service.
  print ('Replica %d listening on port %d for client' %(REPLICA_ID, port))
  # Serve client
  serveClientThreadLis = []
  while(True):
    conn, addr = s.accept()
    serveCli =  threading.Thread (target=serveClientThFunc, args = (conn, addr))
    serveClientThreadLis.append(serveCli)
    serveCli.start()
    
def serveReplica():
  s = socket.socket()             # Create a socket object
  s.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  host = socket.gethostname()     # Get local machine name
  s.bind((host, PORT_R))            # Bind to the port
  s.listen(5)                     # Now wait for client connection.
  print('Replica listening on port %d for replicas that just recovered'%(PORT_R))
  while(True):
    conn, addr = s.accept()
    if(conn.recv(1024) == "Data Please !!"):
      dirlist = os.listdir('.')
      for dirname in dirlist:
        if (os.path.isdir (dirname)):
          # dirname is a dir
          # we want to share it
          share_dir (conn, dirname)
      conn.send("&&&")
    conn.close()

def wakingUp():
  f = open('gateway_ip.json', 'r')
  data = json.load(f)
  f.close()
  gateway_ip_port  = data["gateway"]
  (gateway_ip, gateway_port) = gateway_ip_port.split('_')
  gateway_ip = gateway_ip.encode ("utf-8")
  gateway_port = int(gateway_port.encode ("utf-8"))
  s = socket.socket()
  print ("Gateway IP: %s and Gateway Port: %d" %(gateway_ip, gateway_port))
  s.connect((gateway_ip, gateway_port))
  s.send("Just Woke up Need data")
  ip_port = s.recv(1024)
  replica_ip = ip_port.split('_')[0] 
  replica_port = int(ip_port.split('_')[1])
  s.close()
  s = socket.socket()
  replica_ip = socket.gethostname()
  print ('Replica IP: %s and Replica Port: %d' %(replica_ip, replica_port))
  s.connect((replica_ip, replica_port))
  s.send("Data Please !!")
  while(True):
    received = s.recv(1024)
    if(received == '000'):
      receiveFile (s, ["", ""])
    elif(received == "&&&"):
      print ('Received &&&')
      s.close()
      break

  print ('outside while loop')
  s = socket.socket()
  s.connect((gateway_ip, gateway_port))
  s.send("Recovered Now add me to yr replica list")
  if(s.recv(1024) == "Ready to add Tell me yr replica id"):
    s.send(str(LB_PORT))
    if(s.recv(1024) == "Sucessfully added"):
      main("n")



def main(mode):
  global load
  load = 0

  if(mode == "n"):

    lbThread = threading.Thread (target=health)
    osThread = threading.Thread (target=receiveFromOrigin)
    cliThread = threading.Thread (target=serveClient)
    repThread = threading.Thread (target = serveReplica)

    lbThread.start()
    osThread.start()
    cliThread.start()
    repThread.start()

    lbThread.join()
    osThread.join()
    cliThread.join()
    repThread.join()

    print ("This will never get printed...")
  
  else :
    wakingUp()

  

  

if __name__ == "__main__":
  mode = args["m"]
  main(mode)



