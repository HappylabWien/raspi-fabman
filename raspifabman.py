import requests, json, time, datetime, threading, logging, sys
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # GND:9, MOSI:19, MISO:21, SCK:11, RST:22, SDA:24
#from validate_email import validate_email # is already included in python3 (import for python2.7 needed)
import MFRC522 # from https://github.com/danjperron/MFRC522-python
import serial
import binascii
import pprint

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO) # CRITICAL, ERROR, WARNING, INFO, DEBUG

class Gwiot7941E(object):

	def __init__(self, port = "/dev/ttyS0", baud = 9600):

		try:
			self.ser = serial.Serial(port, baudrate = baud, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS)
		except Exception as e: 
			logging.error('Function Gwiot7941E.__init__ raised exception (' + str(e) + ')')

	def read(self): # duration in seconds (blocking), None means infinite (non-blocking)
		#try:
			#print "Waiting for EM4100 chip..."
			while True:
				nbChars = self.ser.inWaiting()
				if nbChars > 0:
					data = self.ser.read(nbChars)
					data = binascii.b2a_hex(data)
					data = binascii.unhexlify(data)
					checksum_7941E = 0
					for i in range(1, 8):
						checksum_7941E ^= data[i]
					if (checksum_7941E != data[8]):
						logging.error('RFID read error: wrong checksum')
						return False
					checksum_ID12 = 0
					for i in range(3, 8):
						checksum_ID12 ^= data[i]
					fabman_key = 	format(data[3],"x").zfill(2) + format(data[4],"x").zfill(2) + format(data[5],"x").zfill(2) + format(data[6],"x").zfill(2) + format(data[7],"x").zfill(2) + format(checksum_ID12,"x")
					logging.debug ('Successfully read RFID key ' + fabman_key)
					return fabman_key
					
				else:
					time.sleep(0.1)
						
		#except Exception as e: 
		#	logging.error('Function Gwiot7941E.read raised exception (' + str(e) + ')')

class RgbLed(object):

	#def __init__(self, r_pin = 11, g_pin = 13, b_pin = 15): # BOARD mode
	def __init__(self, r_pin = 17, g_pin = 27, b_pin = 22): # BCM mode

		try:
			GPIO.setwarnings(False)
			self.r_pin = r_pin
			self.g_pin = g_pin
			self.b_pin = b_pin
			self.r_state = False
			self.g_state = False
			self.b_state = False
			GPIO.setmode(GPIO.BCM) #GPIO.setmode(GPIO.BOARD)
			GPIO.setup(r_pin, GPIO.OUT, initial= GPIO.LOW)
			GPIO.setup(g_pin, GPIO.OUT, initial= GPIO.LOW)
			GPIO.setup(b_pin, GPIO.OUT, initial= GPIO.LOW)
		except Exception as e: 
			logging.error('Function RgbLed.__init__ raised exception (' + str(e) + ')')

	def on(self,leds,duration = None): # duration in seconds (blocking), None means infinite (non-blocking)
		try:
			if ("r" in leds.lower()):
				GPIO.output(self.r_pin,GPIO.HIGH)
				self.r_state = True
			if ("g" in leds.lower()):
				GPIO.output(self.g_pin,GPIO.HIGH)
				self.r_state = True
			if ("b" in leds.lower()):
				GPIO.output(self.b_pin,GPIO.HIGH)
				self.r_state = True
			if (not(duration is None)):
				time.sleep(duration)
				self.off(leds)
		except Exception as e: 
			logging.error('Function RgbLed.on raised exception (' + str(e) + ')')

	def off(self,leds, duration = None):
		try:
			if ("r" in leds.lower()):
				GPIO.output(self.r_pin,GPIO.LOW)
				self.r_state = False
			if ("g" in leds.lower()):
				GPIO.output(self.g_pin,GPIO.LOW)
				self.r_state = False
			if ("b" in leds.lower()):
				GPIO.output(self.b_pin,GPIO.LOW)
				self.r_state = False
			if (not(duration is None)):
				time.sleep(duration)
				self.on(leds)
		except Exception as e: 
			logging.error('Function RgbLed.off raised exception (' + str(e) + ')')

	def toggle(self,leds):
		try:
			if ("r" in leds.lower()):
				if (self.r_state):
					GPIO.output(self.r_pin,GPIO.LOW)
					self.r_state = False
				else:
					GPIO.output(self.r_pin,GPIO.HIGH)
					self.r_state = True
			if ("g" in leds.lower()):
				if (self.g_state):
					GPIO.output(self.g_pin,GPIO.LOW)
					self.g_state = False
				else:
					GPIO.output(self.g_pin,GPIO.HIGH)
					self.g_state = True
			if ("b" in leds.lower()):
				if (self.b_state):
					GPIO.output(self.b_pin,GPIO.LOW)
					self.b_state = False
				else:
					GPIO.output(self.g_pin,GPIO.HIGH)
					self.b_state = True
		except Exception as e: 
			logging.error('Function RgbLed.toggle raised exception (' + str(e) + ')')

