# python3

import requests, json, time, datetime, threading, logging, sys, pprint
import RPi.GPIO as GPIO

# for MFRC522 NFC Reader
from mfrc522 import SimpleMFRC522 # GND:9, MOSI:19, MISO:21, SCK:11, RST:22, SDA:24
import MFRC522 # from https://github.com/danjperron/MFRC522-python

# for Gwiot 7941E RFID Reader
import serial
import binascii

# for RGB Led
from gpiozero import RGBLED
from colorzero import Color

# for Email Alerts
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# for OLED Display
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO) # CRITICAL, ERROR, WARNING, INFO, DEBUG

class Gwiot7941E(object):

	def __init__(self, port = "/dev/ttyS0", baud = 9600):
		try:
			self.ser = serial.Serial(port, baudrate = baud, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS)
		except Exception as e: 
			logging.error('Function Gwiot7941E.__init__ raised exception (' + str(e) + ')')

	def read(self): 
		try:
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
					fabman_key = format(data[3],"x").zfill(2) + format(data[4],"x").zfill(2) + format(data[5],"x").zfill(2) + format(data[6],"x").zfill(2) + format(data[7],"x").zfill(2) + format(checksum_ID12,"x")
					logging.info('Successfully read RFID key ' + fabman_key)
					return fabman_key
				else:
					time.sleep(0.5)
		except Exception as e: 
			logging.error('Function Gwiot7941E.read raised exception (' + str(e) + ')')
			return False

'''
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
'''

