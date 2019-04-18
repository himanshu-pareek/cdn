import socket                   # Import socket module
import pickle
import os
import threading
import time 


f = open('gateway_LB.json', 'r')
data = json.load(f)
f.close()
gateway_ip = data["gateway_ip"]

s = socket.socket()             # Create a socket object
port_gateway = 50009 
port_client = 50010                # Reserve a port for your service.

s.connect((gateway_ip, port_gateway))

print("Connected")
s.send("alive")
lis = s.recv(1024)
lis = lis.split('&')
print(lis)
s.close()
print("Done !!")

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
   if(os.path.isdir(os.path.join(dir_name, i)) != 1):
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

for i in lis:
   host = socket.gethostbyname(i.split('_')[0])     # Get local machine name
   replica_port = i.split('_')[1]
   print ('Trying to connect to %s on port %d' %(host, int(replica_port)))
   s = socket.socket()
   s.connect((host, int(replica_port)))
   share_dir(s, 'a')
   s.send('###')
   s.close()
   break          

