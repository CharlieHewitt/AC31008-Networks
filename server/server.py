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
import re

# - - - - - - - -
# Server Details
# - - - - - - - -

# change to "10.0.42.17" for vms
HOST = '127.0.0.1'
PORT = 6667

# - - - - - - - - - - - - - - - - -
# User and Channel Manag ement
# - - - - - - - - - - - - - - - - -

# dictionaries for efficient searching

users = {}          # users[userName] = [connected channels]
channels = {}       # channels[channelName] = [connected users]
connections = {}    # connections[userName] = Connection (to send msgs ...)


# Do proper exception handling / name limitation ...

def addUser(userName, connection):
    if userName in users:
        print('Duplicate name exception, DO ERROR HANDLING -------------')
        return False

    # add user with empty channel list
    users[userName] = []
    connections[userName] = connection
    return True


# Active channel connections are cleaned up on removeUser()

def removeUser(userName):
    if userName in users:
        if users[userName]:
            for channel in users[userName]:
                disconnectFromChannel(userName, channel)
        del users[userName]
        del connections[userName]


# Add channel to user's connected channels & add user to channel's connected users

def connectToChannel(userName, channelName):
    if userName in users and channelName in channels:
        # user not connected to channel
        if (not (userName in channels[channelName] and channelName in users[userName])):
            users[userName].append(channelName)
            channels[channelName].append(userName)
            print('succesfully connected')
            return True
    print('failed to connect')

    return False


# Remove channel from user's connected channels & remove user from channel's connected users

def disconnectFromChannel(userName, channelName):
    # user & channel exist
    if userName in users and channelName in channels:

        # user connected to channel
        if userName in channels[channelName] and channelName in users[userName]:
            users[userName].remove(channelName)
            channels[channelName].remove(userName)
            return True

    print('failed to disconnect from ' + channelName + ' because not connected')
    return False


# Send message to all users in a channel ( Add prefix/ who sent ...)

def sendMessage(recipient, message):

    # channel
    if '#' in recipient:
        for userName in channels[recipient]:
            print(recipient + " " + userName + " " +
                  "attempting to send :" + message)
            connections[userName].sendMessage(message)
            print('sent')

    # priv message to single user
    else:
        if(recipient in users):
            connections[recipient].sendMessage(message)


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
    print('Server initialised in default state:')


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
            print('\n-- status update ping failed : JealousJohn not active')


# TODO: pad status message to be nicely formatted (userName = max 9 chars + channel?)
# List of channels + connected users

def printChannels():
    print('\nChannels:\n')

    for channel in channels:
        print(channel + '  connected users: ' + str(channels[channel]))


# List of users + channel connections

def printUsers():
    print('\nUsers:\n')
    for user in users:
        print(user + '  connected to: ' + str(users[user]))


# - - - - - - - - - -
# Message Information
# - - - - - - - - - -

# Connecting to server

# every message \r\n
# USER 'username' 'hostname' 'servername' 'realname'
# NICK 'nickname' -> create user from this

# PRIVMSG 'channelname' 'message'

# JOIN 'channelname'

# LEAVE 'channelname'

# PING - connection figure it out
# receive PONG :pingisn


# dictionary storing regular expressions for message parsing

def parseMessage(message, origin):

    messages = message.split('\r\n')
    for msg in messages:
        # print('message split as : ' + msg)
        for expression in regex:
            match = re.search(regex[expression], msg)

            # IRC message - else ignore
            if (match):
                # print('matched ' + expression)
                groups = match.groups()

                # message action
                executeMessageHandler(expression, groups, origin)


def executeMessageHandler(expression, groups, origin):
    if (expression == 'user'):
        handleUserMessage(groups, origin)

    elif (expression == 'nick'):
        handleNickMessage(groups, origin)

    elif (expression == 'privmsg'):
        handlePrivMessage(groups, origin)

    elif (expression == 'join'):
        handleJoinMessage(groups, origin)

    elif (expression == 'leave'):
        handleLeaveMessage(groups, origin)

    elif (expression == 'who'):
        handleWhoMessage(groups, origin)

    elif (expression == 'names'):
        handleNamesMessage(groups, origin)

    else:
        print('Error: no valid message handler')


regex = {}

regex['user'] = r'USER\s(.*)\s(.*)\s(.*)\s:(.*)'
regex['nick'] = r'NICK\s(.*)'
regex['privmsg'] = r'PRIVMSG\s(.*)\s:(.*)'
regex['join'] = r'JOIN\s(.*)'
regex['leave'] = r'LEAVE\s(.*)'
regex['who'] = r'WHO\s(.*)'
regex['names'] = r'NAMES\s(.*)'
regex['mode'] = r'MODE\s(.*)'