class FabmanBridge(object):

	def __init__(self, config = None): # if no config is given read config from "fabman.json"
		try:
			# default values
			self.config = {
							"api_url_base"       : "https://fabman.io/api/v1/",
							"heartbeat_interval" : 30,
							"stop_button"        : 4,
							"reader_type"        : "MFRC522",
							"led_r"              : 17,
							"led_g"              : 27,
							"led_b"              : 22,
							"display"            : "SSD1306_128_32"
						  }

			if (config is None):
				self.load_config()
			else:
				self.config.update(config)

			self.api_header = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(self.config['api_token'])}
			self.session_id = None
			self.next_heartbeat_call = time.time()
			self.rgbled = RGBLED(self.config["led_r"], self.config["led_g"], self.config["led_b"])
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
				
			self.screen_message = ""
			
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
				file_config = json.load(fp)
				self.config.update(file_config)
			return self.config
		except Exception as e: 
			logging.error('Function FabmanBridge.save_config raised exception (' + str(e) + ')')
			return False

	def access(self, user_id):# user_id can be email address or rfid key 
		try:
			if ("@" in str(user_id)): # authenticate with email address
				data = { 'emailAddress': user_id, 'configVersion': 0 }
			else: # authenticate with rfid key 
				data = { "keys": [ { "type": self.chip_type, "token": user_id } ], "configVersion": 0 }
			api_url = '{0}bridge/access'.format(self.config["api_url_base"])
			response = requests.post(api_url, headers=self.api_header, json=data)
			if (response.status_code == 200 and json.loads(response.content.decode('utf-8'))['type'] == "allowed"):
				logging.info('Bridge started successfully.')
				#self.rgbled.on("g")
				self.rgbled.color = Color('green')
				logging.debug('Press button to switch off.')
				self.session_id = json.loads(response.content.decode('utf-8'))["sessionId"]
				return True
			else:
				logging.warning('Bridge could not be started (user_id: ' + str(user_id) + ')')
				self.display_error("Access\ndenied")
				return False
		except Exception as e: 
			logging.error('Function FabmanBridge.access raised exception (' + str(e) + ')')
			return False
	
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
				#self.rgbled.off("g")
				self.rgbled.off()
				return True
			else:
				logging.error('Bridge could not be stopped (status code ' + str(response.status_code) + ')')
				self.display_error()
				return False			
		except Exception as e: 
			logging.error('Function FabmanBridge.stop raised exception (' + str(e) + ')')
			return False

	def read_key(self):
		try:
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

	def display_error(self, message = None):
		try:
			#self.rgbled.on("r",0.1)
			#self.rgbled.off("r",0.1)
			#self.rgbled.on("r",0.1)
			#self.rgbled.off("r",0.1)
			#self.rgbled.on("r",0.1)
			#self.rgbled.off("r")	
			self.rgbled.blink(0.1, 0.1, 0, 0, Color('red'), Color('black'), 3, True)
			if (message is not None):
				logging.error(message)
				self.display_text(message, 3)
				print(message)
			return True
		except Exception as e: 
			logging.error('Function FabmanBridge.display_error raised exception (' + str(e) + ')')
			return False

	def display_warning(self, message = None):
		try:
			#self.rgbled.on("b",0.1)
			#self.rgbled.off("b",0.1)
			#self.rgbled.on("b",0.1)
			#self.rgbled.off("b",0.1)
			#self.rgbled.on("b",0.1)
			#self.rgbled.off("b")			
			self.rgbled.blink(0.1, 0.1, 0, 0, Color('yellow'), Color('black'), 3, True)
			if (message is not None):
				logging.warning(message)
				self.display_text(message, 3)
				print(message)
			return True
		except Exception as e: 
			logging.error('Function FabmanBridge.display_error raised exception (' + str(e) + ')')
			return False

	def display_text(self, text= "", duration = None): # duration None = forever
		try:
			if (duration is None):
				self.screen_message = text

			if (self.config["display"] == "SSD1306_128_32"):
			
				# Raspberry Pi pin configuration:
				RST = None     # on the PiOLED this pin isnt used

				# 128x32 display with hardware I2C:
				disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

				# 128x64 display with hardware I2C:
				# disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

				# Note you can change the I2C address by passing an i2c_address parameter like:
				# disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)

				# Alternatively you can specify an explicit I2C bus number, for example
				# with the 128x32 display you would use:
				# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, i2c_bus=2)

				# 128x32 display with hardware SPI:
				# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

				# 128x64 display with hardware SPI:
				# disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

				# Alternatively you can specify a software SPI implementation by providing
				# digital GPIO pin numbers for all the required display pins.  For example
				# on a Raspberry Pi with the 128x32 display you might use:
				# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, sclk=18, din=25, cs=22)

				# Initialize library.
				disp.begin()

				# Clear display.
				disp.clear()
				disp.display()

				# Create blank image for drawing.
				# Make sure to create image with mode '1' for 1-bit color.
				width = disp.width
				height = disp.height
				image = Image.new('1', (width, height))

				# Get drawing object to draw on image.
				draw = ImageDraw.Draw(image)

				# Draw a black filled box to clear the image.
				draw.rectangle((0,0,width,height), outline=0, fill=0)

				# Load default font.
				font = ImageFont.load_default()

				# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
				# Some other nice fonts to try: http://www.dafont.com/bitmap.php
				# font = ImageFont.truetype('Minecraftia.ttf', 8)

				# Draw a black filled box to clear the image.
				draw.rectangle((0,0,width,height), outline=0, fill=0)

				# Draw some shapes.
				# First define some constants to allow easy resizing of shapes.
				x = 0
				padding = -2
				top = padding
				bottom = height-padding
				linespacing = 8

				# Write four lines of text
				lines = text.split("\n")
				if (len(lines) >= 1):
					draw.text((x, top+0*linespacing), lines[0],  font=font, fill=255)
				if (len(lines) >= 2):
					draw.text((x, top+1*linespacing), lines[1],  font=font, fill=255)
				if (len(lines) >= 3):
					draw.text((x, top+2*linespacing), lines[2],  font=font, fill=255)
				if (len(lines) >= 4):
					draw.text((x, top+3*linespacing), lines[3],  font=font, fill=255)

				# Display image.
				disp.image(image)
				disp.display()

				if (duration is not None):
					time.sleep(duration)
					# clear display
					disp.clear()
					disp.display()	
					# recover previous screen message
					lines = self.screen_message.split("\n")
					if (len(lines) >= 1):
						draw.text((x, top+0*linespacing), lines[0],  font=font, fill=255)
					if (len(lines) >= 2):
						draw.text((x, top+1*linespacing), lines[1],  font=font, fill=255)
					if (len(lines) >= 3):
						draw.text((x, top+2*linespacing), lines[2],  font=font, fill=255)
					if (len(lines) >= 4):
						draw.text((x, top+3*linespacing), lines[3],  font=font, fill=255)
					
			else:
				logging.warning('Unsupported display type:' + str(self.config["display"]))
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
					key = self.read_key()
					if (key != False and key is not None):
						self.access()
		except Exception as e: 
			logging.error('Function FabmanBridge.run raised exception (' + str(e) + ')')
			return False

	def send_email(self, subject, text, email_to = None):
		try:
		
			# default values from fabman.json
			if (email_to is None):
				email_to = self.config["email_operator"]
			
			server = smtplib.SMTP(self.config["email_smtp"], self.config["email_port"])
			server.ehlo()
			server.starttls()
			server.login(self.config["email_sender"], self.config["email_password"])

			msg = MIMEMultipart('alternative')
			msg.set_charset('utf8')
			msg['FROM'] = self.config["email_sender"]
			msg['Subject'] = Header(
				subject.encode('utf-8'),
				'UTF-8'
			).encode()
			msg['To'] = email_to
			_attach = MIMEText(text.encode('utf-8'), 'html', 'UTF-8')        
			msg.attach(_attach)
			
			server.sendmail(self.config["email_sender"], [email_to], msg.as_string())

			logging.info('Email "' + subject + '" sent to ' + email_to + ': ' + text)
			server.quit()		

		except Exception as e: 
			logging.error('Sending email "' + subject + '" to ' + email_to + 'FAILED: ' + text)
			logging.error('Function FabmanBridge.send_email raised exception (' + str(e) + ')')
			server.quit()		
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
