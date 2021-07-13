#!/bin/bash

# Basic setup
termux-setup-storage
sleep 5

#Clean Install
if [[ ! -d bin ]]; then
  mkdir bin
fi 
if [[ -e bin\\termux-url-opener ]]; then
  rm bin\\termux-url-opener
fi 

#Installing dependencies
pkg update -y && pkg install python -y && pkg install ffmpeg -y && pip install youtube-dl -y

value=$(< termux-url-opener)

# more termux-url-opener > "./bin/termux-url-opener"
curl -L https://raw.githubusercontent.com/LZNOXP/termux-ytdl/main/termux-url-opener > "./bin/termux-url-opener"
chmod +x ./bin/termux-url-opener
curl -L https://raw.githubusercontent.com/LZNOXP/termux-ytdl/main/simple-ytdl.py > "simple-ytdl.py"
read -p "Where should the downloaded video be saved? : " path
python3 ./simple-ytdl.py -p "$path"
