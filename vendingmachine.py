import sys
import RPi.GPIO as GPIO
import time
import pprint
import json
import logging
import requests

# for load cells
# https://github.com/dcrystalj/hx711py3
from scale import Scale
from hx711 import HX711

# for port expander and mux
import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO) # CRITICAL, ERROR, WARNING, INFO, DEBUG

class Scale_PE_MUX(object): # combination of port expander and two multiplexers for multiple hx711 scales

	def __init__(self, i2c_addr = 0x20, channel = 0):	
	
		self.channel = channel
		self.i2c_addr = i2c_addr
				
		# initialize port expander
		i2c = busio.I2C(board.SCL, board.SDA)
		self.mcp = MCP23017(i2c, address=self.i2c_addr)
		
		# DT - yellow (input)
		self.pin_dt_s0 = self.mcp.get_pin(8)
		self.pin_dt_s1 = self.mcp.get_pin(9)
		self.pin_dt_s2 = self.mcp.get_pin(10)
		self.pin_dt_s3 = self.mcp.get_pin(11)
		self.pin_dt_en = self.mcp.get_pin(12)
		
		self.pin_dt_en.switch_to_output(value=True)
		self.pin_dt_s0.switch_to_output(value=True)
		self.pin_dt_s1.switch_to_output(value=True)
		self.pin_dt_s2.switch_to_output(value=True)
		self.pin_dt_s3.switch_to_output(value=True)

		# SCK - orange (output)
		self.pin_sck_s0 = self.mcp.get_pin(0)
		self.pin_sck_s1 = self.mcp.get_pin(1)
		self.pin_sck_s2 = self.mcp.get_pin(2)
		self.pin_sck_s3 = self.mcp.get_pin(3)
		self.pin_sck_en = self.mcp.get_pin(4)
		
		self.pin_sck_en.switch_to_output(value=True)
		self.pin_sck_s0.switch_to_output(value=True)
		self.pin_sck_s1.switch_to_output(value=True)
		self.pin_sck_s2.switch_to_output(value=True)
		self.pin_sck_s3.switch_to_output(value=True)
		
		self.select_channel(self.channel)
		
	def select_channel(self, channel):
		self.channel = channel

		#print ("Set channel to " + str(channel))
		
		# disable MUXs
		self.pin_sck_en.value = True
		self.pin_dt_en.value = True

		# select channel
		if (channel == 0):
			print ("Set channel to 0")
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 0, 0, 0)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 0, 0, 0)
		elif (channel == 1):
			print ("Set channel to 1")
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 0, 0, 1)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 0, 0, 1)
		elif (channel == 2):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 0, 1, 0)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 0, 1, 0)
		elif (channel == 3):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 0, 1, 1)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 0, 1, 1)
		elif (channel == 4):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 1, 0, 0)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 1, 0, 0)
		elif (channel == 5):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 1, 0, 1)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 1, 0, 1)
		elif (channel == 6):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 1, 1, 0)
			(self.pin_dt_s3.value, self.self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 1, 1, 0)
		elif (channel == 7):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 1, 1, 1)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 1, 1, 1)
		elif (channel == 8):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (1, 0, 0, 0)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (1, 0, 0, 0)
		elif (channel == 9):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (1, 0, 0, 1)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (1, 0, 0, 1)
		elif (channel == 10):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (1, 0, 1, 0)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (1, 0, 1, 0)
		elif (channel == 11):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (1, 0, 1, 1)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (1, 0, 1, 1)
		elif (channel == 12):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (1, 1, 0, 0)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (1, 1, 0, 0)
		elif (channel == 13):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (1, 1, 0, 1)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (1, 1, 0, 1)
		elif (channel == 14):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (1, 1, 1, 0)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (1, 1, 1, 0)
		elif (channel == 15):
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (1, 1, 1, 1)	
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (1, 1, 1, 1)	

		# enable MUXs
		self.pin_sck_en.value = False
		self.pin_dt_en.value = False

