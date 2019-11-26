#!/bin/bash

python3 ../server/server.py &
echo "Server Started, bot will start soon ..."

sleep 3

echo "Bot Starting ..." 
python3 ../bot/bot.py