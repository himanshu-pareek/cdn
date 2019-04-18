import socket                   # Import socket module
import pickle
import os
import threading
import time 
import json

port_client = 50010
PORT_ORGIN_BACKUP = 50110
PORT_LISTEN_REPLICA = 45010



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


def listenClient():
  s = socket.socket()             # Create a socket object
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  host = socket.gethostname()     # Get local machine name
  port = port_client
  s.bind(('', port)) 
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
  s = socket.socket()             # Create a socket object
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  host = socket.gethostname()     # Get local machine name
  port = PORT_LISTEN_REPLICA
  s.bind(('', port)) 
  s.listen(5)
  print("Listening ..")
  while(True):
    conn, addr = s.accept()
    if(conn.recv(1024) == "Send me updated file"):
      conn.send("Give me file name")
      fname = conn.recv(1024)
      try :
        f = open(fname, 'r')
        f.close()
        sendFile(conn, fname)
      except:
        conn.send("File Not Found")



def backupGateway():
  s = socket.socket()             # Create a socket object
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  host = socket.gethostname()     # Get local machine name
  port = PORT_ORGIN_BACKUP
  s.bind(('', port)) 
  s.listen(5)
  print("Listening ..")
  while(True):
    conn, addr = s.accept()
    print("Got a connection from backup")
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