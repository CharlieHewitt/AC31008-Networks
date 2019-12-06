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

HOST = '10.0.42.17'
PORT = 6667

# - - - - - - - - - - - - - - - - -
# User and Channel Management
# - - - - - - - - - - - - - - - - -

# dictionaries for efficient searching

users = {}          # users[userName] = [connected channels]
channels = {}       # channels[channelName] = [connected users]
connections = {}    # connections[userName] = Connection (to send msgs ...)


def addUser(userName, connection):
    if userName in users:
        print('username taken')
        connection.sendMessage(
            ':' + socket.gethostname() + ' 433 :' + userName + ' is already in use')
        return False

    if (len(userName) > 9):
        print('username too long')
        connection.sendMessage(
            ':' + socket.gethostname() + ' 432 :' + userName + ' nickname too long')
        return False

    # add user with empty channel list
    users[userName] = []
    connections[userName] = connection
    print(userName + ' has been created')
    return True


# Active channel connections are cleaned up on removeUser()

def removeUser(userName):
    channelList = []
    if userName in users:
        if users[userName]:
            print (users[userName])
            for channel in users[userName]:
                channelList.append(channel)

            for channel in channelList:
                disconnectFromChannel(userName, channel, 'Disconnected')

        del users[userName]
        del connections[userName]
        print(userName + ' has been dropped')



# Add channel to user's connected channels & add user to channel's connected users

def connectToChannel(userName, channelName, origin):
    if userName in users and channelName in channels:
        # user not already connected to channel
        if (not (userName in channels[channelName] and channelName in users[userName])):
            users[userName].append(channelName)
            channels[channelName].append(userName)
            print(userName +  ' connected to ' + channelName)
            return True

        else:
            origin.sendMessage(':' + socket.gethostname() + ' 443 ' + userName + ' ' +
                               channelName + ' :already in channel')

    return False


# Remove channel from user's connected channels & remove user from channel's connected users

def disconnectFromChannel(userName, channelName, reason):
    # user & channel exist
    if userName in users and channelName in channels:

        # user connected to channel
        if userName in channels[channelName] and channelName in users[userName]:

            # message so clients know about the disconnection
            message = ':' + userName + '!' + userName + '@' + \
                socket.gethostname() + ' PART ' + channelName + ' :' + reason + '\r\n'
            sendMessage(channelName, message, None)

            # disconnect
            users[userName].remove(channelName)
            channels[channelName].remove(userName)
            print(userName + ' has disconnected from ' +  channelName)

            return True

    print('failed to disconnect from ' + channelName + ' (user not connected)')
    return False


# Send message to all users in a channel ( Add prefix/ who sent ...)
# Pass None if sender needs to receive the message.

def sendMessage(recipient, message, sender):
    # channel
    if '#' in recipient:
        for userName in channels[recipient]:

            # duplicate message
            if (not userName == None and userName == sender):
                continue

            connections[userName].sendMessage(message)

    # priv message to single user
    else:
        if(recipient in users):
            connections[recipient].sendMessage(message)

    print('sent message to ' + recipient + ' :' + message)


# - - - - - - - - - - -
# Initial Server State
# - - - - - - - - - - -

# Initialise default channels here, maybe add from file later if useful but not needed

def initialiseDefaultChannels():
    channels['#test'] = []
    channels['#general'] = []
    print ('created #test and #general')


# Can also add dummy users for testing purposes here

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


# - - - - - - - - - - - - - -
# Message parsing & handling
# - - - - - - - - - - - - - -

# dictionary storing regular expressions for message parsing

regex = {}

regex['user'] = r'USER\s(.*)\s(.*)\s(.*)\s:(.*)'
regex['nick'] = r'NICK\s(.*)'
regex['privmsg'] = r'PRIVMSG\s(.*)\s:(.*)'
regex['join'] = r'JOIN\s(.*)'
regex['part'] = r'PART\s(.*) (:.*)'
regex['who'] = r'WHO\s(.*)'
regex['names'] = r'NAMES\s(.*)'
regex['mode'] = r'MODE\s(.*)'
regex['ping'] = r'PING\s(.*)'
regex['quit'] = r'QUIT\s(.*)'

