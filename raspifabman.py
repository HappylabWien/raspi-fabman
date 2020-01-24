import requests, json, time, datetime, threading
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522 # GND:9, MOSI:19, MISO:21, SCK:11, RST:22, SDA:24
from validate_email import validate_email
import RPi.GPIO as GPIO  

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
			print ('Function RgbLed.__init__ raised exception (' + str(e) + ')')

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
			print ('Function RgbLed.on raised exception (' + str(e) + ')')

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
			print ('Function RgbLed.off raised exception (' + str(e) + ')')

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
			print ('Function RgbLed.toggle raised exception (' + str(e) + ')')

class FabmanBridge(object):

	def __init__(self, config):
		try:
			self.api_token = config["api_token"]
			self.api_url_base = config["api_url_base"]
			self.heartbeat_interval = config["heartbeat_interval"]
			self.stop_button = config["stop_button"]
			self.reader_type = config["reader_type"]
			self.api_header = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(self.api_token)}
			self.session_id = None
			self.next_heartbeat_call = time.time()
			self.rgbled = RgbLed()
			GPIO.setwarnings(False)
			if (self.reader_type == "MFRC522"):
				self.reader = SimpleMFRC522()
			if (self.heartbeat_interval > 0):
				self._start_heartbeat_thread()
			if (not(self.stop_button is None)):
				GPIO.setmode(GPIO.BOARD)  
				GPIO.setup(self.stop_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
				GPIO.add_event_detect(self.stop_button, GPIO.FALLING, callback=self._callback_stop_button, bouncetime=300)
		except Exception as e: 
			print ('Function FabmanBridge.__init__ raised exception (' + str(e) + ')')

	def access(self,
			   user_id, # user_id can be email address or rfid key
			   chip_type = "nfca" # em4102, nfca, nfcb, nfcf, iso15693, hid
			  ): 
		try:
			if (validate_email(user_id)): # authenticate with email address
				data = { 'emailAddress': user_id, 'configVersion': 0 }
			else: # authenticate with rfid key 
				data = { "keys": [ { "type": chip_type, "token": user_id } ], "configVersion": 0 }
			api_url = '{0}bridge/access'.format(self.api_url_base)
			response = requests.post(api_url, headers=self.api_header, json=data)
			if (response.status_code == 200 and json.loads(response.content.decode('utf-8'))['type'] == "allowed"):
				print('Bridge started successfully.')
				self.rgbled.on("g")
				print('Press button to switch off.')
				self.session_id = json.loads(response.content.decode('utf-8'))["sessionId"]
				return True
			else:
				print('Bridge could not be started.')
				self.display_error()
				return False
		except Exception as e: 
			print ('Function FabmanBridge.access raised exception (' + str(e) + ')')
			return False
	
	def stop(self):
		try:
			api_url = '{0}bridge/stop'.format(self.api_url_base)
			data = { "stopType": "normal", "currentSession": { "id": self.session_id } }
			response = requests.post(api_url, headers=self.api_header, json=data)
			if response.status_code == 200 or response.status_code == 204:
				#self.user_id = None
				self.session_id = None
				print('Bridge stopped successfully.')
				self.rgbled.off("g")
				return True
			else:
				print('Bridge could not be stopped.')
				self.display_error()
				return False			
		except Exception as e: 
			print ('Function FabmanBridge.stop raised exception (' + str(e) + ')')
			return False

	def read_key(self):
		try:
			if (self.reader_type == "MFRC522"):
				return str(hex(self.reader.read_id()))[2:10] # does only work with the sample card provided with the reader!!!!!!
			else:
				print "Undefined reader type"
				return False
		except Exception as e: 
			print ('Function FabmanBridge.read_key raised exception (' + str(e) + ')')
			return False
		
	def is_on(self):
		try:
			if (self.session_id is None):
				return False
			else:
				return True
		except Exception as e: 
			print ('Function FabmanBridge.is_on raised exception (' + str(e) + ')')
			return False
				
	def is_off(self):
		try:
			return not(self.is_on())
		except Exception as e: 
			print ('Function FabmanBridge.is_off raised exception (' + str(e) + ')')
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
			print ('Function FabmanBridge.display_error raised exception (' + str(e) + ')')
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
			print ('Function FabmanBridge.display_error raised exception (' + str(e) + ')')
			return False

	def _start_heartbeat_thread(self):
		try:
			#print datetime.datetime.now()
			api_url = '{0}bridge/heartbeat'.format(self.api_url_base)
			data = { 'configVersion': 0 }
			response = requests.post(api_url, headers=self.api_header, json=data)
			if response.status_code == 200:
				response = json.loads(response.content.decode('utf-8'))
				print("(Heartbeat)")
			else:
				print("Heartbeat failed")
			self.next_heartbeat_call += self.heartbeat_interval
			heartbeat_thread = threading.Timer( self.next_heartbeat_call - time.time(), self._start_heartbeat_thread )
			heartbeat_thread.daemon = True
			heartbeat_thread.start()
		except Exception as e: 
			print ('Function FabmanBridge._start_heartbeat_thread raised exception (' + str(e) + ')')
			return False

	def _callback_stop_button(self, channel):
		try:
			
			if (self.stop_button == channel and self.is_on()):
				print "Switching off ..."
				self.stop()
			else:
				print "stop button (gpio" + str(channel) + ") pressed."
				print "stop_button: " + str(self.stop_button)
				print "channel (muss gleich sein wie stop_button): " + str(channel)
				print "is_on (muss True sein): " +str(self.is_on())

				print "stop() wurde nicht aufgerufen"
				self.display_warning()
				
		except Exception as e: 
			print ('Function FabmanBridge._callback_stop_button raised exception (' + str(e) + ')')
			return False

			

