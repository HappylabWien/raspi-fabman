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
else
  echo "$(/bin/date) OK" >> /home/pi/raspi-fabman/watchdog.log
fi
