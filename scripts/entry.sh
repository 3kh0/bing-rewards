#!/bin/bash
CONFIG=/config/config.json
log=/bing-rewards/BingRewards/logs/error.log
cronLog=/bing-rewards/BingRewards/logs/cronBing.log

# Add update.sh & script.sh to cronjob, do this dynamically to account for diff schedules
echo "$UPDATE /bin/bash /bing-rewards/scripts/update.sh > \$logfile 2>&1" >> /etc/cron.d/bing.cron
echo "$SCH /bin/bash /bing-rewards/scripts/script.sh > \$logfile 2>&1" >> /etc/cron.d/bing.cron
set -x
service cron start
crontab /etc/cron.d/bing.cron

echo "Checking for imported logs"
if test -e "$log";
then
	echo "You imported logs"
	if test ! -e "/bing-rewards/BingRewards/logs/cronBing.log";
	then
		echo "You must be new to docker welcome"
		touch /bing-rewards/BingRewards/logs/cronBing.log
	fi
else
	echo "Making logs To tail"
	mkdir /bing-rewards/BingRewards/logs
	touch /bing-rewards/BingRewards/logs/cronBing.log
	# touch /bing-rewards/BingRewards/logs/error.log
fi
cd /bing-rewards/BingRewards
"$@"
tail -f /bing-rewards/BingRewards/logs/cronBing.log
