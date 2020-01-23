import requests, json, time, datetime, threading
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from validate_email import validate_email
import RPi.GPIO as GPIO  

class FabmanBridge(object):

	def __init__(self, 
				 api_token, 
				 api_url_base = "https://fabman.io/api/v1/", 
				 heartbeat_interval = 30,
				 stop_button = None,
				 reader_type = "MFRC522"
				):

		try:
			self.api_token = api_token
			self.api_url_base = api_url_base
			self.heartbeat_interval = heartbeat_interval
			self.stop_button = stop_button
			self.reader_type = reader_type
			self.api_header = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(api_token)}
			self.session_id = None
			self.next_heartbeat_call = time.time()
			GPIO.setwarnings(False)
			if (self.reader_type == "MFRC522"):
				self.reader = SimpleMFRC522()
			if (self.heartbeat_interval > 0):
				self.__start_heartbeat_thread()
			if (not(self.stop_button is None)):
				GPIO.setmode(GPIO.BOARD)  
				GPIO.setup(self.stop_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
				GPIO.add_event_detect(self.stop_button, GPIO.FALLING, callback=self.__callback_stop_button, bouncetime=300)
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
				print('Press button to switch off.')
				self.session_id = json.loads(response.content.decode('utf-8'))["sessionId"]
				return True
			else:
				print('Bridge could not be started.')
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
				return True
			else:
				print('Bridge could not be stopped.')
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

	def __start_heartbeat_thread(self):
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
			heartbeat_thread = threading.Timer( self.next_heartbeat_call - time.time(), self.__start_heartbeat_thread )
			heartbeat_thread.daemon = True
			heartbeat_thread.start()
		except Exception as e: 
			print ('Function FabmanBridge.__start_heartbeat_thread raised exception (' + str(e) + ')')
			return False
			
	def __callback_stop_button(self, channel):
		try:
			#print "stop button (gpio" + str(channel) + ") pressed."

			#print "stop_button: " + str(self.stop_button)
			#print "channel (muss gleich sein wie stop_button): " + str(channel)
			#print "is_on (muss True sein): " +str(self.is_on())
			
			if (self.stop_button == channel and self.is_on()):
				print "Switching off ..."
				self.stop()
			else:
				print "stop() wurde nicht aufgerufen"
				
		except Exception as e: 
			print ('Function FabmanBridge.__callback_stop_button raised exception (' + str(e) + ')')
			return False

			


machine = FabmanBridge("710ce79f-684b-40d1-a4e3-0c6e5657d910",	# api token
					   "https://internal.fabman.io/api/v1/", 	# api url base
					   30, 										# heartbeat interval in seconds
					   7, 										# stop button pin number (board mode, e.g. use 7 for GPIO4)
					   "MFRC522"								# card reader type
					  );

while (True):
	if (machine.is_off()):
		print " "
		print "Ready to read nfc key ..."
		#print machine.read_key()
		machine.access(machine.read_key())
		#print "switching on ..."
		#print "is on?"
		#print machine.is_on()
		time.sleep(2)
		
