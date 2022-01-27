import evdev
from evdev import InputDevice, categorize, ecodes  
import csv
import time
import pprint
import RPi.GPIO as GPIO
import threading
import sys

from vendingmachine import Vend

class MicroPOS(object): 

    def __init__(self, bridge, input_device = '/dev/input/event0', inventory_file = 'articles.csv', reset_code = 'RESET', undo_code = 'UNDO', timeout = 30, currency = "EUR", pin_reset_button = None, pin_undo_button = None, vend = None):

        # setup scanner
        self.scanner = InputDevice(input_device)
        self.scanner.grab() # grab provides exclusive access to the device
        
        self.bridge = bridge
        self.bridge.display_text("Initializing\nDatabase.\n\nPlease wait...")
        
        self.inventory = {}
        
        # read invetory from vend via api and add to products list
        if (vend is not None): 
            self.inventory = vend.get_products()

        # read inventory file and add to products list (default: articles.json)
        with open(inventory_file) as fin:
            #reader=csv.reader(fin, quotechar='"', skipinitialspace=True)
            reader=csv.reader(fin, quotechar='"', delimiter='\t', skipinitialspace=True)
            for row in reader:
                self.inventory[row[0]]=row[1:]
            
        print (str(len(self.inventory)) + " products loaded.")
        
        self.barcode = None
        self.sale_products = {}	
        self.reset_code = reset_code
        self.undo_code = undo_code
        self.timeout = timeout # reset sale if no barcode scanned for x seconds
        self.t_timeout = threading.Timer(self.timeout, thread_timeout) # thread for timeout
        self.currency = currency
        
        self.charge = { 'description' : "n/a", 'price' : 0.0 }
        self.metadata = {}
        
        self.lock_scanner = True # disable scanner during startup screens
        #self.bridge.display_text("Welcome to\nMicroPOS\nfor Fabman")
        #time.sleep(3)
        self.update_display()
        self.lock_scanner = False # enable scaner
        
        self.pin_reset_button = pin_reset_button
        if (pin_reset_button is not None):
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin_reset_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin_reset_button, GPIO.FALLING, callback=self._callback_reset_button, bouncetime=300)

        self.pin_undo_button = pin_undo_button
        if (pin_undo_button is not None):
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin_undo_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin_undo_button, GPIO.FALLING, callback=self._callback_undo_button, bouncetime=300)
        
        self.vend = vend

    def del__(self):
        #self.bridge.display_text("Goodbye!")
        #time.sleep(2)
        #self.bridge.display_text("")
        self.scanner.close()
        
    def read_barcode(self):

        # Provided as an example taken from my own keyboard attached to a Centos 6 box:
        scancodes = {
            # Scancode: ASCIICode
            0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
            10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'q', 17: u'w', 18: u'e', 19: u'r',
            20: u't', 21: u'y', 22: u'u', 23: u'i', 24: u'o', 25: u'p', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
            30: u'a', 31: u's', 32: u'd', 33: u'f', 34: u'g', 35: u'h', 36: u'j', 37: u'k', 38: u'l', 39: u';',
            40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'z', 45: u'x', 46: u'c', 47: u'v', 48: u'b', 49: u'n',
            50: u'm', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 57: u' ', 100: u'RALT'
        }

        capscodes = {
            0: None, 1: u'ESC', 2: u'!', 3: u'@', 4: u'#', 5: u'$', 6: u'%', 7: u'^', 8: u'&', 9: u'*',
            10: u'(', 11: u')', 12: u'_', 13: u'+', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
            20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'{', 27: u'}', 28: u'CRLF', 29: u'LCTRL',
            30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u':',
            40: u'\'', 41: u'~', 42: u'LSHFT', 43: u'|', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
            50: u'M', 51: u'<', 52: u'>', 53: u'?', 54: u'RSHFT', 56: u'LALT',  57: u' ', 100: u'RALT'
        }
        #setup vars
        x = ''
        caps = False

        # grab provides exclusive access to the device
        #self.scanner.grab()

        #loop
        for event in self.scanner.read_loop():
            if event.type == ecodes.EV_KEY:
                data = categorize(event)  # Save the event temporarily to introspect it
                if data.scancode == 42:
                    if data.keystate == 1:
                        caps = True
                    if data.keystate == 0:
                        caps = False
                if data.keystate == 1:  # Down events only
                    if caps:
                        key_lookup = u'{}'.format(capscodes.get(data.scancode)) or u'UNKNOWN:[{}]'.format(data.scancode)  # Lookup or return UNKNOWN:XX
                    else:
                        key_lookup = u'{}'.format(scancodes.get(data.scancode)) or u'UNKNOWN:[{}]'.format(data.scancode)  # Lookup or return UNKNOWN:XX
                    if (data.scancode != 42) and (data.scancode != 28):
                        if (str(key_lookup) != "None"):
                            x += key_lookup  
                            #print ("ADD KEY_LOOKUP: " + str(key_lookup) + "\n")
                    if(data.scancode == 28):
                        if (self.lock_scanner == True):
                            # discard barcodes while sale is processed (after swiping key card)
                            #print ("DISCARD BARCODES WHILE LOCKED")
                            #self.barcode = None
                            return(None)
                        else:
                            #print ("NOT LOCKED")
                            #self.barcode = x
                            return(x)

    def get_description(self, barcode = None):
        if (barcode is None):
            barcode = self.barcode
        if (barcode in self.inventory):
            return self.inventory[barcode][0]
        else:
            print("Barcode " + str(barcode) + " not found in inventory")
            return ""
           
    def get_price(self, barcode = None):
        if (barcode is None):
            barcode = self.barcode
        if barcode in self.inventory:
            return float(self.inventory[barcode][1])
        else:
            print("Barcode " + str(barcode) + " not found in inventory")
            return False

    def get_vend_id(self, barcode = None):
        if (barcode is None):
            barcode = self.barcode
        if (barcode in self.inventory):
            try:
                return self.inventory[barcode][2]
            except IndexError:
                print("No vend-id available for article " + str(barcode))
                return None
        else:
            print("Barcode " + str(barcode) + " not found in inventory")
            return None
    
    def reset_sale(self): 
        self.sale_products = {}
        self.barcode = None

    def add_product_to_sale(self, barcode = None):
        if (barcode is None):
            barcode = self.barcode
        if (barcode in self.sale_products):
            self.sale_products[barcode]['quantity'] += 1
        else:
            self.sale_products[barcode] = {'description' : self.get_description(barcode), 'price' : self.get_price(barcode), 'quantity' : 1, 'vend_id' : self.get_vend_id(barcode)}
    
    def undo(self):
        if (self.barcode is not None):			
            print("Undo " + str(self.barcode))
            
            print("VORHER:")
            pprint.pprint(self.sale_products)

            # adjust cart
            if (self.sale_products[self.barcode]['quantity'] == 1):
                del self.sale_products[self.barcode]
                print ("delete sales entry " + str(self.barcode))
            else:
                self.sale_products[self.barcode]['quantity'] -= 1
                print ("decrement amount of " + str(self.barcode))
            print("NACHHER:")
            pprint.pprint(self.sale_products)

            # display info
            line1 = "1x " + self.get_description(self.barcode)
            line2 = "removed from cart"
            if (self.get_number_if_items() == 0): # empty shopping cart
                line3 = "Scan barcode"
                line4 = "to start shopping"
            else:
                line3 = str(self.get_number_if_items()) + " item(s) in cart"
                line4 = "TOTAL: " + "{:.2f}".format(self.get_total()) + " " + self.currency

            #print(line1)
            #print(line2)
            #print(line3)
            #print(line4)
            
            self.bridge.display_text(line1 + "\n" + line2 + "\n" + line3 + "\n" + line4)

            self.barcode = None
            
            #time.sleep(3)
            #self.update_display()

        else:
            print("Nothing to be undone")
            self.bridge.display_text("Undo not possible")
            time.sleep(3)
            self.update_display()
            
    def get_total(self):
        total = 0
        for barcode in self.sale_products:
            if 'stock_min' not in self.sale_products[barcode]:
                total += self.sale_products[barcode]['quantity'] * self.sale_products[barcode]['price']
        return total
        
    def get_number_if_items(self):
        total = 0
        for barcode in self.sale_products:
            if 'stock_min' not in self.sale_products[barcode]:
                total += self.sale_products[barcode]['quantity']
        return total

    def close_sale(self, note="MicroPOS"): # sells all products prevously added with add_product_to_sale	
        first_item = True
        description = "n/a"
        price = 0.0
        for barcode in self.sale_products:
            if (first_item):
                description = str(self.sale_products[barcode]['quantity']) + " x " + self.sale_products[barcode]['description'] + " á € " + "{:.2f}".format(self.sale_products[barcode]['price'])
                first_item = False
            else:
                description += " and " + str(self.sale_products[barcode]['quantity']) + " x " + self.sale_products[barcode]['description'] + " á € " + "{:.2f}".format(self.sale_products[barcode]['price'])
            #price += self.sale_products[barcode]['quantity'] * self.sale_products[barcode]['price']
        # create charge in fabman
        self.charge = { 'description' : description, 'price' : self.get_total() }
        self.metadata = {
                    'articles'     : self.sale_products,
                    'charge'       : self.charge
                   }
        #print ("----------------")
        #pprint.pprint (self.metadata)
        #print ("----------------")
        
        if (self.vend is not None):
            #pprint.pprint("CLOSE SALE IN VEND - NOT TESTED YET")
            
            # create charge in vend
            
            #for barcode in self.sale_products:
            #    pprint.pprint("XXX " + str(self.sale_products[barcode]['quantity']) + " x " + self.sale_products[barcode]['description'] + " á € " + "{:.2f}".format(self.sale_products[barcode]['price']) + "(vend_id: " + str(self.sale_products[barcode]['vend_id']) + ")")

            self.vend.start_sale()
            tax_percent = self.vend.config['tax_percent']
            for barcode in self.sale_products:
                if (self.sale_products[barcode]['quantity'] > 0):
                    self.vend.add_product_to_sale(self.sale_products[barcode]['vend_id'], self.sale_products[barcode]['quantity'], self.sale_products[barcode]['price']/(100+tax_percent)*100, self.sale_products[barcode]['price']/(100+tax_percent)*tax_percent)
            if (self.vend.close_sale(note=note) == False):
                print ("VEND SALE FAILED")
            
            #print ("VEND WARENKORB:")
            #pprint.pprint(self.vend.register_sale_products)
        
        self.reset_sale()
        
    def update_display(self):
        #pprint.pprint(self.sale_products)
        #print("LEN = " + str(len(self.sale_products)))
        if (self.get_number_if_items() == 0): # empty shopping cart
            #pos.bridge.display_text("Scan barcode\nto start\nshopping")
            line1 = "Scan barcode"
            line2 = "to start shopping"
            line3 = str(self.get_number_if_items()) + " item(s) in cart"
            line4 = "TOTAL: " + "{:.2f}".format(self.get_total()) + " " + self.currency
            self.bridge.display_text(line1 + "\n" + line2 + "\n" + line3 + "\n" + line4)
        else: # there are articles in the shopping cart
            line1 = self.get_description()
            if (self.get_price() is False):
                line2 = ""
            else:
                line2 = "for {:.2f}".format(self.get_price()) + " " + self.currency + " added"
            line3 = str(self.get_number_if_items()) + " item(s) in cart"
            line4 = "TOTAL: " + "{:.2f}".format(self.get_total()) + " " + self.currency
            self.bridge.display_text(line1 + "\n" + line2 + "\n" + line3 + "\n" + line4)

    def _callback_reset_button(self, channel):
        print("reset button pressed")
        self.reset_sale()
        self.update_display()
            
    def _callback_undo_button(self, channel):
        print("undo button pressed")
        self.undo()
        #self.update_display()
            
