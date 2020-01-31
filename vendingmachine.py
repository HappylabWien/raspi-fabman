import sys
import RPi.GPIO as GPIO
import time
import pprint
import json
import logging

#https://github.com/dcrystalj/hx711py3
from scale import Scale
from hx711 import HX711

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO) # CRITICAL, ERROR, WARNING, INFO, DEBUG
		 
class VendingMachine(object):

	def __init__(self, bridge = None, config = None): # if no config is given read config from "config.json"
		try:
			self.bridge = bridge
			if (config is None):
				self.load_config()
			else:
				self.config = config
			self.scales = {}
			self.transactions = {}
			self.charge = { 'description' : None, 'price' : 0.0 }
			self._setup()
			#pprint.pprint(self.config)
		except Exception as e: 
			logging.error('Function VendingMachine.__init__ raised exception (' + str(e) + ')')
			return False

	def _setup(self):
		#try:
			for key in self.config:
				print ("Initializing " + key)
				self.scales[key] = Scale(HX711(self.config[key]['dout'],self.config[key]['spd_sck'])) 
				self.scales[key].setReferenceUnit(self.config[key]['ref'])
				self.scales[key].setOffset(self.config[key]['offset'])
				self.scales[key].reset()
				self.transactions[key] = { 
									'weight_new'  : 0.0, 
									'weight_old'  : 0.0, 
									'stock_new'   : 0, 
									'stock_old'   : 0, 
									'weight_loss' : 0, 
									'items_taken' : 0, 
									'description' : "", 
									'price'       : 0.0 
								   }
			return True
		#except Exception as e: 
		#	logging.error('Function VendingMachine.setup raised exception (' + str(e) + ')')
		#	return False
	
	def save_config(self, filename = "config.json"):
		try:
			with open(filename, 'w') as fp:
				json.dump(self.config, fp, sort_keys=True, indent=4)
			return True
		except Exception as e: 
			logging.error('Function VendingMachine.save_config raised exception (' + str(e) + ')')
			return False

	def load_config(self, filename = "config.json"):
		try:
			with open(filename, 'r') as fp:
				self.config = json.load(fp)
			return self.config
		except Exception as e: 
			logging.error('Function VendingMachine.save_config raised exception (' + str(e) + ')')
			return False

	def calibrate(self, scale_key = None): # if no scale_key is provided, all scales will be calibrated
		try:
			#pprint.pprint(self.config)

			calibration_weight = 577 # default value
			answer = input("How heavy is your calibration weight in grams? [" + str(calibration_weight) + "] ")
			if (answer != ""):
				calibration_weight = float(answer)
			for key in self.config:
				if ((scale_key is None) or (key == scale_key)):

					self.scales[key].setReferenceUnit(1)

					print ("\nCalibrating " + key)
					
					input ("EMPTY -> ENTER")
					empty_weight = self.scales[key].getWeight(1)
					#print ("Empty weight (uncalibrated): " + str(empty_weight))
					
					input ("LOADED -> ENTER")
					print ("calibrating...")
					loaded_weight = self.scales[key].getWeight(1)
					#print ("Loaded weight (uncalibrated): " + str(loaded_weight))
					
					self.config[key]['ref'] = (loaded_weight - empty_weight) / calibration_weight
					#print ("Reference unit: " + str(self.config[key]['ref']))

					self.scales[key].setReferenceUnit(self.config[key]['ref'])

					input ("EMPTY -> ENTER")
					print ("taring...")
					#print (self.scales[key].source.OFFSET)
					self.scales[key].tare()
					self.config[key]['offset'] = self.scales[key].source.OFFSET
					#print (self.config[key]['offset'])
					
					#print ("Empty weight (calibrated): " + str(self.scales[key].getWeight(1)))
					#input ("Put your calibration weight onto the scale and press ENTER to continue.")
					#print ("\nLoaded weight (calibrated): " + str(self.scales[key].getWeight(1)))

					print (str(key) + " calibrated.")
					pprint.pprint(self.config[key])
					
			self.save_config()
			
			return self.config
		except Exception as e: 
			logging.error('Function VendingMachine.calibrate raised exception (' + str(e) + ')')
			return False
			
	def tare(self):
		try:
			for key in self.config:
				print ("Taring " + key)
				self.scales[key].reset()
				self.scales[key].tare()
			return True
		except Exception as e: 
			logging.error('Function VendingMachine.setup raised exception (' + str(e) + ')')
			return False


	def run(self):
		try:


			while True:
				try:
					#if (self.bridge is not None):
					#	self.bridge.run()
					
					print ("READY FOR TRANSACTION - SHOW CARD")
					if (self.bridge.access(self.bridge.read_key())): # wait for key card
						print ("ACCESS GRANTED")
						# access granted
						
						# Procedure: 
						#   (1) measure weight before opening door
						#   (2) open door
						#   (3) wait for door to be closed
						#   (4) measure weight at end of transaction again 
						#   (5) create charge
						
						# (1) measure weight before opening door
						for key in self.config:
							weight_old = self.scales[key].getWeight(1)
							stock_old = max(0,round(weight_old / self.config[key]['weight']))
							self.transactions[key] = { 
														'weight_old' : weight_old,
														'stock_old'  : stock_old
													 }
							#pprint.pprint(self.transactions)
							
						# (2) open door - TODO!!!!!!!!!!!!!!
						input ("Press ENTER to open the door...")
						print ("DOOR OPEN")
						input ("Take items and press ENTER to close the door...")
						# (3) wait for door to be closed - TODO!!!!!!!!!!!!!!
						print ("DOOR CLOSED")
						
						# (4) measure weight at end of transaction again 
						for key in self.config:
							weight_new = self.scales[key].getWeight(1)
							weight_loss = self.transactions[key]['weight_old'] - weight_new
							items_taken = round(weight_loss/self.config[key]['weight'])
							stock_new = self.transactions[key]['stock_old'] - items_taken
							if (items_taken != 0):
								print ("Stock change on " + str(key) + ": " + "{:+2d}".format(-items_taken) + " (" + self.config[key]['name'] + ")")  
							if (items_taken > 0):
								description = str(items_taken) + " x " + self.config[key]['name'] + " á " + "{:.2f}".format(self.config[key]['price'])
								price = items_taken * self.config[key]['price']
							else:
								description = None
								price = 0.0
							self.transactions[key].update( { 
												'weight_new'  : weight_new, 
												'stock_new'   : stock_new,
												'weight_loss' : weight_loss, 
												'items_taken' : items_taken, 
												'description' : description, 
												'price'       : price 
											   } )
						
						# (5) create charge
						self.charge = { 'description' : None, 'price' : 0.0 }
						for key in self.transactions:
							if (self.transactions[key]['price'] > 0):
								self.charge['price'] += self.transactions[key]['price']
								if (self.charge['description'] is None):
									self.charge['description'] = str(self.transactions[key]['description'])
								else:
									self.charge['description'] += " and " + self.transactions[key]['description']
									
						pprint.pprint(self.charge)
						
						# TODO!!!!!!!!!!! write charge and metadata to fabman during stop()
						metadata = {
									'config'       : self.config,
									'transactions' : self.transactions,
									'charge'       : self.charge
								   }
						
						print ("----------------")
						#pprint.pprint (self.transactions)
						pprint.pprint (metadata)
						print ("----------------")

						self.bridge.stop(metadata, self.charge) 
						
						#input("\nPress Enter to continue...")			
					else:
						print ("ACCESS DENIED")
						
				except (KeyboardInterrupt, SystemExit):
					GPIO.cleanup()
					sys.exit()


		except Exception as e: 
			logging.error('Function VendingMachine.run raised exception (' + str(e) + ')')
			return False

