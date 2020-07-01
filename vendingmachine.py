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
import statistics

# for port expander and mux
import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017

# for background offset adjustment
import threading

logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO) # CRITICAL, ERROR, WARNING, INFO, DEBUG

class PortExpander(object): # combination of port expander and multiplexers for multiple hx711 scales

	def __init__(self, i2c_addr = 0x20):	
	
		self.channel = None
		self.i2c_addr = i2c_addr
				
		# initialize port expander
		i2c = busio.I2C(board.SCL, board.SDA)
		self.mcp = MCP23017(i2c, address=self.i2c_addr)
		
		# DT - yellow (input)

		self.pin_dt1_s0 = self.mcp.get_pin(0)
		self.pin_dt1_s1 = self.mcp.get_pin(1)
		self.pin_dt1_s2 = self.mcp.get_pin(2)
		self.pin_dt1_en = self.mcp.get_pin(3)

		self.pin_dt2_s0 = self.mcp.get_pin(4)
		self.pin_dt2_s1 = self.mcp.get_pin(5)
		self.pin_dt2_s2 = self.mcp.get_pin(6)
		self.pin_dt2_en = self.mcp.get_pin(7)
		
		self.pin_dt1_en.switch_to_output(value=True)
		self.pin_dt1_s0.switch_to_output(value=True)
		self.pin_dt1_s1.switch_to_output(value=True)
		self.pin_dt1_s2.switch_to_output(value=True)

		self.pin_dt2_en.switch_to_output(value=True)
		self.pin_dt2_s0.switch_to_output(value=True)
		self.pin_dt2_s1.switch_to_output(value=True)
		self.pin_dt2_s2.switch_to_output(value=True)

		# SCK - orange (output)
		self.pin_sck1_s0 = self.mcp.get_pin(8)
		self.pin_sck1_s1 = self.mcp.get_pin(9)
		self.pin_sck1_s2 = self.mcp.get_pin(10)
		self.pin_sck1_en = self.mcp.get_pin(11)

		self.pin_sck2_s0 = self.mcp.get_pin(12)
		self.pin_sck2_s1 = self.mcp.get_pin(13)
		self.pin_sck2_s2 = self.mcp.get_pin(14)
		self.pin_sck2_en = self.mcp.get_pin(15)
		
		self.pin_sck1_en.switch_to_output(value=True)
		self.pin_sck1_s0.switch_to_output(value=True)
		self.pin_sck1_s1.switch_to_output(value=True)
		self.pin_sck1_s2.switch_to_output(value=True)

		self.pin_sck2_en.switch_to_output(value=True)
		self.pin_sck2_s0.switch_to_output(value=True)
		self.pin_sck2_s1.switch_to_output(value=True)
		self.pin_sck2_s2.switch_to_output(value=True)
		
	def select_channel(self, channel):
		self.channel = channel

		#print ("Set channel to " + str(channel))
		
		# disable MUXs
		#self.pin_sck_en.value = True
		#self.pin_dt_en.value = True

		# select channel
		if (channel == 0):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 1):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (1, 1)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 2):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (1, 1)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 3):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (1, 1)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (1, 1)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 4):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (1, 1)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 5):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (1, 1)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (1, 1)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 6):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (1, 1)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (1, 1)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 7):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (1, 1)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (1, 1)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (1, 1)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 8):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 9):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (1, 1)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 10):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (1, 1)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 11):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (1, 1)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (1, 1)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 12):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (1, 1)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 13):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (1, 1)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (1, 1)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 14):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (1, 1)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (1, 1)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 15):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (1, 1)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (1, 1)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (1, 1)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)

	def disable(self):
		# disable MUXs
		self.pin_sck1_en.value = True
		self.pin_sck2_en.value = True
		self.pin_dt1_en.value = True
		self.pin_dt2_en.value = True

