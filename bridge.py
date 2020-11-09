#!/usr/bin/python3

'''
Minimal Example for Fabman Bridge:
* Switch on with member card
* A relay is switched on, when access is granted
* Switch off by pressing a button
'''

import RPi.GPIO as GPIO
import time, logging, pprint
from raspifabman import FabmanBridge, Fabman
#from signal import pause

# Bridge config
'''
Example for "bridge.json" (Use bridge API token for the equipment you want to connect to.)
{ 
	"api_url_base"       : "https://fabman.io/api/v1/",
	"api_token"          : "xxxxxxxxxxx-xxxxxxxxx-x-xxxxxxxx-xxxxxx",
	"display"            : "sh1106",
	"reader_type"        : "Gwiot7941E",
	"left_button"        : 24,
	"right_button"       : 4,
	"relay"              : 26
}
'''
bridge = FabmanBridge(config_file="bridge.json")

# Handle stop button
def callback_left_button(channel):
	if (bridge.is_on()):
		logging.debug("Switching off")
		bridge.stop()
		bridge.relay.off()
GPIO.add_event_detect(bridge.config["left_button"], GPIO.FALLING, callback=callback_left_button, bouncetime=300)

# Run bridge
logging.info("Bridge started")
while (True):
	if (bridge.is_off()):		
		bridge.display_text("Show card to start")
		logging.debug("Waiting for key")
		key = bridge.read_key()
		if (key != False and key is not None):
			if (bridge.access(key)):
				bridge.display_text("Access granted\n\n\n<-STOP")
				logging.debug("Switching on")
				bridge.relay.on()
			else:
				bridge.display_text("Access denied",3)
				logging.debug("Access denied")