# parse message & handle based on matching 'expression'


def parseMessage(message, origin):
    try:
        messages = message.split('\r\n')
        for msg in messages:
            for expression in regex:
                match = re.search(regex[expression], msg)

                # supported IRC message - else ignore
                if (match):
                    groups = match.groups()

                    # message action
                    executeMessageHandler(expression, groups, origin)

    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)


# call the expression's message handler

def executeMessageHandler(expression, groups, origin):
    try:
        if (expression == 'user'):
            handleUserMessage(groups, origin)

        elif (expression == 'nick'):
            handleNickMessage(groups, origin)

        elif (expression == 'privmsg'):
            handlePrivMessage(groups, origin)

        elif (expression == 'join'):
            handleJoinMessage(groups, origin)

        elif (expression == 'part'):
            handlePartMessage(groups, origin)

        elif (expression == 'who'):
            handleWhoMessage(groups, origin)

        elif (expression == 'names'):
            handleNamesMessage(groups, origin)

        elif (expression == 'mode'):
            handleModeMessage(groups, origin)

        elif (expression == 'ping'):
            handlePingMessage(groups, origin)
        
        elif (expression == 'quit'):
            handleQuitMessage(origin)

        else:
            print('Error: no valid message handler')

    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)


# USER <username> <"useless"> <"useless"> <realname>
# eg: USER chewitt * * Charlie Hewitt

def handleUserMessage(groups, origin):
    try:
        if origin.userSet:
            # 'ignore', duplicate USER message ...
            return False

        origin.userName = groups[0]
        origin.realName = groups[3]
        origin.userSet = True

        # Check if connection valid & connect user to server if valid
        if (origin.nickSet):
            success = addUser(origin.nickName, origin)
            if (not success):
                origin.nickSet = False
                origin.nickName = '' 
                print ('rejected connection')

                return False
            else:
                print('successfully connected')
                origin.sendMessage(':' + socket.gethostname() + ' 001 ' +
                                origin.nickName + ' :Hi welcome to the Networks Assignment IRC Server\r\n')
                origin.sendMessage(':' + socket.gethostname() + ' 002 ' + origin.nickName +
                                ' :Your host is ' + socket.gethostname() + ', running version team6v0.0.0.1\r\n')
                origin.sendMessage(':' + socket.gethostname() + ' 003 ' + origin.nickName +
                                ' :This server was created sometime in 2019\r\n')
                origin.sendMessage(':' + socket.gethostname() + ' 004 ' +
                                origin.nickName + ' ' + socket.gethostname() + ' team6v0.0.0.1 o o\r\n')
                origin.sendMessage(':' + socket.gethostname() + ' 251 ' + origin.nickName + ' :There are ' + str(len(connections)) + ' users on the server\r\n')

                return True

    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)

# NICK <nickname>
# eg: NICK Charlie


def handleNickMessage(groups, origin):
    try:
        # add nickname to origin
        # nick = groups(0)
        alreadySet = origin.nickSet

        if not alreadySet:
            origin.nickName = groups[0]
            origin.nickSet = True

        # Check if connection valid & connect user to server if valid
        if (origin.userSet and not alreadySet):
            success = addUser(origin.nickName, origin)
            if (not success):
                origin.nickSet = False
                origin.nickName = '' 
                print ('rejected connection')
                return False
            
            else:
                print('successfully connected')

                origin.sendMessage(':' + socket.gethostname() + ' 001 ' +
                                origin.nickName + ' :Hi welcome to the Networks Assignment IRC Server\r\n')
                origin.sendMessage(':' + socket.gethostname() + ' 002 ' + origin.nickName +
                                ' :Your host is ' + socket.gethostname() + ', running version team6v0.0.0.1\r\n')
                origin.sendMessage(':' + socket.gethostname() + ' 003 ' + origin.nickName +
                                ' :This server was created sometime in 2019\r\n')
                origin.sendMessage(':' + socket.gethostname() + ' 004 ' +
                                origin.nickName + ' ' + socket.gethostname() + ' team6v0.0.0.1 o o\r\n')
                origin.sendMessage(':' + socket.gethostname() + ' 251 ' + origin.nickName + ' :There are ' + str(len(connections)) + ' user(s) on the server\r\n')
                


        return alreadySet

    except (ConnectionResetError, BrokenPipeError) as e:
         origin.handleException(e)

