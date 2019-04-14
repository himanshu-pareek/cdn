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
    # for i in range (chunks):
    #   # print('receiving data...')
    #   data = s.recv(1024)
    #   # print('data=%s', (data))
    #   if not data:
    #       break
    #   # write data to a file
    #   f.write(data)

    # data = s.recv (last_size)
    # print ('data =', data)
    # f.write (data)
    # f.close()
  print ('file closed:', full_path)
  s.send ('111')

while True:
  conn, addr = s.accept()
  host = addr[0]
  print ('Connected to origin')
  while True:
    res = conn.recv (1024)
    # print ('res from origin =', res)
    if (res == '000'):
      receiveFile (conn)

s.close()
print('connection closed')


