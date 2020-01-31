#!/usr/bin/python3
import sys
import RPi.GPIO as GPIO
import time
import pprint

#https://github.com/dcrystalj/hx711py3
from scale import Scale
from hx711 import HX711

# settings
config = { 
			'Scale 1' :	{
							'dout':5, 
							'spd_sck':6,
							'ref':2077, # output from calibration procedure	
							'sku': "98098",
							'name': "Büroklammer",
							'weight': .39, # in gram
							'price' : 1
						},
			'Scale 2' :	{
							'dout':23, 
							'spd_sck':24,
							'ref':399, # output from calibration procedure				
							'sku': "98099",
							'name': "Bohrer 2mm",
							'weight': 23.39, # in gram
							'price' : 19.90
						}
		 }
#pprint.pprint (config)

# initialize scales
scales = {}
transactions = {}
#print (config['Scale 1'])
for key in config:
	print ("Initializing " + key)
	scales[key] = Scale(HX711(config[key]['dout'],config[key]['spd_sck'])) 
	scales[key].setReferenceUnit(config[key]['ref'])
	scales[key].reset()
	transactions[key] = { 
						'weight' : 0.0, 
						'prev_weight' : 0.0, 
						'weight_loss' : 0, 
						'items_taken' : 0, 
						'description' : "", 
						'price' : 0.0 
					   }

# tare scales
for key in config:
	print ("Taring " + key)
	scales[key].reset()
	scales[key].tare()


while True:
	try:
		#print ("Measuring...")
		for key in config:
			weight = scales[key].getWeight(1)
			prev_weight = transactions[key]['weight']
			weight_loss = prev_weight - weight
			items_taken = round(weight_loss/config[key]['weight'])
			if (items_taken > 0):
				description = str(items_taken) + " x " + config[key]['name'] + " á " + "{:.2f}".format(config[key]['price'])
				price = items_taken * config[key]['price']
			else:
				description = None
				price = 0.0
				if (items_taken < 0):
					print (str(-items_taken) + " items have been added to " + str(key))
			transactions[key] = { 
								'weight' : weight, 
								'prev_weight' : prev_weight, 
								'weight_loss' : weight_loss, 
								'items_taken' : items_taken, 
								'description' : description, 
								'price' : price 
							   }
		#pprint.pprint (transactions)
		
		# create charge
		charge = { 'description' : None, 'price' : 0.0 }
		for key in transactions:
			if (transactions[key]['price'] > 0):
				charge['price'] += transactions[key]['price']
				if (charge['description'] is None):
					charge['description'] = str(transactions[key]['description'])
				else:
					charge['description'] += ", " + transactions[key]['description']
		pprint.pprint(charge)
		
		input("Press Enter to continue...")			
	except (KeyboardInterrupt, SystemExit):
		GPIO.cleanup()
		sys.exit()
	