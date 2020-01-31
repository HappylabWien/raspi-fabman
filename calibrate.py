#!/usr/bin/python3

from vendingmachine import VendingMachine
import sys

vending_machine = VendingMachine() # read config from "config.json"
if ((len(sys.argv)) == 2):
	vending_machine.calibrate(sys.argv[1])
else:
	vending_machine.calibrate()

