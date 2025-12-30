#!/bin/bash

if [ -z ${PROXY_USER} ]
then
  ( while true; do proxy --hostname 0.0.0.0; echo "proxy failed, restarting..."; sleep 1; done ) &
else
  ( while true; do proxy --hostname 0.0.0.0 --basic-auth "$PROXY_USER:$PROXY_PASSWORD"; echo "proxy failed, restarting..."; sleep 1; done ) &
fi

mkfifo gfifo
touch gout.log
touch gdebug.log

( CDATE="$(date -u +%s)" && f1=0 && while ! grep -q 'Enter OTP:' gdebug.log; do while ! grep -q 'Enter email:' gdebug.log; do echo "waiting for email..."; sleep 1; done ; if [ $f1 -eq 0 ]; then echo "$EMAIL_USER" >> gfifo; f1=1; fi ; echo "waiting for OTP..."; sleep 5; done && otp="$(python -c 'import otp; import sys; otp.main(int(sys.argv[1]))' $CDATE)" && while [ -z "$otp" ]; do echo "waiting for email to be received..."; sleep 5; otp="$(python -c 'import otp; import sys; otp.main(int(sys.argv[1]))' $CDATE)"; done && echo "$otp" >> gfifo ) &
tail -f gfifo | grout tcp://:8899 2>>gout.log 1>>gdebug.log
( tail -f gout.log ) &

while true
do
  tail -f gfifo | grout tcp://:8899 2>>gout.log 1>>gdebug.log
  echo "failed tunnel, restarting..."
  sleep 1
done