class Vend(object):

	def __init__(self, config = None): # if no config is given read config from "vend.json"
		try:
			if (config is None):
				self.load_config()
			else:
				self.config = config

			self.vend_api_url_base = "https://fabstore.vendhq.com/api/"
			self.vend_header = {'Content-Type': 'application/json', 'Authorization': 'Bearer {0}'.format(self.config['api_token'])}
			
			self.register_sale_products = []

			#pprint.pprint(self.config)
		except Exception as e: 
			logging.error('Function Vend.__init__ raised exception (' + str(e) + ')')
	
	def save_config(self, filename = "vend.json"):
		try:
			with open(filename, 'w') as fp:
				json.dump(self.config, fp, sort_keys=True, indent=4)
			return True
		except Exception as e: 
			logging.error('Function Vend.save_config raised exception (' + str(e) + ')')
			return False

	def load_config(self, filename = "vend.json"):
		try:
			with open(filename, 'r') as fp:
				self.config = json.load(fp)
			return self.config
		except Exception as e: 
			logging.error('Function Vend.save_config raised exception (' + str(e) + ')')
			return False

	def reset_sale(self): 
		self.register_sale_products = []

	def start_sale(self): 
		self.reset_sale()

	def add_product_to_sale(
								self, 
								product_id, 
								quantity, 
								price, # price per piece excluding tax
								tax # amount of tax per piece (not percentage)
						   ): 
		# API-Doku: https://docs.vendhq.com/tutorials/guides/sales/sales-101
		self.register_sale_products.append({                                             
												"product_id": product_id,               
												"quantity": quantity,
												"price": price, # price per piece excluding tax                                                       
												"tax": tax, # amount of tax per piece (not percentage)
												"tax_id": self.config['tax_id']
										  })
	
	def close_sale(self): # sells all products prevously added with add_product_to_sale
		try:
			vend_endpoint = "register_sales"

			total = 0.0
			for i in range(len(self.register_sale_products)):
				total += self.register_sale_products[i]['quantity'] * (self.register_sale_products[i]['price'] + self.register_sale_products[i]['tax'])

			payload = {
						"register_id": self.config['register_id'],
						"user_id": self.config['user_id'],
						"status": "CLOSED",  
						"register_sale_products" : self.register_sale_products,
						"register_sale_payments": [{
													"register_id": "b1e198a9-f019-11e3-a0f5-b8ca3a64f8f4",              
													"retailer_payment_type_id": self.config['payment_type'],
													"amount" : total
												  }]
					  }
			
			
			#print ("BEGIN PAYLOAD")
			#pprint.pprint(payload)
			#print ("END PAYLOAD")
			
			vend_api_url = self.vend_api_url_base + vend_endpoint
			#print (vend_api_url)
			#print (self.vend_header)

			return requests.post(vend_api_url, headers=self.vend_header, json=payload) 
			
		except Exception as e: 
			logging.error('Function Vend.post_sale raised exception (' + str(e) + ')')

	'''
	def sell_product( # sells one product
						self, 
						product_id, 
						quantity, 
						price, # total price including tax
						tax # total amount of tax (not percentage)
					): # API-Doku: https://docs.vendhq.com/tutorials/guides/sales/sales-101
		#try:
			vend_endpoint = "register_sales"

			payload = {
					"register_id": self.config['register_id'],
					"user_id": self.config['user_id'],
					"status": "CLOSED",                                                     
					"register_sale_products": [{                                            
						"product_id": product_id,               
						"quantity": quantity,                                                      
						"price": price,                                                        
						"tax": tax, # ACHTUNG: Wert in EUR, nicht in % angeben!!!
						"tax_id": self.config['tax_id'],                   
					}],
					"register_sale_payments": [{                                            
						"register_id": "b1e198a9-f019-11e3-a0f5-b8ca3a64f8f4",              
						"retailer_payment_type_id": self.config['payment_type'], 
						#"payment_date": "2020-01-31 12:00:00",                              
						#"amount": 0.0                                                      
					}]
			   }
			
			pprint.pprint(payload)

			vend_api_url = self.vend_api_url_base + vend_endpoint
			print (vend_api_url)
			print (self.vend_header)

			return requests.post(vend_api_url, headers=self.vend_header, json=payload)
			
		#except Exception as e: 
		#	logging.error('Function Vend.post_sale raised exception (' + str(e) + ')')
	'''	
		 
