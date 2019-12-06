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
        # message = buffer.decode()
        # print("received-message")
        # print(message)
        IRCSocket.send("JOIN #test\n".encode())
        time.sleep(5)
        IRCSocket.send(
            "PRIVMSG #test :Hello I am Rowan\r\n".encode())
        print('tried TO SEND')
        time.sleep(5)
        IRCSocket.send("PRIVMSG Charlie :Hello I am Rowan the second\r\n".encode())
        IRCSocket.send('PART #test\r\n'.encode())
        time.sleep(10)

        # time.sleep(2)
        # IRCSocket.send("LEAVE #test\r\n".encode())


# send login data (customizable)


def login():
    IRCSocket.send("USER Rowan rowan sfs :Rowan\r\n".encode())
    IRCSocket.send("NICK Rowan\r\n".encode())
    # send_data("NICK " + nickname)


connect()
login()
join()
listen()
