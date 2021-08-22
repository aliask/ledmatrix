#!/bin/bash

set -eo pipefail

RESET='\033[0m'
WHITE_R='\033[39m'
RED='\033[1;31m' # Light Red.
GREEN='\033[1;32m' # Light Green.

# Check for root (sudo)
if [[ "$EUID" -ne 0 ]]; then
  echo -e "${RED}##########################################################${RESET}"
  echo -e "${RED}#${RESET}       The script need to be run as root..."
  echo -e "${RED}##########################################################${RESET}"
  exit 1
fi

# Set up virtual environment
pip3 install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt

# Install executable and systemd service
if [ ! -x /usr/local/bin/ledserver ]; then
  THISDIR=$(pwd)
  ln -s /usr/local/bin/ledserver $THISDIR/main.py
fi
cp ledserver.service /lib/systemd/system/
systemctl daemon-reload
systemctl enable ledserver.service
