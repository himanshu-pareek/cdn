# client.py

import socket                   # Import socket module
import pickle
import os

s = socket.socket()             # Create a socket object
host = socket.gethostname()     # Get local machine name
port = 40011
s.bind(('', port))            # Bind to the port
s.listen(5)                 # Reserve a port for your service.
print ('Replica 1 listening on port %d' %(port))


def receiveFile (s):
  s.send ('1')
  file_size = s.recv(1024)
  (filename, size) = file_size.split ('||||')
  s.send ('11')
  full_path = os.path.join (host, filename)
  fname = full_path.split('/')[-1]
  dir_path = '/'.join(full_path.split('/')[:-1])
  os.system("mkdir -p " + dir_path)

  with open(full_path, 'wb') as f:
    print ('file opened')
    chunks = int(size) / 1024
    last_size = int(size) - chunks * 1024
    for i in range (chunks):
      # print('receiving data...')
      data = s.recv(1024)
      # print('data=%s', (data))
      if not data:
          break
      # write data to a file
      f.write(data)

    data = s.recv (last_size)
    f.write (data)
    f.close()

  s.send ('111')

while True:
  conn, addr = s.accept()
  print ('Connected to origin')
  while True:
    if (conn.recv(1024) == '000'):
      receiveFile (conn)

s.close()
print('connection closed')


