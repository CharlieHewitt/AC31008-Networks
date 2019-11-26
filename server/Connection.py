#!/usr/bin/env python3
import time


class Connection:
    # Constructor
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

    def sendMessage(self, message):
        message = str(message).encode()
        self.conn.send(message)

    def receive(self):
        return self.conn.recv(1024)

    def status(self):
        print('Current Connection details: Connection =',
              self.conn, ' + Address = ', self.address, ' :')

    def listen(self):
        print('Connection listening')
        while True:
            time.sleep(2)
            self.status()
            data = self.receive()
            if data:
                print('Received data from: ', self.address, 'contents: ', data)
                self.sendMessage(data)