# PRIVMSG <recipient> :<message>
# recipient can be a channel (#test) or a single user (Charlie):
# eg: PRIVMSG #test :Hello I am new here!   / PRIVMSG Charlie :Hello


def handlePrivMessage(groups, origin):
    try:
        # user connected
        if (origin.userSet and origin.nickSet):
            recipient = groups[0]
            message = ':' + origin.nickName + '!' + origin.userName + '@' + \
                socket.gethostname() + ' PRIVMSG ' + recipient + \
                ' ' + groups[1] + '\r\n'

            # channel
            if '#' in recipient:
                sendMessage(recipient, message, origin.nickName)
            # pm
            else:
                if recipient in connections:
                    connections[recipient].sendMessage(message)
            return True
        else:
            # ignore as not connected
            return False

    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)


# JOIN <channel>
# eg: JOIN #test

def handleJoinMessage(groups, origin):
    try:
        # user connected
        if (origin.userSet and origin.nickSet):
            connected = origin.connectToChannel(groups[0])

            if connected:
                sendMessage(groups[0], ':' + origin.nickName + '!' + origin.userName +
                            '@' + socket.gethostname() + ' JOIN ' + groups[0] + '\r\n', None)
                origin.sendMessage(':' + socket.gethostname() + ' 331 ' + origin.nickName +
                                ' ' + str(groups[0]) + ' :No topic is set\r\n')
                handleNamesMessage(groups, origin)

            return connected
        else:
            # ignore as not connected
            return False
    
    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)

# PART <channel>
# eg: PART #test
# -> leave #test


def handlePartMessage(groups, origin):
    try:
        # user connected
        if (origin.userSet and origin.nickSet):
            channelName = groups[0]

            # user connected & will be disconnected from channel
            if (origin.nickName in channels[channelName] and channelName in users[origin.nickName]):
                # message = ':' + origin.nickName + '!' + origin.userName + '@' + 
                #     socket.gethostname() + ' PART ' + channelName + 
                #     ' ' + groups[1] + '\r\n'
                sendMessage(channelName, message, None)
                origin.disconnectFromChannel(channelName)

        else:
            # ignore as not connected
            return False

    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)

# WHO <channel>
# eg: WHO #test
# -> list of users in #test (for client use)

def handleWhoMessage(groups, origin):
    try:
        if (origin.userSet and origin.nickSet):
            origin.sendMessage(':' + socket.gethostname() + ' 352 ' + origin.nickName + ' ' + str(
                groups[0]) + ' ' + origin.userName + ' ' + origin.address[0] + ' + socket.gethostname() ' + ' ' + origin.nickName + ' H: 0 ' + origin.realName + '\r\n')
            origin.sendMessage(':' + socket.gethostname() + ' 315 ' + origin.nickName +
                            ' ' + str(groups[0]) + ' :End of WHO list\r\n')

    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)

# NAMES <channel>
# eg: NAMES #test
# -> list of users in #test (for client use)
# TODO: look into how this is different from WHO ...


