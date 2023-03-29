#!/bin/bash
if [[ `git rev-parse --abbrev-ref HEAD` != master ]]; then git checkout master; fi
git pull
pip install -r BingRewards/requirements.txt
