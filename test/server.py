# server.py

import socket                   # Import socket module
import pickle

port = 60000                    # Reserve a port for your service.
s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
s.bind((host, port))            # Bind to the port
s.listen(5)                     # Now wait for client connection.

print('Server listening....')

class FileObject:
   
   def __init__(self, filename):
      self.filename = filename
      f = open (filename, 'rb')
      self.content = f.read()
      # self.size = len (content)
      f.close()

   def send (self, conn):
      serialized = pickle.dumps (self)
      size = len (serialized)
      conn.send (str(size))
      ack = conn.recv (1024)
      print ("ack = " + str (ack))
      conn.send (serialized)

def transferFile (conn, filename):
   fileObj = FileObject (filename)
   fileObj.send (conn)

# def transferDirectory (conn, dirname):


while True:
   conn, addr = s.accept()     # Establish connection with client.
   print ('Got connection from', addr)
   data = conn.recv(1024)

   filename='get-pip.py'
   transferFile (conn, filename)
   # f = open(filename,'rb')
   # l = f.read(1024)
   # print (type (l))
   # while (l):
   #    conn.send(l)
   #    #  print('Sent ',repr(l))
   #    l = f.read(1024)
   #    f.close()

   print('Done sending')
   conn.send('Thank you for connecting')
   conn.close()
