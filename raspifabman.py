import requests, json, time, datetime, threading, logging, sys
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # GND:9, MOSI:19, MISO:21, SCK:11, RST:22, SDA:24
from validate_email import validate_email

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG) # CRITICAL, ERROR, WARNING, INFO, DEBUG

class RgbLed(object):

	def __init__(self, r_pin = 11, g_pin = 13, b_pin = 15):

		try:
			GPIO.setwarnings(False)
			self.r_pin = r_pin
			self.g_pin = g_pin
			self.b_pin = b_pin
			self.r_state = False
			self.g_state = False
			self.b_state = False
			GPIO.setmode(GPIO.BOARD)
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

	def __init__(self, api_token, config = { }):
		try:
			self.api_token = api_token
			self.config = { # default values
						"api_url_base"       : "https://fabman.io/api/v1/", # api url base / for production systems remove "internal."
						"heartbeat_interval" : 30, # in seconds
						"stop_button"        : 7, # stop button pin number (board mode, e.g. use 7 for GPIO4)
						"reader_type"        : "MFRC522" # for NFC cards (so far, it works only with cards provided with the reader!!!)
					  }
			self.config.update(config)
			#self.api_url_base = config["api_url_base"]
			#self.heartbeat_interval = config["heartbeat_interval"]
			#self.stop_button = config["stop_button"]
			#self.reader_type = config["reader_type"]
			self.api_header = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(self.api_token)}
			self.session_id = None
			self.next_heartbeat_call = time.time()
			self.rgbled = RgbLed()
			GPIO.setwarnings(False)
			if (self.config["reader_type"] == "MFRC522"):
				self.reader = SimpleMFRC522()
			if (self.config["heartbeat_interval"] > 0):
				self._start_heartbeat_thread()
			if (not(self.config["stop_button"] is None)):
				GPIO.setmode(GPIO.BOARD)  
				GPIO.setup(self.config["stop_button"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
				GPIO.add_event_detect(self.config["stop_button"], GPIO.FALLING, callback=self._callback_stop_button, bouncetime=300)
		except Exception as e: 
			logging.error('Function FabmanBridge.__init__ raised exception (' + str(e) + ')')

	def access(self,
			   user_id, # user_id can be email address or rfid key
			   chip_type = "nfca" # em4102, nfca, nfcb, nfcf, iso15693, hid
			  ): 
		try:
			if (validate_email(user_id)): # authenticate with email address
				data = { 'emailAddress': user_id, 'configVersion': 0 }
			else: # authenticate with rfid key 
				data = { "keys": [ { "type": chip_type, "token": user_id } ], "configVersion": 0 }
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
		except Exception as e: 
			logging.error('Function FabmanBridge.access raised exception (' + str(e) + ')')
			return False
	
	def stop(self):
		try:
			api_url = '{0}bridge/stop'.format(self.config["api_url_base"])
			data = { "stopType": "normal", "currentSession": { "id": self.session_id } }
			response = requests.post(api_url, headers=self.api_header, json=data)
			if response.status_code == 200 or response.status_code == 204:
				#self.user_id = None
				self.session_id = None
				logging.info('Bridge stopped successfully.')
				self.rgbled.off("g")
				return True
			else:
				logging.warning('Bridge could not be stopped.')
				self.display_error()
				return False			
		except Exception as e: 
			logging.error('Function FabmanBridge.stop raised exception (' + str(e) + ')')
			return False

	def read_key(self):
		try:
			if (self.config["reader_type"] == "MFRC522"):
				# does only work with the sample card provided with the reader!!!!!!
				# solution might be found here: https://www.raspberrypi.org/forums/viewtopic.php?t=154814
				return str(hex(self.reader.read_id()))[2:10] 
			else:
				logging.error("Undefined reader type")
				return False
		except Exception as e: 
			logging.error('Function FabmanBridge.read_key raised exception (' + str(e) + ')')
			return False
		
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
			print(message)
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
			print(message)
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
