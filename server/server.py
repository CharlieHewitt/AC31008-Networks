#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 09:51:22 2019

@author: charlie
"""

import socket
import string
import threading
import time

# connection class
from Connection import Connection

# globals
HOST = 'localhost'
PORT = 5000
connections = []


def main():
    socket = initialiseSocket()
    listenForConnections(socket)
    print('Server shutting down ...')


def initialiseSocket():
    # initialise socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind to given port & listen for connections
    s.bind((HOST, PORT))

    return s


def listenForConnections(s):
    s.listen()
    while True:
        time.sleep(2)
        conn, addr = s.accept()
        initialiseConnection(conn, addr)
        print(connections)


def initialiseConnection(conn, addr):
    # initialise Connection & start thread
    connection = Connection(conn, addr)
    connection.status
    connections.append(connection)
    threading.Thread(target=connection.listen).start()


# run program
main()
# multi-threading example usage:
# def runThread(name):
#   print('Running Thread: ', name)
#
# thread1 = threading.Thread(target=runThread, args=('test1',))
# thread2 = threading.Thread(target=runThread, args=('test2',))

# thread1.start()
# thread2.start()
