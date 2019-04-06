# client.py

import socket                   # Import socket module
import pickle

class FileObject:
   
   def __init__(self, filename):
      self.filename = filename
      f = open (filename, 'rb')
      self.content = f.read()
      f.close()

   def send (self, conn):
      serialized = pickle.dumps (self)
      conn.send (serialized)

    # def receive (self, conn):
    #     serialized = conn.receive(1024)
    #     FileObject newObj = pickle.loads(serialized)
    #     f = open (newObj.filename, 'wb')
    #     f.write (newObj.content)
    #     f.close()


def transferFile (conn, filename):
   fileObj = FileObject (filename)
   fileObj.send (conn)

s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
port = 60000                    # Reserve a port for your service.

s.connect((host, port))
s.send("Hello server!")

size = int(s.recv (1024))
s.send ('1')

serialized = s.recv(size)
print (len(serialized))
newObj = pickle.loads(serialized)

f = open ('new_' + newObj.filename, 'wb')
f.write (newObj.content)
f.close()

# with open('received_file.py', 'wb') as f:
#     print ('file opened')
#     while True:
#         print('receiving data...')
#         data = s.recv(1024)
#         # print('data=%s', (data))
#         if not data:
#             break
#         # write data to a file
#         f.write(data)

# f.close()
# print('Successfully get the file')
s.close()
print('connection closed')


