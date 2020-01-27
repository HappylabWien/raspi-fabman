from raspifabman import FabmanBridge
import sys # because api token is read from command line

config = { # change default settings
	"api_url_base"       : "https://internal.fabman.io/api/v1/", # api url base / for production systems remove "internal."
	"heartbeat_interval" : 30
}

bridge = FabmanBridge(sys.argv[1], config)
bridge.run()
#bridge.read_key()