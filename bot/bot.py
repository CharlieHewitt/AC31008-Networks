#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 09:51:22 2019

@author: charlie
"""

import socket, string

# vars specificying server

SERVER = "localhost"
PORT = 6667
CHANNEL = "#test"


# open socket
IRCSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect():
    IRCSocket.connect((SERVER, PORT))
    
# hardcoded to join test
def join():
    IRCSocket.send("JOIN #test\n".encode())
    
def listen():
    while (True):
        buffer = IRCSocket.recv(1024)
        message = buffer.decode()
        if ("MSG" in message):
            print ("received-message")
        print (buffer)
        
#send login data (customizable)
def login():
    IRCSocket.send("USER bot networksbot server bot\n".encode())
    IRCSocket.send("NICK Bot\n".encode())
  #  send_data("NICK " + nickname)
  
connect()
login()
join()
        

