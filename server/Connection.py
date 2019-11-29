#!/usr/bin/env python3
import time

# TODO: Sort Drop Connections message, messages between connections


class Connection:
    # Constructor
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

    # toString
    def __str__(self):
        return "Active connection from: " + str(self.address)

    # send as bytes, returns num of bytes sent
    def sendMessage(self, message):
        message = str(message).encode()
        return self.conn.send(message)

    # receive message
    def receive(self):
        return self.conn.recv(1024)

    def status(self):
        print('Current Connection details: Connection =',
              self.conn, ' + Address = ', self.address, ' :')

    def listen(self):
        try:
            while True:
                time.sleep(2)
                # self.status()
                data = self.receive()
                if data:
                    print('Received data from: ', self.address,
                          'contents: ', data.decode())
                    self.sendMessage(data)

                time.sleep(10)
                self.sendMessage('Hello there Obi-Wan')

        # needs more testing but kinda works
        except ConnectionResetError:
            print('Connection dropped by: ' + str(self.address))
            # remove from active connections []
