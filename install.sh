#!/bin/bash

# Basic setup
termux-setup-storage
sleep 2

#Clean Install
if [[ ! -d ~/bin ]]; then
  mkdir ~/bin
fi 
if [[ -e ~/bin/termux-url-opener ]]; then
  rm ~/bin/termux-url-opener
fi 

curl -L https://raw.githubusercontent.com/LZNOXP/termux-ytdl/main/termux-url-opener > "./bin/termux-url-opener"
chmod +x ./bin/termux-url-opener
curl -L https://raw.githubusercontent.com/LZNOXP/termux-ytdl/main/simple-ytdl.py > "simple-ytdl.py"


# Basic setup
termux-setup-storage
sleep 2
apt-get update
apt-get -y install python ffmpeg
pip install youtube-dl

read -p "Where should the downloaded video be saved? : " path
python3 ~/simple-ytdl.py -p "$path"
