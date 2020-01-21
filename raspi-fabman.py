import requests, json, time, datetime, threading

class FabmanBridge(object):

	def __init__(self, api_token, api_url_base = "https://fabman.io/api/v1/", heartbeat_interval = 30):
		self.api_token = api_token
		self.api_url_base = api_url_base
		self.heartbeat_interval = heartbeat_interval
		self.api_header = {'Content-Type': 'application/json','Authorization': 'Bearer {0}'.format(api_token)}
		self.user_name = None
		self.session_id = None
		self.next_heartbeat_call = time.time()
		if (self.heartbeat_interval > 0):
			self.__start_heartbeat_thread()

	def start(self,user_name):
		try:
			self.user_name = user_name
			api_url = '{0}bridge/access'.format(self.api_url_base)
			data = {'emailAddress': user_name, 'configVersion': 0}
			response = requests.post(api_url, headers=self.api_header, json=data)
			if (response.status_code == 200 and json.loads(response.content.decode('utf-8'))['type'] == "allowed"):
				print('Bridge started successfully.')
				self.session_id = json.loads(response.content.decode('utf-8'))["sessionId"]
				return True
			else:
				print('Bridge could not be started.')
				return False
		except Exception as e: 
			print ('Function FabmanBridge.start raised exception (' + str(e) + ')')
			return False
	
	def stop(self):
		try:
			api_url = '{0}bridge/stop'.format(self.api_url_base)
			data = { "stopType": "normal", "currentSession": { "id": self.session_id } }
			response = requests.post(api_url, headers=self.api_header, json=data)
			if response.status_code == 200 or response.status_code == 204:
				self.user_name = None
				self.session_id = None
				print('Bridge stopped successfully.')
				return True
			else:
				print('Bridge could not be stopped.')
				return False			
		except Exception as e: 
			print ('Function FabmanBridge.stop raised exception (' + str(e) + ')')
			return False

	def heartbeat(self):
		try:
			api_url = '{0}bridge/heartbeat'.format(self.api_url_base)
			data = { 'configVersion': 0 }
			response = requests.post(api_url, headers=self.api_header, json=data)
			if response.status_code == 200:
				response = json.loads(response.content.decode('utf-8'))
				print("Heartbeat")
				return True
			else:
				return False
		except Exception as e: 
			logging.error('Function FabmanBridge.heartbeat raised exception (' + str(e) + ')')
			return False

	def __start_heartbeat_thread(self):
		print datetime.datetime.now()
		self.heartbeat()
		self.next_heartbeat_call += self.heartbeat_interval
		threading.Timer( self.next_heartbeat_call - time.time(), self.__start_heartbeat_thread ).start()



machine = FabmanBridge("710ce79f-684b-40d1-a4e3-0c6e5657d910","https://internal.fabman.io/api/v1/", 10);


#machine.start("roland@fabman.io")
#print machine.session_id
#time.sleep(10)
#machine.stop()
#print machine.session_id
