#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 09:51:22 2019

@author: charlie
"""

import socket
import string
import time

# vars specificying server

SERVER = "127.0.0.1"
PORT = 6667
CHANNEL = "#test"


# open socket
IRCSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def connect():
    IRCSocket.connect((SERVER, PORT))
    print('Connected to ', SERVER, ':', PORT)

# hardcoded to join test


def join():
    IRCSocket.send("JOIN #test\n".encode())


def listen():
    while (True):
        time.sleep(5)
        buffer = IRCSocket.recv(1024)
        message = buffer.decode()
        if ("MSG" in message):
            print("received-message")
        print(message)

# send login data (customizable)


def login():
    IRCSocket.send("USER bot networksbot server bot\n".encode())
    IRCSocket.send("NICK Bot\n".encode())
    # send_data("NICK " + nickname)


connect()
login()
join()
listen()
