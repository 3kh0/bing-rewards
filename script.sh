#!/bin/bash
df="%b %d %T"
m0="-- Job scheduled -- pid:"
m1="-- Job started ---- pid:"
m2="-- Job completed -- pid:"
date +"$df $m0 $$"
MAXWAIT=1800 #max seconds to wait
MAXTIME=$[RANDOM%$MAXWAIT+1]
echo "Waiting For "$MAXTIME" seconds"
REWRITE="\e[25D\e[1A\e[K"
echo "Starting..."
while [ $MAXTIME -gt 0 ]; do 
    MAXTIME=$((MAXTIME-1))
    sleep 1
    echo -e "${REWRITE}$MAXTIME"
done
echo -e "${REWRITE}Done sleeping."
/usr/local/bin/python /bing-rewards/BingRewards/BingRewards.py -nsb
