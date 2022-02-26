#!/bin/bash
if [ $EUID != 0 ]; then
    sudo "$0" "$@"
    exit $?
fi
if [[ `git rev-parse --abbrev-ref HEAD` != master ]]; then git checkout master; fi
git pull
pip3 install -r BingRewards/requirements.txt