class FabmanBridge(object):

	def __init__(self, config = None): # if no config is given read config from "fabman.json"
		try:
			if (config is None):
				self.load_config()
			else:
				self.config = config
		
			#self.api_token = api_token
			#self.config = { # default values
			#			"api_url_base"       : "https://fabman.io/api/v1/", # api url base / for production systems remove "internal."
			#			"heartbeat_interval" : 30, # in seconds
			#			"stop_button"        : 4, # stop button pin number (BCM mode, e.g. use 4 for GPIO4)
			#			"reader_type"        : "MFRC522" # for NFC cards
			#		  }
			#self.config.update(config)

			#self.api_url_base = config["api_url_base"]
			#self.heartbeat_interval = config["heartbeat_interval"]
			#self.stop_button = config["stop_button"]
			#self.reader_type = config["reader_type"]

			self.api_header = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(self.config['api_token'])}
			self.session_id = None
			self.next_heartbeat_call = time.time()
			self.rgbled = RgbLed()
			GPIO.setwarnings(False)
			if (self.config["reader_type"] == "MFRC522"):
				#self.reader = SimpleMFRC522()
				#self.reader = SimpleMFRC522()
				self.reader = MFRC522.MFRC522()
				self.chip_type = "nfca"
			elif (self.config["reader_type"] == "Gwiot7941E"):
				#print ("setze reader")
				self.reader = Gwiot7941E()
				self.chip_type = "em4102"
			if (self.config["heartbeat_interval"] > 0):
				self._start_heartbeat_thread()
			if (not(self.config["stop_button"] is None)):
				GPIO.setmode(GPIO.BCM) #GPIO.setmode(GPIO.BOARD)  
				GPIO.setup(self.config["stop_button"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
				GPIO.add_event_detect(self.config["stop_button"], GPIO.FALLING, callback=self._callback_stop_button, bouncetime=300)
		except Exception as e: 
			logging.error('Function FabmanBridge.__init__ raised exception (' + str(e) + ')')

	def save_config(self, filename = "fabman.json"):
		try:
			with open(filename, 'w') as fp:
				json.dump(self.config, fp, sort_keys=True, indent=4)
			return True
		except Exception as e: 
			logging.error('Function FabmanBridge.save_config raised exception (' + str(e) + ')')
			return False

	def load_config(self, filename = "fabman.json"):
		try:
			with open(filename, 'r') as fp:
				self.config = json.load(fp)
			return self.config
		except Exception as e: 
			logging.error('Function FabmanBridge.save_config raised exception (' + str(e) + ')')
			return False

	def access(self, user_id):# user_id can be email address or rfid key 
		#try:
			if ("@" in str(user_id)): # authenticate with email address
				data = { 'emailAddress': user_id, 'configVersion': 0 }
			else: # authenticate with rfid key 
				data = { "keys": [ { "type": self.chip_type, "token": user_id } ], "configVersion": 0 }
			api_url = '{0}bridge/access'.format(self.config["api_url_base"])
			response = requests.post(api_url, headers=self.api_header, json=data)
			if (response.status_code == 200 and json.loads(response.content.decode('utf-8'))['type'] == "allowed"):
				logging.info('Bridge started successfully.')
				self.rgbled.on("g")
				logging.debug('Press button to switch off.')
				self.session_id = json.loads(response.content.decode('utf-8'))["sessionId"]
				return True
			else:
				logging.warning('Bridge could not be started.')
				self.display_error()
				return False
		#except Exception as e: 
		#	logging.error('Function FabmanBridge.access raised exception (' + str(e) + ')')
		#	return False
	
	def stop(self, metadata = None, charge = None):
		try:
			api_url = '{0}bridge/stop'.format(self.config["api_url_base"])

			data = { "stopType": "normal", "currentSession": { "id": self.session_id } }
			if (metadata is not None):
				data['currentSession'].update( { 'metadata' : metadata } )
			if (charge is not None):
				data['currentSession'].update( { 'charge' : charge } )			

			'''
			if (metadata is None): # do not set metadata if no data available
				#data = { "stopType": "normal", "currentSession": { "id": sessionId, "idleDurationSeconds": idleTime } }
				data = { "stopType": "normal", "currentSession": { "id": self.session_id } }
			else: # set metadata, if available
				try:
					data = { "stopType": "normal", "currentSession": { "id": sessionId, "idleDurationSeconds": idleTime, "metadata": metadata, "charge": create_charge(get_metadata()) } }
				except: # no charge data available
					data = { "stopType": "normal", "currentSession": { "id": sessionId, "idleDurationSeconds": idleTime, "metadata": metadata } }
			
					data = { 
							"stopType": "normal", 
							"currentSession": { 
												"id": sessionId, 
												"idleDurationSeconds": idleTime, 
												"metadata": metadata, 
												"charge": create_charge(get_metadata()) 
											  } 
						   }		
			'''
			
			response = requests.post(api_url, headers=self.api_header, json=data)
			if response.status_code == 200 or response.status_code == 204:
				#self.user_id = None
				self.session_id = None
				logging.info('Bridge stopped successfully.')
				self.rgbled.off("g")
				return True
			else:
				logging.error('Bridge could not be stopped (status code ' + str(response.status_code) + ')')
				#print("HALLLLLO")
				#pprint.pprint(data)
				#pprint.pprint(response)
				self.display_error()
				return False			
		except Exception as e: 
			logging.error('Function FabmanBridge.stop raised exception (' + str(e) + ')')
			return False

	def read_key(self):
		#try:
			if (self.config["reader_type"] == "MFRC522"):
				#return str(hex(self.reader.read_id()))[2:10] 
				continue_reading = True
				while continue_reading:
					# Scan for cards
					(status, TagType) = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)
					# If a card is found
					if status == self.reader.MI_OK:
						logging.debug("Card detected")
						continue_reading = False
						# Get the UID of the card
						(status, uid) = self.reader.MFRC522_SelectTagSN()
						# If we have the UID, continue
						if status == self.reader.MI_OK:
							uid_string = ""
							for i in uid:
								uid_string += format(i, '02X') 
							logging.debug("Card uid: " + uid_string)
							return uid_string
						else:
							logging.debug("Card authentication error")				
			elif (self.config["reader_type"] == "Gwiot7941E"):
				uid_string = self.reader.read()
				return uid_string
			else:
				logging.error("Undefined reader type")
				return False
		#except Exception as e: 
		#	logging.error('Function FabmanBridge.read_key raised exception (' + str(e) + ')')
		#	return False
		
	def is_on(self):
		try:
			if (self.session_id is None):
				return False
			else:
				return True
		except Exception as e: 
			logging.error('Function FabmanBridge.is_on raised exception (' + str(e) + ')')
			return False
				
	def is_off(self):
		try:
			return not(self.is_on())
		except Exception as e: 
			logging.error('Function FabmanBridge.is_off raised exception (' + str(e) + ')')
			return False

	def display_error(self,message="ERROR"):
		try:
			logging.error(message)
			self.rgbled.on("r",0.1)
			self.rgbled.off("r",0.1)
			self.rgbled.on("r",0.1)
			self.rgbled.off("r",0.1)
			self.rgbled.on("r",0.1)
			self.rgbled.off("r")			
			return True
		except Exception as e: 
			logging.error('Function FabmanBridge.display_error raised exception (' + str(e) + ')')
			return False

	def display_warning(self,message="WARNING"):
		try:
			logging.error(message)
			self.rgbled.on("b",0.1)
			self.rgbled.off("b",0.1)
			self.rgbled.on("b",0.1)
			self.rgbled.off("b",0.1)
			self.rgbled.on("b",0.1)
			self.rgbled.off("b")			
			return True
		except Exception as e: 
			logging.error('Function FabmanBridge.display_error raised exception (' + str(e) + ')')
			return False

	def _start_heartbeat_thread(self):
		try:
			#print datetime.datetime.now()
			api_url = '{0}bridge/heartbeat'.format(self.config["api_url_base"])
			data = { 'configVersion': 0 }
			response = requests.post(api_url, headers=self.api_header, json=data)
			if response.status_code == 200:
				response = json.loads(response.content.decode('utf-8'))
				logging.debug("(Heartbeat)")
			else:
				logging.warning("Heartbeat failed")
			self.next_heartbeat_call += self.config["heartbeat_interval"]
			heartbeat_thread = threading.Timer( self.next_heartbeat_call - time.time(), self._start_heartbeat_thread )
			heartbeat_thread.daemon = True
			heartbeat_thread.start()
		except Exception as e: 
			logging.error('Function FabmanBridge._start_heartbeat_thread raised exception (' + str(e) + ')')
			return False

	def _callback_stop_button(self, channel):
		try:
			
			if (self.config["stop_button"] == channel and self.is_on()):
				logging.debug("Switching off ...")
				self.stop()
			#else:
			#	print "stop button (gpio" + str(channel) + ") pressed."
			#	print "stop_button: " + str(self.config["stop_button"])
			#	print "channel (muss gleich sein wie stop_button): " + str(channel)
			#	print "is_on (muss True sein): " +str(self.is_on())
			#	print "stop() wurde nicht aufgerufen"
			#	self.display_warning()
		except Exception as e: 
			logging.error('Function FabmanBridge._callback_stop_button raised exception (' + str(e) + ')')
			return False
	
	def run(self):
		try:
			logging.info("Bridge started.")
			while (True):
				if (self.is_off()):
					logging.debug("Ready to read nfc key ...")
					self.access(self.read_key())
		except Exception as e: 
			logging.error('Function FabmanBridge.run raised exception (' + str(e) + ')')
			return False

'''
	def run_bg(self): # run as background thread
		try:
			thread = threading.Thread(target=self.run, args=())
			thread.daemon = True                            # Daemonize thread
			thread.start()                                  # Start the execution
		except Exception as e: 
			print ('Function FabmanBridge.run_bg raised exception (' + str(e) + ')')
			return False
'''
