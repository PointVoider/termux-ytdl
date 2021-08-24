#!/bin/bash
set -euo pipefail
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


# one liner because this script somehow doesn't reach the read command
apt-get update && apt-get -y install python ffmpeg && pip install youtube-dl colorama && python3 ~/simple-ytdl.py --setup