'''
class Scale_PE_MUX(object): # combination of port expander and multiplexers for multiple hx711 scales

	def __init__(self, i2c_addr = 0x20, channel = 0):	
	
		self.channel = channel
		self.i2c_addr = i2c_addr
				
		# initialize port expander
		i2c = busio.I2C(board.SCL, board.SDA)
		self.mcp = MCP23017(i2c, address=self.i2c_addr)
		
		# DT - yellow (input)

		self.pin_dt1_s0 = self.mcp.get_pin(0)
		self.pin_dt1_s1 = self.mcp.get_pin(1)
		self.pin_dt1_s2 = self.mcp.get_pin(2)
		self.pin_dt1_en = self.mcp.get_pin(3)

		self.pin_dt2_s0 = self.mcp.get_pin(4)
		self.pin_dt2_s1 = self.mcp.get_pin(5)
		self.pin_dt2_s2 = self.mcp.get_pin(6)
		self.pin_dt2_en = self.mcp.get_pin(7)
		
		self.pin_dt1_en.switch_to_output(value=True)
		self.pin_dt1_s0.switch_to_output(value=True)
		self.pin_dt1_s1.switch_to_output(value=True)
		self.pin_dt1_s2.switch_to_output(value=True)

		self.pin_dt2_en.switch_to_output(value=True)
		self.pin_dt2_s0.switch_to_output(value=True)
		self.pin_dt2_s1.switch_to_output(value=True)
		self.pin_dt2_s2.switch_to_output(value=True)

		# SCK - orange (output)
		self.pin_sck1_s0 = self.mcp.get_pin(8)
		self.pin_sck1_s1 = self.mcp.get_pin(9)
		self.pin_sck1_s2 = self.mcp.get_pin(10)
		self.pin_sck1_en = self.mcp.get_pin(11)

		self.pin_sck2_s0 = self.mcp.get_pin(12)
		self.pin_sck2_s1 = self.mcp.get_pin(13)
		self.pin_sck2_s2 = self.mcp.get_pin(14)
		self.pin_sck2_en = self.mcp.get_pin(15)
		
		self.pin_sck1_en.switch_to_output(value=True)
		self.pin_sck1_s0.switch_to_output(value=True)
		self.pin_sck1_s1.switch_to_output(value=True)
		self.pin_sck1_s2.switch_to_output(value=True)

		self.pin_sck2_en.switch_to_output(value=True)
		self.pin_sck2_s0.switch_to_output(value=True)
		self.pin_sck2_s1.switch_to_output(value=True)
		self.pin_sck2_s2.switch_to_output(value=True)
		
		self.disable()
		self.select_channel(self.channel)
		
	def select_channel(self, channel):
		self.channel = channel

		#print ("Set channel to " + str(channel))
		
		# disable MUXs
		#self.pin_sck_en.value = True
		#self.pin_dt_en.value = True

		# select channel
		if (channel == 0):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 1):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (1, 1)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 2):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (1, 1)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 3):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (1, 1)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (1, 1)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 4):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (1, 1)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 5):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (1, 1)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (1, 1)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 6):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (1, 1)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (1, 1)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 7):
			(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (1, 1)
			(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (1, 1)
			(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (1, 1)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (0, 0)
			
			#(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			#(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			#(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (1, 1)
		elif (channel == 8):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 9):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (1, 1)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 10):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (1, 1)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 11):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (1, 1)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (1, 1)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (0, 0)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 12):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (1, 1)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 13):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (1, 1)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (0, 0)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (1, 1)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 14):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (0, 0)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (1, 1)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (1, 1)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)
		elif (channel == 15):
			#(self.pin_dt1_s0.value, self.pin_sck1_s0.value) = (0, 0)
			#(self.pin_dt1_s1.value, self.pin_sck1_s1.value) = (0, 0)
			#(self.pin_dt1_s2.value, self.pin_sck1_s2.value) = (0, 0)
			(self.pin_dt1_en.value, self.pin_sck1_en.value) = (1, 1)
			
			(self.pin_dt2_s0.value, self.pin_sck2_s0.value) = (1, 1)
			(self.pin_dt2_s1.value, self.pin_sck2_s1.value) = (1, 1)
			(self.pin_dt2_s2.value, self.pin_sck2_s2.value) = (1, 1)
			(self.pin_dt2_en.value, self.pin_sck2_en.value) = (0, 0)

		# enable MUXs
		#self.pin_sck_en.value = False
		#self.pin_dt_en.value = False

	def disable(self):
		# disable MUXs
		self.pin_sck1_en.value = True
		self.pin_sck2_en.value = True
		self.pin_dt1_en.value = True
		self.pin_dt2_en.value = True
		
		
	def enable(self):
		# enable MUXs
		pass
		#self.pin_sck1_en.value = False
		#self.pin_sck2_en.value = False
		#self.pin_dt1_en.value = False
		#self.pin_dt2_en.value = False


class Scale_PE_MUX_analog(object): # combination of port expander and two multiplexers for multiple hx711 scales

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
		
		self.disable()
		self.select_channel(self.channel)
		
	def select_channel(self, channel):
		self.channel = channel

		#print ("Set channel to " + str(channel))
		
		# disable MUXs
		#self.pin_sck_en.value = True
		#self.pin_dt_en.value = True

		# select channel
		if (channel == 0):
			#print ("Set channel to 0")
			(self.pin_sck_s3.value, self.pin_sck_s2.value, self.pin_sck_s1.value, self.pin_sck_s0.value) = (0, 0, 0, 0)
			(self.pin_dt_s3.value, self.pin_dt_s2.value, self.pin_dt_s1.value, self.pin_dt_s0.value) = (0, 0, 0, 0)
		elif (channel == 1):
			#print ("Set channel to 1")
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
		#self.pin_sck_en.value = False
		#self.pin_dt_en.value = False

	def disable(self):
		# disable MUXs
		self.pin_sck_en.value = True
		self.pin_dt_en.value = True
		
	def enable(self):
		# enable MUXs
		self.pin_sck_en.value = False
		self.pin_dt_en.value = False
'''
		
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
				json.dump(self.config, fp, sort_keys=False, indent=4)
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

	'''
	Example for articles.json
	{
		"Scale 32-0": {
			"pe_i2c_addr": 32,
			"mux_channel": 0,
			"name": "VHM Fr\u00e4ser 2-Schneider 3mm lang",
			"ref": 1840.6576344086022,
			"offset": 194330.08058494623,
			"price": 15.9,
			"weight": 3.22,
			"stock_min": 1,
			"product_id": "dd50b798-cf73-11e3-a0f5-b8ca3a64f8f4",
			"stock": 3
		}
	}
	'''

	def __init__(self, bridge = None, vend = None, articles = None, config = None): # if no config/articles is given read config from "vendingmachine.json"/"articles.json"
		try:
		
			# set enable pin for nfc reader and spi display and switch on power for mux boards
			GPIO.setmode(GPIO.BCM)
			GPIO.setup(25, GPIO.OUT)
			GPIO.output(25, 1)
		
			self.bridge = bridge
			self.vend = vend
			self.pe = {}
			self.in_transaction = False
			
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
			if 'pin_dout' not in self.config:
				self.config['pin_dout'] = 5				
			if 'pin_spd_sck' not in self.config:
				self.config['pin_spd_sck'] = 6				
			
			GPIO.setmode(GPIO.BCM)
			GPIO.setup(self.config['pin_door_status'], GPIO.IN, GPIO.PUD_UP)

			self._setup()
			
			# initialize stock values
			for key in self.articles:
				'''
				self.pe[self.articles[key]['pe_i2c_addr']].disable()
				self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
				
				#print ("=========> VALUE 1ST READ from " + str(key) + ": " + str(self.scales[key].source.read()))
				
				weight_old = self.scales[key].getWeight(1)
				'''

				weight = self.get_weight(key)

				logging.info("Weight on " + str(key) + " = " + str(weight))

				if 'stock' not in self.articles[key]:
					self.articles[key]['stock'] = max(0,round(weight_old / self.articles[key]['weight']))

				self.transactions[key] = { 
											'weight_old' : weight,
											'weight_new' : weight,
											'stock_old'  : self.articles[key]['stock'],
											'stock_new'  : self.articles[key]['stock']
										 }

				'''
				self.pe[self.articles[key]['pe_i2c_addr']].disable()
				'''
				
				#self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
				#print ("=========> VALUE 2ND READ from " + str(key) + ": " + str(self.scales[key].source.read()))
				
				

			#pprint.pprint(self.transactions)
			#input("initial stock values set ... weiter -> ENTER")
			
			# beep when initialization completed
			self.bridge.buzzer.beep(n=1)
			
		except Exception as e: 
			logging.error('Function VendingMachine.__init__ raised exception (' + str(e) + ')')

	def _setup(self):
		try:
			for key in self.articles:
				logging.info("Initializing " + key)
				self.bridge.display_text("Initializing\n" + str(key))
				
				#self.pe.update( { self.articles[key]['pe_i2c_addr'] : Scale_PE_MUX(int(self.articles[key]['pe_i2c_addr']), int(self.articles[key]['mux_channel'])) 	} )
				self.pe.update( { self.articles[key]['pe_i2c_addr'] : PortExpander(int(self.articles[key]['pe_i2c_addr']))} )
				logging.info("Add Port Expander on i2c Address " + str(int(self.articles[key]['pe_i2c_addr'])))

				#self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])

				#self.pe[self.articles[key]['pe_i2c_addr']].disable()
				#self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
				#self.pe[self.articles[key]['pe_i2c_addr']].enable()
				
				#self.scales[key] = Scale(HX711(self.articles[key]['dout'],self.articles[key]['spd_sck'])) 
				self.scales[key] = Scale(HX711(self.config['pin_dout'],self.config['pin_spd_sck'])) 
				self.scales[key].setReferenceUnit(self.articles[key]['ref'])
				self.scales[key].setOffset(self.articles[key]['offset'])
				self.scales[key].reset()
				self.transactions[key] = { 
									'weight_new'  : self.articles[key]['stock'] * self.articles[key]['weight'], 
									'weight_old'  : self.articles[key]['stock'] * self.articles[key]['weight'], 
									'stock_new'   : self.articles[key]['stock'], 
									'stock_old'   : self.articles[key]['stock'], 
									'weight_loss' : 0, 
									'items_taken' : 0, 
									'description' : "n/a", 
									'price'       : 0.0 
								   }
								   
				#self.pe[self.articles[key]['pe_i2c_addr']].enable()
			self.bridge.display_text("Initialization\ncompleted.")
			return True
		except Exception as e: 
			logging.error('Function VendingMachine._setup raised exception (' + str(e) + ')')
			return False
	
	def save_articles(self, filename = "articles.json"):
		try:
			#try:
				with open(filename, 'w') as fp:
					json.dump(self.articles, fp, sort_keys=False, indent=4)
				return True
			#except KeyboardInterrupt:
			#	return False
		except Exception as e: 
			logging.error('Function VendingMachine.save_articles raised exception (' + str(e) + ')')
			return False

	def load_articles(self, filename = "articles.json"):
		try:
			with open(filename, 'r') as fp:
				self.articles = json.load(fp)
			return self.articles
		except Exception as e: 
			logging.error('Function VendingMachine.load_articles raised exception (' + str(e) + ')')
			return False

	def save_config(self, filename = "vendingmachine.json"):
		try:
			with open(filename, 'w') as fp:
				json.dump(self.config, fp, sort_keys=False, indent=4)
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

			calibration_weight = 395 # default value 
			answer = input("How heavy is your calibration weight in grams? [" + str(calibration_weight) + "] ")
			if (answer != ""):
				calibration_weight = float(answer)
			for key in self.articles:
				if ((scale_key is None) or (key == scale_key)):
				
					self.pe[self.articles[key]['pe_i2c_addr']].disable()
					self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
					self.scales[key].reset()
					
					#print ("=========> VALUE READ from " + str(key) + ": " + str(self.scales[key].source.read()))
					
					
					
					
					self.scales[key].setReferenceUnit(1)
					self.scales[key].setOffset(0)
					
					print ("\nCalibrating " + key)
					
					input ("EMPTY -> ENTER")
					#empty_weight = self.scales[key].getWeight(1)
					empty_weight = self.get_weight(key)
					
					print ("*** Empty weight (uncalibrated): " + str(empty_weight))
					
					input ("LOADED -> ENTER")
					print ("calibrating...")
					#loaded_weight = self.scales[key].getWeight(1)
					loaded_weight = self.get_weight(key)
					
					print ("*** Loaded weight (uncalibrated): " + str(loaded_weight))
					
					self.articles[key]['ref'] = (loaded_weight - empty_weight) / calibration_weight
					print ("*** Reference unit: " + str(self.articles[key]['ref']))

					self.scales[key].setReferenceUnit(self.articles[key]['ref'])

					'''
					input ("EMPTY -> ENTER")
					print ("taring...")
					print ("Source Offset: " + str(self.scales[key].source.OFFSET))
					self.scales[key].tare()
					self.articles[key]['offset'] = self.scales[key].source.OFFSET
					print ("Offset: " + str(self.articles[key]['offset']))
					'''
					
					self.articles[key]['offset'] = empty_weight #* self.articles[key]['ref']
					self.scales[key].setOffset(self.articles[key]['offset'])
					print ("*** Offset: " + str(self.articles[key]['offset']))
					
					
					
					#print ("Empty weight (calibrated): " + str(self.scales[key].getWeight(1)))
					#input ("Put your calibration weight onto the scale and press ENTER to continue.")
					#print ("\nLoaded weight (calibrated): " + str(self.scales[key].getWeight(1)))

					print (str(key) + " calibrated.")
					#pprint.pprint(self.articles[key])
					self.pe[self.articles[key]['pe_i2c_addr']].disable()
					
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
			
	def get_weight(self,key,times=3): # key is the article key from articles.json
		try:
			self.pe[self.articles[key]['pe_i2c_addr']].disable()
			self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
			self.scales[key].reset()

			#cut = times//5
			values = sorted([self.scales[key].source.read() for i in range(times)])#[cut:-cut]
			#pprint.pprint(values)
			value = statistics.mean(values)
			#value = self.scales[key].source.read()
			
			ref = self.scales[key].source.REFERENCE_UNIT
			offset = self.scales[key].source.OFFSET
			#print ("Value (original) for " + str(key) + ": " + str(value))
			#print ("ref = " + str(ref))
			#print ("offset = " + str(offset))
			weight = (value - offset) / ref
			
			#weight = self.scales[key].getWeight(times)
			#print ("Weight on " + str(key) + " = " + str(weight_old))
			
			self.pe[self.articles[key]['pe_i2c_addr']].disable()
			
			return weight
			
		except Exception as e: 
			logging.error('Function VendingMachine.get_weight raised exception (' + str(e) + ')')
			return False
		
	def show_weights(self):
		while True:
			print ("---------------------")
			for key in self.articles:
				#self.get_weight(key)
				print (str(key) + ": " + str(self.get_weight(key)))
			time.sleep(1)

	def adjust_offset(self, scale_key = None): # if no scale_key is provided, all scales will be calibrated
		#try:
			#pprint.pprint(self.articles)


			for key in self.articles:
				if ((scale_key is None) or (key == scale_key)):
				
					#print ("Adjust Offset for Scale " + str(key))
					#print ("   Old Offset:            " + str(self.articles[key]['offset']))
					offset_old = self.articles[key]['offset']
				
					weight_actual = self.get_weight(key)
					#print ("   Actual (wrong) Weight: " + str(weight_actual))

					if (weight_actual != False):
						#pprint.pprint(self.transactions)
						weight_target = self.transactions[key]['stock_new'] * self.articles[key]['weight']
						#print ("   Weight should be:      " + str(weight_target) + " (" + str(self.transactions[key]['stock_new']) + " * " + str(self.articles[key]['weight']) + "g)")

						weight_error = weight_actual - weight_target
						offset_error = weight_error * self.articles[key]['ref']
						#print ("   Offset Error:          " + str(offset_error) + " (" + str(weight_error) + " * " + str(offset_error) + ")")

						self.articles[key]['offset'] += offset_error
						self.scales[key].setOffset(self.articles[key]['offset'])
						
						#print ("   New Offset:            " + str(self.articles[key]['offset']))

						#print ("Offset for Scale " + str(key) + " adjusted ( " + str(offset_old) + " => " + str(self.articles[key]['offset']) + " / weight = " + str(self.get_weight(key)) + "g )")
						logging.info('Offset for Scale "' + str(key) + '" adjusted (' + str(offset_old) + " => " + str(self.articles[key]['offset']) + ")")
			
			#if (self.get_weight(key) == False):
			#print ("SAVE " + str(self.articles[key]['offset']))
			self.save_articles()
				
			return self.articles
		#except Exception as e: 
		#	logging.error('Function VendingMachine.adjust_offset raised exception (' + str(e) + ')')
		#	return False

	def adjust_offset_thread(self, wait_during_transaction=30, wait_between_adjustments=60):
		try:
			while True:
				for key in self.articles:
					while (self.in_transaction == True):
						print ("Waiting for end of transaction to continue adjusting offset values. (in_transaction = " + str(self.in_transaction) + ")")
						time.sleep(wait_during_transaction)
					self.adjust_offset(key)
				time.sleep(wait_between_adjustments)
		except KeyboardInterrupt:
			return False
			
	def run(self):
		#try:

			# start background thread to adjust offste values
			t_adjust_offset = threading.Thread(target=self.adjust_offset_thread)
			t_adjust_offset.daemon = True
			t_adjust_offset.start()

			while True:
				try:
					#if (self.bridge is not None):
					#	self.bridge.run()
					
					logging.info("Ready for transaction - waiting for card.")
					self.in_transaction = False
					self.bridge.display_text("Swipe your\nmember card\nto start\nshopping...")
					key_id = self.bridge.read_key()
					if (key_id): # avoid processing ghost keys
						if (self.bridge.access(key_id)): # wait for key card
							self.bridge.buzzer.beep(on_time=0.1, off_time=0, n=1, background=False)
							logging.info("Access granted.")
							self.in_transaction = True
							# access granted
							
							# Procedure: 
							#   (1) measure initial stock values at startup (see __init__)
							#   (2) open door
							#   (3) wait for door to be closed
							#   (4) measure weight at end of transaction again 
							#   (5) create charge in fabman
							#   (6) create charge in vend
							#   (7) save new stock values for next transaction
							
							'''
							# (1) measure weight before opening door
							for key in self.articles:
							
								self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
								#self.pe[self.articles[key]['pe_i2c_addr']].enable()
								weight_old = self.scales[key].getWeight(1)
								print ("weight_old = " + str(weight_old))
								
								stock_old = max(0,round(weight_old / self.articles[key]['weight']))
								self.transactions[key] = { 
															'weight_old' : weight_old,
															'stock_old'  : stock_old
														 }
								self.pe[self.articles[key]['pe_i2c_addr']].disable()
							'''
							#pprint.pprint(self.transactions)
							#input("weiter...-> ENTER")
							
							# (2) open door
							self.bridge.display_text("Access granted\n\nPlease\nopen doors...")
							#input ("Press ENTER to open the door...")
							self.open_door()
							self.bridge.display_text("Take items and\nclose BOTH doors\nto finish shopping")				
							#logging.info("Door is open.")
							#input ("Take items and press ENTER to close the door...")
							
							# (3) wait for door to be closed
							while (self.door_is_open()):
								time.sleep(0.5)
							logging.info("Door is closed - processing purchase")
							#self.bridge.display_text("Processing\nyour purchase...")
							
							# (4) measure weight at end of transaction again 
							for key in self.articles:
								#print("Checking Scale " + str(key) + "...")
								self.bridge.display_text("Processing\nyour purchase:\nChecking\n" + str(key))
								#self.bridge.display_text("Checking\n" + str(key) + "...")		
							
								#self.pe[self.articles[key]['pe_i2c_addr']].select_channel(self.articles[key]['mux_channel'])
								#self.pe[self.articles[key]['pe_i2c_addr']].enable()
								
								#weight_new = self.scales[key].getWeight(1)
								weight_new = self.get_weight(key)
								#print ("weight_new = " + str(weight_new))

								weight_loss = self.transactions[key]['weight_old'] - weight_new
								items_taken = round(weight_loss/self.articles[key]['weight'])
								stock_new = self.transactions[key]['stock_old'] - items_taken
								if (items_taken != 0):
									logging.info("Stock change on " + str(key) + ": " + "{:+2d}".format(-items_taken) + " (" + self.articles[key]['name'] + ")")  
									logging.info("New stock on " + str(key) + ": " + str(stock_new))  
								if (items_taken > 0):
									description = str(items_taken) + " x " + self.articles[key]['name'] + " á " + "{:.2f}".format(self.articles[key]['price'])
									price = items_taken * self.articles[key]['price']
								else:
									description = "n/a"
									price = 0.0
								#print("VOR UPDATE:")
								#pprint.pprint(self.transactions)		
								self.transactions[key].update( { 
													'weight_new'  : weight_new, 
													'stock_new'   : stock_new,
													'weight_loss' : weight_loss, 
													'items_taken' : items_taken, 
													'description' : description, 
													'price'       : price 
												   } )
								#print("NACH UPDATE:")
								#pprint.pprint(self.transactions)		
							
								if (items_taken < 0):
									self.bridge.send_email("Fabman Vending Machine: Stock Level Increased", "Article:<br>" + str(self.articles[key]) + "<br><br>Transaction Details:<br>" + str(self.transactions[key]))
								if (items_taken > 0 and self.transactions[key]['stock_new'] <= self.articles[key]['stock_min']):
									self.bridge.send_email("Fabman Vending Machine: Minimum Stock Level Reached", "Article:<br>" + str(self.articles[key]) + "<br><br>Transaction Details:<br>" + str(self.transactions[key]))
								
								#self.pe[self.articles[key]['pe_i2c_addr']].disable()
								
							#pprint.pprint(self.transactions)
							
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

							# beep and show summary
							self.bridge.buzzer.beep(n=1)
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
									logging.info("Vend sale posted successfully.")
									response = json.loads(response.content.decode('utf-8'))
									pprint.pprint(response)
								else:
									logging.error("Vend sale FAILED.")
									pprint.pprint(response)
							
							#input("\nPress Enter to continue...")			
							
							# (7) save new stock values for next transaction
							for key in self.articles:
								self.articles[key]['stock'] = self.transactions[key]['stock_new']
								
								weight_old = self.transactions[key]['weight_new']
								stock_old = self.transactions[key]['stock_new']
								self.transactions[key].update( 
																{ 
																	'weight_old' : weight_old,
																	'stock_old'  : stock_old
																} 
															 )
								'''
								self.transactions[key].update( { 
													'weight_new'  : weight_new, 
													'stock_new'   : stock_new,
													'weight_loss' : weight_loss, 
													'items_taken' : items_taken, 
													'description' : description, 
													'price'       : price 
												   } )
								'''
							self.save_articles()
							
						else:
							self.bridge.buzzer.beep(on_time=0.1, off_time=0.1, n=3, background=False)
							logging.info("Access denied.")
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

		
