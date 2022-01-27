# a prototype of the RPi, sending and receiving TCP packets
import socket
import json

IP = '127.0.0.1' # local computer
PORT = 2000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    def local(MESSAGE):
        data = bytes(MESSAGE, 'utf-8')

        print("TCP target IP: %s" % IP)
        print("TCP target port: %s" % PORT)
        print("Message: %s" % data)

        s.send(data)
        data = s.recv(1024)
        data = data.decode("utf-8")
        
        print('Received ' , data)
        print()

    s.connect((IP, PORT))

    while True:
        x = input("updates? ")
        if x=="end" or x=="exit":
            break
        local(x)