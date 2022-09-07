#!/bin/sh

# reboots raspberry, when www.fabman.io is not reachable
# checked via crontab
# reboots logged in /home/pi/raspi-fabman/watchdog.log
# source: https://weworkweplay.com/play/rebooting-the-raspberry-pi-when-it-loses-wireless-connection-wifi/

ping -c4 www.fabman.io > /dev/null

if [ $? != 0 ]
then
  echo "$(/bin/date) PING FAILED -> REBOOT" >> /home/pi/raspi-fabman/watchdog.log
  sudo /sbin/shutdown -r now
#else
#  echo "$(/bin/date) PING OK" >> /home/pi/raspi-fabman/watchdog.log
fi

/usr/bin/pgrep python3
if [ $? != 0 ]
then
  echo "$(/bin/date) MICROPOS NOT RUNNING -> STARTING MICROPOS" >> /home/pi/raspi-fabman/watchdog.log
  ############runuser -l pi -c "cd /home/pi/raspi-fabman;/usr/bin/python3 /home/pi/raspi-fabman/micropos.py >> /home/pi/raspi-fabman/log/micropos.log 2>&1 &"
  #sudo /sbin/shutdown -r now
#else
  #echo "$(/bin/date) MICROPOS OK" >> /home/pi/raspi-fabman/watchdog.log
fi