def handleUserMessage(groups, origin):
    if origin.userSet:
        # 'ignore', duplicate USER message ...
        return False  # ???
    print('tuple: ' + groups[0])
    origin.userName = groups[0]
    origin.userSet = True
    # + add userName to origin connection

    if (origin.nickSet):
        print('successfully connected')
        origin.sendMessage(':127.0.0.1' + ' 001 ' +
                           origin.nickName + ' :Hi welcome to IRC\r\n')
        origin.sendMessage(':127.0.0.1 002 ' + origin.nickName +
                           ':Your host is DESKTOP-BS338CC, running version team6.0.0.0.1 (alpha)\r\n')
        origin.sendMessage(':127.0.0.1 003 ' + origin.nickName +
                           ':This server was created sometime in 2019\r\n')
        origin.sendMessage(':127.0.0.1 004 ' +
                           origin.nickName + '127.0.0.1 0.0.0.1 o o\r\n')
        success = addUser(origin.nickName, origin)
        return success
        # throw error &| close connection (depends on error type) -> ie duplicate name


def handleNickMessage(groups, origin):
    # add nickname to origin
    # nick = groups(1)
    alreadySet = origin.nickSet

    # TODO: handle name change, or don't lol
    origin.nickName = groups[0]
    origin.nickSet = True

    if (origin.userSet and not alreadySet):
        print('successfully connected')
        success = addUser(origin.nickName, origin)
        return success

    return True

# TODO: sort priv message


def handlePrivMessage(groups, origin):
    # user connected
    if (origin.userSet and origin.nickSet):
        sendMessage(groups[0], groups[1])
        # TODO: return sendMessage>>>>?
        return True
    else:
        # ignore as not connected
        return False

# TODO: handle replies


def handleJoinMessage(groups, origin):
    # user connected
    print('handlejoin')
    if (origin.userSet and origin.nickSet):
        print(groups[0])
        connected = origin.connectToChannel(groups[0])

        if connected:
            origin.sendMessage(':127.0.0.1 331 ' + origin.nickName +
                               ' ' + str(groups[0]) + ' :No topic is set\r\n')
            handleNamesMessage(groups[0], origin)

            # TODO: SORT OUT MESSAGES + HOSTNAME

        return connected
    else:
        # ignore as not connected
        return False


def handleWhoMessage(groups, origin):
    origin.sendMessage(':127.0.0.1 352 ' + origin.nickName + ' ' + str(
        groups[0]) + origin.userName + ' 127.0.0.1 ' + 'server ' + origin.nickName + ' :0 realname\r\n')
    origin.sendMessage(':127.0.0.1 315 ' + origin.nickName +
                       ' ' + str(groups[0]) + ' :End of WHO list\r\n')


def handleNamesMessage(groups, origin):
    origin.sendMessage(':127.0.0.1 353 ' + origin.nickName + ' = ' + str(
        groups[0]) + ':oneOfTheNames\r\n')
    origin.sendMessage(':127.0.0.1 366 ' + origin.nickName +
                       ' ' + str(groups[0]) + ' :End of NAMES list\r\n')


def handleModeMessage(groups, origin):
    origin.sendMessage(':127.0.0.1 324 ' + origin.nickName +
                       ' ' + str(groups[0]) + ' +')


def handleLeaveMessage(groups, origin):
    # user connected
    if (origin.userSet and origin.nickSet):
        return origin.disconnectFromChannel(groups[0])
    else:
        # ignore as not connected
        return False


# def parseUserMessage(message):
#     match = re.search(r'USER\s(.*)\s(.*)\s(.*)\s:(.*)', message)

#     if (match):
#         print(match)
#         print(match.group())
#         print(match.group(1))  # username
#         print(match.group(2))  # hostname
#         print(match.group(3))  # servername
#         print(match.group(4))  # realname (prefixed by :)


# - - - - - - - - -
# Connection class
# - - - - - - - - -

class Connection:
    # Constructor
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

        # variables set by USER and NICK messages
        self.userName = None
        self.nickName = None
        self.userSet = False
        self.nickSet = False

    # toString
    def __str__(self):
        return "Active connection from: " + str(self.address)

    # send as bytes, returns num of bytes sent
    def sendMessage(self, message):
        print('sending:' + str(message))
        message = str(message).encode()
        return self.conn.send(message)

    # receive message
    def receive(self):
        return self.conn.recv(1024)

    def connectToChannel(self, channelName):
        if (self.userName is None):
            return False
        print('connection attempting to connect to ' + channelName)
        return connectToChannel(self.nickName, channelName)

    def disconnectFromChannel(self, channelName):
        if (self.userName is None):
            return False

        return disconnectFromChannel(self.userName, channelName)

    def listen(self):
        try:
            while True:
                data = self.receive()
                if data:
                    strData = data.decode()
                    print('Received data from: ', self.address,
                          'contents: ', strData)

                    # add splitting received messages by \r\n!
                    parseMessage(strData, self)
                    print(self.userName)
                    self.sendMessage(data)

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


# listen for & accept new connections

def listenForConnections(s):
    s.listen()
    while True:
        conn, addr = s.accept()
        initialiseConnection(conn, addr)


# create Connection & listen for messages on seperate thread

def initialiseConnection(conn, addr):
    connection = Connection(conn, addr)
    threading.Thread(target=connection.listen).start()


# - - - - - - - - -
# Program Execution
# - - - - - - - - -

# initialise server with channels and some 'ghost' users
testInitialisation()

# server status thread (args = frequency of status updates in seconds)
threading.Thread(target=serverStatus, args=(10,)).start()
main()
