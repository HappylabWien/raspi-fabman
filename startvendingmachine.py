#!/usr/bin/python3

from raspifabman import FabmanBridge
from vendingmachine import VendingMachine
import sys # because api token is read from command line

config = { # change default settings
	"api_url_base"       : "https://internal.fabman.io/api/v1/", # api url base / for production systems remove "internal."
	"heartbeat_interval" : 30
}
bridge = FabmanBridge(sys.argv[1], config)
vending_machine = VendingMachine(bridge) # read config from "config.json"
vending_machine.run()
