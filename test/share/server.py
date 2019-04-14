# client.py

import socket                   # Import socket module
import pickle
import os

port = 60011                   # Reserve a port for your service.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # Create a socket object
# host = socket.gethostname('')
# Get local machine name

s.bind(('localhost', port))            # Bind to the port
s.listen(5)                     # Now wait for client connection.

print('Server listening....')

def sendFile (conn, filename):

   conn.send ("000")
   if (conn.recv(1024) != '1'):
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
         share_dir(conn, os.path.join(dir_name, i))
      else:
         sendFile(conn, os.path.join(dir_name, i))


while True:
   conn, addr = s.accept()    # Establish connection with client.
   print ('Got connection from', addr)
   # data = conn.recv(1024)
   sendFile(conn, 'get-pip.py')
   # lis = os.listdir (path)
   # for filename in lis:
   #    filename = os.path.join (path, filename)
   #    sendFile (conn, filename)
   conn.send('Thank you for connecting')
   conn.close()
