#!/usr/bin/python3

from raspifabman import FabmanBridge
from vendingmachine import VendingMachine
import sys

bridge = FabmanBridge() # read config from "fabman.json"
vending_machine = VendingMachine(bridge) # read config from "config.json"
if ((len(sys.argv)) == 2):
	vending_machine.calibrate(sys.argv[1])
else:
	vending_machine.calibrate()

