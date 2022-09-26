#!/bin/bash
CONFIG=/config/config.json
set -x
service cron start
crontab /etc/cron.d/bing.cron
echo "Cloning jjchens235/bing-rewards"
git clone https://github.com/jjjchens235/bing-rewards.git /bing-rewards/
echo "Setting Up pip and installing requirements"
python -m pip install --upgrade pip
pip install --no-warn-script-location -r /bing-rewards/BingRewards/requirements.txt
if test -f "$CONFIG"; then
	echo "Config was imported linking /config/config.json to /bing-rewards/BingRewards/config"
	mkdir /bing-rewards/BingRewards/config
	ln -s /config/config.json /bing-rewards/BingRewards/config/config.json
fi
echo "Linking bing-rewards logs to /logs"
mkdir /bing-rewards/BingRewards/logs
ln -s /bing-rewards/BingRewards/logs /bing
touch /bing-rewards/BingRewards/logs/cronBing.log
touch /bing-rewards/BingRewards/logs/error.log
cd /bing-rewards/BingRewards
"$@"
tail -f /bing-rewards/BingRewards/logs/*.log

