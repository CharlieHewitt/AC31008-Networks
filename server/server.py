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

# - - - - - - - -
# Server Details
# - - - - - - - -

HOST = 'localhost'
PORT = 6667

# - - - - - - - - - - - - - - - - -
# User and Channel Management
# - - - - - - - - - - - - - - - - -

# dictionaries for efficient searching

users = {}          # users[userName] = [connected channels]
channels = {}       # channels[channelName] = [connected users]
connections = {}    # connections[userName] = Connection (to send msgs ...)


# Do proper exception handling / name limitation ...

def addUser(userName):
    if userName in users:
        print('Duplicate name exception, DO ERROR HANDLING -------------')
        return

    # add user with empty channel list
    users[userName] = []


# Active channel connections are cleaned up on removeUser()

def removeUser(userName):
    if userName in users:
        if users[userName]:
            for channel in users[userName]:
                disconnectFromChannel(userName, channel)
        del users[userName]


def connectToChannel(userName, channelName):
    if userName in users and channelName in channels:
        # add channel to users connected list
        users[userName].append(channelName)

        # add user to channel's list of connected users
        channels[channelName].append(userName)

    # return success/fail??


def disconnectFromChannel(userName, channelName):
    if userName in users and channelName in channels:
        # remove user from channel
        channels[channelName].remove(userName)

        # remove channel from user's list of channels
        users[userName].remove(channelName)


# Send message to all users in a channel ( Add prefix/ who sent ...)

def sendMessage(channelName, message):
    for userName in channels[channelName]:
        connections[userName].sendMessage(message)


# - - - - - - - - - - -
# Initial Server State
# - - - - - - - - - - -

# Initialise default channels here, maybe add from file later if useful but not needed

def initialiseDefaultChannels():
    channels['#test'] = []
    channels['#test3'] = []


# Dummy users for testing purposes

def testInitialisation():
    initialiseDefaultChannels()
    addUser('Holly<3')
    addUser('Holly<34')
    addUser('Tom')
    addUser('Briaaaan')
    addUser('Alfie')
    connectToChannel('Alfie', '#test3')
    connectToChannel('Briaaaan', '#test')
    connectToChannel('Briaaaan', '#test3')
    connectToChannel('Holly<3', '#test')
    connectToChannel('Holly<34', '#test')
    connectToChannel('Tom', '#test')
    connectToChannel('Tom', '#test34')
    disconnectFromChannel('Tom', '#test34')
    removeUser('Holly<34')
    print('Server initialised in default state:')
    printChannels()
    printUsers()


# - - - - - - - -
# Server Status
# - - - - - - - -

# server status message posted every {frequency} seconds -- should be run on a seperate thread

def serverStatus(frequency):
    while True:
        time.sleep(frequency)
        print('\nCurrent Server Status: \n')
        printChannels()
        printUsers()
        try:
            connections['JealousJohn'].sendMessage('-- Status update live')
        except:
            print('\n-- update ping failed : JealousJohn not active')


# List of channels + connected users

def printChannels():
    print('\nChannels:\n')

    for channel in channels:
        print(channel + ' (connected users: ' + str(channels[channel]) + ')')


# List of users + channel connections

def printUsers():
    print('\nUsers:\n')
    for user in users:
        print(user + ' (connected to: ' + str(users[user]) + ')')


# - - - - - - - - -
# Connection class
# - - - - - - - - -

# TODO: initialise userName in connection initialisation message, not in constructor / hardcoded!
#       connections aren't 'active' in the chat server ecosystem until a user is created (which requites a valid name)

class Connection:
    # Constructor
    def __init__(self, conn, address, userName):
        self.conn = conn
        self.address = address
        self.userName = userName

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

    def connectToChannel(self, channelName):
        connectToChannel(self.userName, channelName)

    def disconnectFromChannel(self, channelName):
        disconnectFromChannel(self.userName, channelName)

    def listen(self):
        try:
            while True:
                time.sleep(2)
                data = self.receive()
                if data:
                    print('Received data from: ', self.address,
                          'contents: ', data.decode())
                    self.sendMessage(data)
                addUser(self.userName)
                self.connectToChannel('#test')

                time.sleep(20)
                self.disconnectFromChannel('#test')
                self.sendMessage('Hello there')

        except ConnectionResetError:
            # clean up open channel/user connections
            removeUser(self.userName)
            print('Connection dropped by: ' + str(self.address))

# - - - - - - - - - - - - - -
# Server/Socket Related Code
# - - - - - - - - - - - - - -


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

    print('Server live on port 6667. Awaiting connections ...')
    return s


def listenForConnections(s):
    s.listen()
    while True:
        # time.sleep(2)
        conn, addr = s.accept()
        initialiseConnection(conn, addr, 'JealousJohn')
        time.sleep(5)
        printUsers()


def initialiseConnection(conn, addr, userName):
    # initialise Connection & start thread
    connection = Connection(conn, addr, userName)
    connections[userName] = connection
    threading.Thread(target=connection.listen).start()


# - - - - - - - - -
# Program Execution
# - - - - - - - - -

# initialise server with channels and some 'ghost' users
testInitialisation()

# server status thread (args = frequency of status updates in seconds)
threading.Thread(target=serverStatus, args=(10,)).start()
main()