if __name__ == '__main__':

    from raspifabman import FabmanBridge, Fabman
    #import threading
    
    
    
    def thread_read_key():
        print("Thread read_key starting", )
        while True:

            if (pos.bridge.is_off() and pos.get_number_if_items() > 0):
                print("thread_read_key: Thread read_key is ready to read key from " + str(pos.bridge.config['reader_type']))
                key = pos.bridge.read_key()
                print("thread_read_key: Key detected: " + str(key))
                if (key != False and key is not None): # key detected (no "ghost key")
                    print("thread_read_key: Key is no ghost key")
                    print("thread_read_key: Locking barcode scanner")
                    pos.lock_scanner = True
                    #print("Key detected: " + str(key))
                    if (pos.bridge.access(key) is not False): # access granted
                        print("thread_read_key: Access granted")
                        pos.bridge.display_text("Processing\nsale...")
                        total = pos.get_total()
                        
                        
                        if (pos.bridge.config['reader_type'] == "Gwiot7941E"):
                            key_type = "em4102"
                            f = Fabman(api_token="b2a94e24-8358-4914-86da-8c81396c2ab0", api_url_base="https://internal.fabman.io/api/v1/")
                            f.get(api_endpoint='members', id=None, query_string='keyType=em4102&keyToken=' + str(key) + '&limit=1')
                            sale_note = "Customer: " + f.response[0]['firstName'] + " " + f.response[0]['lastName'] + " (" + f.response[0]['memberNumber'] + ")"
                            pos.close_sale(note=sale_note)                            
                        else:
                            pos.close_sale()
                        
                        print("thread_read_key: Cancel timeout countdown")
                        pos.t_timeout.cancel()
                        
                        #print("Metadata:")
                        #pprint.pprint(pos.metadata)
                        #print("Charge:")
                        pprint.pprint(pos.charge)
                        pos.bridge.stop(pos.metadata, pos.charge) 
                        pos.bridge.display_text("{:.2f}".format(total) + " " + pos.currency + " charged\n\nTHANK YOU!")
                    else: # access denied
                        print("thread_read_key: Access denied")					
                        print("thread_read_key: Restart timeout countdown: " + str(pos.timeout) + "s")
                        pos.t_timeout.cancel()
                        pos.t_timeout = threading.Timer(pos.timeout, thread_timeout)
                        pos.t_timeout.start()
                        
                        pos.bridge.display_text("ACCESS\nDENIED!")
                    time.sleep(3)
                    pos.update_display()
                    print("thread_read_key: Unlocking barcode scanner")
                    pos.lock_scanner = False
            else: # shopping cart is empty
                time.sleep(0.1)
        print("Thread read_key finishing")

    def thread_timeout():
        #print("Timeout thread starting", )
        print("timeout -> reset shopping cart")
        pos.lock_scanner = True
        pos.bridge.display_text("TIMEOUT\nResetting sale")
        time.sleep(3)
        pos.reset_sale()
        pos.update_display()
        pos.lock_scanner = False
        #print("Thread " + name + " finishing")
    
    #config = { # change default settings
    #    "api_url_base"       : "https://internal.fabman.io/api/v1/", # api url base / for production systems remove "internal."
    #    #"reader_type"        : "Gwiot7941E",
    #    "reader_type"        : "MFRC522",
    #    "api_token"          : "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    #}
    #bridge = FabmanBridge(config) # of no parameter is given, read config from "fabman.json"
    bridge = FabmanBridge() # of no parameter is given, read config from "fabman.json"
    pos = MicroPOS(bridge, timeout=30, pin_reset_button=4, pin_undo_button=None, vend=Vend())

    t_read_key = threading.Thread(target=thread_read_key, daemon=True)
    t_read_key.start()

    while True:
        barcode = pos.read_barcode()
        #print ("pos.undo_code = " + pos.undo_code + " / barcode = " + barcode)
        if (barcode is not None):
            if (barcode == pos.reset_code):
                print("*** RESET SALE ***")
                pos.reset_sale()	

                print("cancel timeout countdown")
                pos.t_timeout.cancel()
                
                pos.update_display()

            elif (barcode == pos.undo_code):
                pos.undo()
            
                print("restart timeout countdown: " + str(pos.timeout) + "s")
                pos.t_timeout.cancel()
                pos.t_timeout = threading.Timer(pos.timeout, thread_timeout)
                pos.t_timeout.start()
                
            elif (barcode in pos.inventory):
                pos.barcode = barcode
            
                print("Add article: " + str(pos.barcode))
                #print(pos.get_description())
                #print(pos.get_price())
                pos.add_product_to_sale()
                
                print("restart timeout countdown: " + str(pos.timeout) + "s")
                pos.t_timeout.cancel()
                pos.t_timeout = threading.Timer(pos.timeout, thread_timeout)
                pos.t_timeout.start()
                
                pos.update_display()

            else:
                pos.lock_scanner = True
                print("Unknown barcode: " + str(barcode))
                pos.bridge.display_text("Invalid barcode:\n" + str(barcode))
                time.sleep(3)
                pos.lock_scanner = False
                
                print("restart timeout countdown: " + str(pos.timeout) + "s")
                pos.t_timeout.cancel()
                pos.t_timeout = threading.Timer(pos.timeout, thread_timeout)
                pos.t_timeout.start()
                
                pos.update_display()
            #pprint.pprint(pos.sale_products)
            #print("TOTAL: " + str(pos.get_total()))
            

            
        #else:
        #	print("Barcode discarded through locking mechanisms")