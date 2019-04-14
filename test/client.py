# client.py

import socket                   # Import socket module
import pickle
import os

s = socket.socket()             # Create a socket object
host = socket.gethostbyname("10.5.31.207")     # Get local machine name
port = 60011                 # Reserve a port for your service.

s.connect(('localhost', port))

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
  if (s.recv(1024) == '000'):
    receiveFile (s)

s.close()
print('connection closed')


