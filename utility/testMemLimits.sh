#!/bin/bash

i=0
while [ $i -lt 250 ]
do 
python3 ../bot/testClient.py &
let "i++"
done
