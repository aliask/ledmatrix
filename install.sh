#!/bin/bash

set -e

if [ -z $SUDO_UID ]; then
  echo "Must be run using sudo!"
  exit 1
fi

pip3 install pyyaml
mkdir -p /usr/share/ledserver
cp config.yml /etc/ledserver.yml
PWD=`pwd`
ln -s $PWD/main.py /usr/local/bin/ledserver
cp ledserver.service /lib/systemd/system/ledserver.service
systemctl daemon-reload
systemctl enable ledserver.service