class VendingMachine(object):

	def __init__(self, bridge = None, vend = None, articles = None, config = None): # if no config/articles is given read config from "vendingmachine.json"/"articles.json"
		try:
			self.bridge = bridge
			self.vend = vend
			self.pe = {}
			
			# load article settings
			if (articles is None):
				self.load_articles()
			else:
				self.articles = articles
				
			# use default values, if not set in articles
			for key in self.articles:
				#print("KEY = " + str(key))
				if 'stock_min' not in self.articles[key]:
					self.articles[key]['stock_min'] = 0
				
			self.scales = {}
			self.transactions = {}
			self.charge = { 'description' : "n/a", 'price' : 0.0 }
			#pprint.pprint(self.articles)
			
			# load config
			if (config is None):
				self.load_config()
			else:
				self.config = config
				
			# use default values, if not set in config
			if 'pin_door_status' not in self.config:
				self.config['pin_door_status'] = 16			
			
			GPIO.setmode(GPIO.BCM)
			GPIO.setup(self.config['pin_door_status'], GPIO.IN, GPIO.PUD_UP)

			self._setup()

		except Exception as e: 
			logging.error('Function VendingMachine.__init__ raised exception (' + str(e) + ')')

	def _setup(self):
		try:
			for key in self.articles:
				print ("Initializing " + key)

				self.pe.update( { self.articles[key]['pe_i2c_addr'] : Scale_PE_MUX(int(self.articles[key]['pe_i2c_addr']), int(self.articles[key]['mux_channel'])) } )
				#self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])

				self.bridge.display_text("Initializing\n" + str(key))
				self.scales[key] = Scale(HX711(self.articles[key]['dout'],self.articles[key]['spd_sck'])) 
				self.scales[key].setReferenceUnit(self.articles[key]['ref'])
				self.scales[key].setOffset(self.articles[key]['offset'])
				self.scales[key].reset()
				self.transactions[key] = { 
									'weight_new'  : 0.0, 
									'weight_old'  : 0.0, 
									'stock_new'   : 0, 
									'stock_old'   : 0, 
									'weight_loss' : 0, 
									'items_taken' : 0, 
									'description' : "n/a", 
									'price'       : 0.0 
								   }
			return True
		except Exception as e: 
			logging.error('Function VendingMachine._setup raised exception (' + str(e) + ')')
			return False
	
	def save_articles(self, filename = "articles.json"):
		try:
			with open(filename, 'w') as fp:
				json.dump(self.articles, fp, sort_keys=True, indent=4)
			return True
		except Exception as e: 
			logging.error('Function VendingMachine.save_articles raised exception (' + str(e) + ')')
			return False

	def load_articles(self, filename = "articles.json"):
		try:
			with open(filename, 'r') as fp:
				self.articles = json.load(fp)
			return self.articles
		except Exception as e: 
			logging.error('Function VendingMachine.save_articles raised exception (' + str(e) + ')')
			return False

	def save_config(self, filename = "vendingmachine.json"):
		try:
			with open(filename, 'w') as fp:
				json.dump(self.config, fp, sort_keys=True, indent=4)
			return True
		except Exception as e: 
			logging.error('Function VendingMachine.save_config raised exception (' + str(e) + ')')
			return False

	def load_config(self, filename = "vendingmachine.json"):
		try:
			with open(filename, 'r') as fp:
				self.config = json.load(fp)
			return self.config
		except Exception as e: 
			logging.error('Function VendingMachine.save_config raised exception (' + str(e) + ')')
			return False

	def calibrate(self, scale_key = None): # if no scale_key is provided, all scales will be calibrated
		try:
			#pprint.pprint(self.articles)

			calibration_weight = 577 # default value
			answer = input("How heavy is your calibration weight in grams? [" + str(calibration_weight) + "] ")
			if (answer != ""):
				calibration_weight = float(answer)
			for key in self.articles:
				if ((scale_key is None) or (key == scale_key)):
				
					#self.pe.select_channel(self.articles[key]['mux_channel'])
					self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])

					self.scales[key].setReferenceUnit(1)

					print ("\nCalibrating " + key)
					
					input ("EMPTY -> ENTER")
					empty_weight = self.scales[key].getWeight(1)
					#print ("Empty weight (uncalibrated): " + str(empty_weight))
					
					input ("LOADED -> ENTER")
					print ("calibrating...")
					loaded_weight = self.scales[key].getWeight(1)
					#print ("Loaded weight (uncalibrated): " + str(loaded_weight))
					
					self.articles[key]['ref'] = (loaded_weight - empty_weight) / calibration_weight
					#print ("Reference unit: " + str(self.articles[key]['ref']))

					self.scales[key].setReferenceUnit(self.articles[key]['ref'])

					input ("EMPTY -> ENTER")
					print ("taring...")
					#print (self.scales[key].source.OFFSET)
					self.scales[key].tare()
					self.articles[key]['offset'] = self.scales[key].source.OFFSET
					#print (self.articles[key]['offset'])
					
					#print ("Empty weight (calibrated): " + str(self.scales[key].getWeight(1)))
					#input ("Put your calibration weight onto the scale and press ENTER to continue.")
					#print ("\nLoaded weight (calibrated): " + str(self.scales[key].getWeight(1)))

					print (str(key) + " calibrated.")
					#pprint.pprint(self.articles[key])
					
			self.save_articles()
			
			return self.articles
		except Exception as e: 
			logging.error('Function VendingMachine.calibrate raised exception (' + str(e) + ')')
			return False
			
	def tare(self):
		try:
			for key in self.articles:
				print ("Taring " + key)
				self.scales[key].reset()
				self.scales[key].tare()
			return True
		except Exception as e: 
			logging.error('Function VendingMachine.setup raised exception (' + str(e) + ')')
			return False

	def open_door(self):
		try:
			self.bridge.relay.on()
			time.sleep(2)
			self.bridge.relay.off()
			if (self.door_is_open()):
				logging.info('Door is open.')
				return True
			else:
				logging.error('Opening door failed.')
				return False
		except Exception as e: 
			logging.error('Function VendingMachine.open_door raised exception (' + str(e) + ')')
			return False

	def door_is_open(self):
		try:
			if (GPIO.input(self.config['pin_door_status']) == GPIO.LOW):
				return False
			else:
				return True
		except Exception as e: 
			logging.error('Function VendingMachine.open_door raised exception (' + str(e) + ')')
			return False

	def run(self):
		#try:


			while True:
				try:
					#if (self.bridge is not None):
					#	self.bridge.run()
					
					print ("READY FOR TRANSACTION - SHOW CARD")
					self.bridge.display_text("Swipe your\nmember card\nto start\nshopping...")
					key_id = self.bridge.read_key()
					if (key_id): # avoid processing ghost keys
						if (self.bridge.access(key_id)): # wait for key card
							print ("ACCESS GRANTED")
							# access granted
							
							# Procedure: 
							#   (1) measure weight before opening door
							#   (2) open door
							#   (3) wait for door to be closed
							#   (4) measure weight at end of transaction again 
							#   (5) create charge in fabman
							#   (6) create charge in vend
							
							# (1) measure weight before opening door
							for key in self.articles:
							
								self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
							
								weight_old = self.scales[key].getWeight(1)
								print ("weight_old = " + str(weight_old))
								
								stock_old = max(0,round(weight_old / self.articles[key]['weight']))
								self.transactions[key] = { 
															'weight_old' : weight_old,
															'stock_old'  : stock_old
														 }
								#pprint.pprint(self.transactions)
								
							# (2) open door
							self.bridge.display_text("Access granted\n\nPlease\nopen door...")
							#input ("Press ENTER to open the door...")
							self.open_door()
							self.bridge.display_text("Take items and\nclose door to\nfinish shopping")				
							print ("DOOR OPEN")
							#input ("Take items and press ENTER to close the door...")
							
							# (3) wait for door to be closed
							while (self.door_is_open()):
								time.sleep(0.5)
							print ("DOOR CLOSED")
							self.bridge.display_text("Proecessing\nyour purchase...")
							
							# (4) measure weight at end of transaction again 
							for key in self.articles:
							
								self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
								
								weight_new = self.scales[key].getWeight(1)
								print ("weight_new = " + str(weight_new))

								weight_loss = self.transactions[key]['weight_old'] - weight_new
								items_taken = round(weight_loss/self.articles[key]['weight'])
								stock_new = self.transactions[key]['stock_old'] - items_taken
								if (items_taken != 0):
									print ("Stock change on " + str(key) + ": " + "{:+2d}".format(-items_taken) + " (" + self.articles[key]['name'] + ")")  
								if (items_taken > 0):
									description = str(items_taken) + " x " + self.articles[key]['name'] + " á " + "{:.2f}".format(self.articles[key]['price'])
									price = items_taken * self.articles[key]['price']
								else:
									description = "n/a"
									price = 0.0
										
								self.transactions[key].update( { 
													'weight_new'  : weight_new, 
													'stock_new'   : stock_new,
													'weight_loss' : weight_loss, 
													'items_taken' : items_taken, 
													'description' : description, 
													'price'       : price 
												   } )
							
								if (items_taken < 0):
									self.bridge.send_email("Fabman Vending Machine: Stock Level Increased", "Article:<br>" + str(self.articles[key]) + "<br><br>Transaction Details:<br>" + str(self.transactions[key]))
								if (items_taken > 0 and self.transactions[key]['stock_new'] <= self.articles[key]['stock_min']):
									self.bridge.send_email("Fabman Vending Machine: Minimum Stock Level Reached", "Article:<br>" + str(self.articles[key]) + "<br><br>Transaction Details:<br>" + str(self.transactions[key]))

							# (5) create charge in fabman
							self.charge = { 'description' : "n/a", 'price' : 0.0 }
							items_charged = 0
							for key in self.transactions:
								if (self.transactions[key]['items_taken'] > 0):
									items_charged += self.transactions[key]['items_taken']
									self.charge['price'] += self.transactions[key]['price']
									if (self.charge['description'] == "n/a"):
										self.charge['description'] = str(self.transactions[key]['description'])
									else:
										self.charge['description'] += " and " + self.transactions[key]['description']
							pprint.pprint(self.charge)
							metadata = {
										'articles'     : self.articles,
										'transactions' : self.transactions,
										'charge'       : self.charge
									   }
							
							#print ("----------------")
							#pprint.pprint (self.transactions)
							#pprint.pprint (metadata)
							#print ("----------------")

							self.bridge.stop(metadata, self.charge) 
							
							# show transaction summary on display
							if (items_charged == 1):
								text = "1 item taken"
							else:
								text = str(items_charged) + " items taken"
							text += "\nEUR {:.2f}".format(self.charge['price']) + " charged\n\nTHANK YOU!"
							self.bridge.display_text(text, 5)
							
							# (6) create charge in vend
							if (self.vend is not None):
								self.vend.start_sale()
								tax_percent = self.vend.config['tax_percent']
								for key in self.transactions:
									if (self.transactions[key]['items_taken'] > 0):
										self.vend.add_product_to_sale(self.articles[key]['product_id'], self.transactions[key]['items_taken'], self.articles[key]['price']/(100+tax_percent)*100, self.articles[key]['price']/(100+tax_percent)*tax_percent)
								response = self.vend.close_sale()
								if response.status_code == 200:
									print("Vend sale posted successfully.")
									response = json.loads(response.content.decode('utf-8'))
									pprint.pprint(response)
								else:
									print("Vend sale FAILED.")
									pprint.pprint(response)
							
							#input("\nPress Enter to continue...")			
						else:
							print ("ACCESS DENIED")
							self.bridge.display_text("Access\ndenied", 3)
							#self.bridge.display_text("Proecessing\nyour purchase...", 3)
					#else:
					#	print ("Ghost key detected -> discard")
				except (KeyboardInterrupt, SystemExit):
					GPIO.cleanup()
					sys.exit()

		#except Exception as e: 
		#	logging.error('Function VendingMachine.run raised exception (' + str(e) + ')')
		#	return False

		
