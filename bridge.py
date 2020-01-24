from raspifabman import FabmanBridge
import time
import sys

bridge_config = {
	"api_token"          : sys.argv[1],	# read api token from command line
	"api_url_base"       : "https://internal.fabman.io/api/v1/", # api url base / for production systems remove "internal."
	"heartbeat_interval" : 30, # in seconds
	"stop_button"        : 7, # stop button pin number (board mode, e.g. use 7 for GPIO4)
	"reader_type"        : "MFRC522" # for NFC cards (so far, it works only with cards provided with the reader!!!)
}
machine = FabmanBridge(bridge_config)

while (True):
	if (machine.is_off()):
		print " "
		print "Ready to read nfc key ..."
		#print machine.read_key()
		machine.access(machine.read_key())
		#print "switching on ..."
		#print "is on?"
		#print machine.is_on()
		time.sleep(2)

