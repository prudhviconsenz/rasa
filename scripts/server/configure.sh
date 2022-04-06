#!/bin/bash

# this is the installation script to setup rasax for the first time
# it does not run on reloading an image

# fail if any command fails
set -e -o pipefail

# rasa install
curl -sSL -o install.sh https://storage.googleapis.com/rasa-x-releases/0.42.6/install.sh
bash ./install.sh
mv .env .env_original
cat .env_original .env_extra | sudo tee .env

# warning message says to do this
sysctl vm.overcommit_memory=1

cd /etc/rasa

# docker container user 1001 requires access
mkdir -p credentials
chown -R 1001 credentials
mkdir -p dbtest
chown -R 1001 dbtest

source /etc/profile.d/shortcuts.sh
up