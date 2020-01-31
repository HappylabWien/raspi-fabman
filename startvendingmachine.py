#!/usr/bin/python3

from raspifabman import FabmanBridge
from vendingmachine import VendingMachine
from vendingmachine import Vend
import sys # because api token is read from command line

config = { # change default settings
	"api_url_base"       : "https://internal.fabman.io/api/v1/", # api url base / for production systems remove "internal."
	"heartbeat_interval" : 30
}
#bridge = FabmanBridge(sys.argv[1], config)
bridge = FabmanBridge()

vend = None
#vend = Vend() # uncomment this to active vend sync (configure in vend.json)

vending_machine = VendingMachine(bridge, vend) # read config from "articles.json"
vending_machine.run()