'''		
from raspifabman import FabmanBridge
from vendingmachine import VendingMachine
from vendingmachine import Vend
import sys # because api token is read from command line
import datetime

config = { # change default settings
	"api_url_base"       : "https://internal.fabman.io/api/v1/", # api url base / for production systems remove "internal."
	"heartbeat_interval" : 30
}
#bridge = FabmanBridge(sys.argv[1], config)
bridge = FabmanBridge() # read config from "fabman.json"

vend = None
#vend = Vend() # uncomment this to active vend sync (configure in vend.json)

vending_machine = VendingMachine(bridge, vend) # read config from "articles.json"

#print(vending_machine.open_door())
#vending_machine.run()

pprint.pprint(vending_machine.pe[32])

#	# 1kg load cell
#	vending_machine.pe[32].select_channel(0)
#	weight = vending_machine.scales['Scale 0'].getWeight(1)
#	print("weight scale 0: " + "{:.2f}".format(weight) + " g")

# 5kg load cell
vending_machine.pe[32].select_channel(1)
weight = vending_machine.scales['Scale 1'].getWeight(1)
print("weight scale 1: " + "{:.2f}".format(weight) + " g")
'''
'''
while (True):
	print ("\n***" + str(datetime.datetime.now()) + "***")

	# 1kg load cell
	vending_machine.pe[32].select_channel(0)
	weight = vending_machine.scales['Scale 0'].getWeight(1)
	print("weight scale 0: " + "{:.2f}".format(weight) + " g")

	# 5kg load cell
	vending_machine.pe[32].select_channel(1)
	weight = vending_machine.scales['Scale 1'].getWeight(1)
	print("weight scale 1: " + "{:.2f}".format(weight) + " g")
'''