def handleNamesMessage(groups, origin):
    try:
        if (origin.userSet and origin.nickSet):
            channelName = str(groups[0])

            if channelName in channels:
                for person in channels[channelName]:
                    origin.sendMessage(':' + socket.gethostname() + ' 353 ' + person + ' = ' + str(
                        groups[0]) + ' :' + person + '\r\n')
            origin.sendMessage(':' + socket.gethostname() + ' 366 ' + origin.nickName +
                            ' ' + str(groups[0]) + ' :End of NAMES list\r\n')
    
    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)


# MODE <channel>
# eg: MODE #test
# -> returns channel mode (modes aren't currently implemented)

def handleModeMessage(groups, origin):
    try:
        if (origin.userSet and origin.nickSet):
            origin.sendMessage(':' + socket.gethostname() + ' 324 ' + origin.nickName +
                        ' ' + str(groups[0]) + ' +\r\n')

    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)

# PING

def handlePingMessage(groups, origin):
    try:
        if (origin.userSet and origin.nickSet):
            origin.sendMessage(':' + socket.gethostname() +
                        ' PONG ' + origin.address[0] + ' :' + str(groups[0] + '\r\n'))
            
    except (ConnectionResetError, BrokenPipeError) as e:
        origin.handleException(e)

# QUIT
def handleQuitMessage(origin):
    try:
        # should really send an error message back to confirm..
        raise Exception('quit')

    except (ConnectionResetError, BrokenPipeError, Exception) as e:
        origin.handleException(e)


# - - - - - - - - -
# Connection class
# - - - - - - - - -

class Connection:
    # Constructor
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

        # variables set by USER and NICK messages
        self.realName = None
        self.userName = None
        self.nickName = None

        # connection to IRC server valid when these are True
        self.userSet = False
        self.nickSet = False

    # toString
    def __str__(self):
        return "Active connection from: " + str(self.address)

    # send message to 'connected client'
    def sendMessage(self, message):
        try:
            print('sending: ' + str(message))
            message = str(message).encode()
            self.conn.send(message)

        except (ConnectionResetError, BrokenPipeError) as e:
            self.handleException(e)


    # receive message from 'connected client'
    def receive(self):
        try:
            return self.conn.recv(1024)

        except (ConnectionResetError, BrokenPipeError) as e:
            self.handleException(e)

    def connectToChannel(self, channelName):
        try:
            if (not self.userSet or not self.nickSet):
                return False
            return connectToChannel(self.nickName, channelName, self)

        except (ConnectionResetError, BrokenPipeError) as e:
            self.handleException(e)

    def disconnectFromChannel(self, channelName):
        try:
            if (not self.userSet or not self.nickSet):
                return False

            return disconnectFromChannel(self.nickName, channelName, 'Leaving')

        except (ConnectionResetError, BrokenPipeError) as e:
            self.handleException(e)


    # cleans up connected user by disconnecting them from channels/server and closes connection
    def handleException(self, e):
        print(e)
        if self.userSet and self.nickSet and e.__class__.__name__ != 'BrokenPipeError':
            removeUser(self.nickName)
            self.conn.close()
            print('Connection dropped by: ' + str(self.address))


    def listen(self):
        try:
            while True:
                data = self.receive()
                if data:
                    strData = data.decode()
                    parseMessage(strData, self)

        except (ConnectionResetError, BrokenPipeError) as e:
            self.handleException(e)
            return

# - - - - - - - - - - - - - -
# Server/Socket Related Code
# - - - - - - - - - - - - - -




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


# create Connection object & run it on a thread

def initialiseConnection(conn, addr):
    connection = Connection(conn, addr)
    threading.Thread(target=connection.listen).start()


# - - - - - - - - -
# Program Execution
# - - - - - - - - -

if __name__ == "__main__":
    # create default channels
    testInitialisation()

    # server status thread (args = frequency of status updates in seconds)
    threading.Thread(target=serverStatus, args=(10,)).start()

    # initialise socket
    sock = initialiseSocket()
    listenForConnections(sock)
    print('Server shutting down ...')