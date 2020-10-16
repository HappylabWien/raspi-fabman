# raspi-fabman

**This project is under development and not yet tested!!! Use it at your own risk.**

[Fabman](https://fabman.io) is an all-in-one makerspace management solution. It is the "operating system" for makerspaces, fab labs, coworking spaces or school workshops. It helps to manage machines and members easily, safely & efficiently. `raspi-faman` is an open source library written in python3, with the help of which you can build your own [Fabman](https://fabman.io)-compatible hardware. 

Specific use cases are described in detail below:
- [RasPi Bridge](https://github.com/HappylabWien/raspi-fabman/blob/master/README.md#raspi-bridge): Open source alternative to the [Fabman Bridge](https://shop.fabman.io/products/fabman-bridge-v2), primarily intended as a basis for customer-specific hardware integrations that cannot be covered with the standard Fabman Bridge.
- [MicroPOS](https://github.com/HappylabWien/raspi-fabman/blob/master/README.md#micropos): Point of sale solution for Fabman
- [Vending Machine](https://github.com/HappylabWien/raspi-fabman/blob/master/README.md#vending-machine): Vending machine to sell consumables which charges automatically via Fabman
- *...more use cases coming soon...*

We will gradually expand the list and we look forward to your feedback.

## Software Installation

All of the above use cases are based on this library running on a [RasPi 3 B+](https://www.amazon.de/UCreate-Raspberry-Pi-Desktop-Starter/dp/B07BNPZVR7). The first thing to do is to install the library on your Raspberry Pi as follows.

### Install Image File

You can [download this image (zip-file, ca. 1.3 GB)](https://drive.google.com/file/d/11m_erBqufvHFaryymkIm5_6_yDtTD6Tx/view?usp=sharing), unzip it and install it on your SD card (min. size 8 GB). We suggest to use the [Raspberry Pi Imager](https://www.raspberrypi.org/downloads/) for this purpose.

1. [Download](https://www.raspberrypi.org/downloads/), install and start the Rapberry Pi Imager
2. Insert a Micro SD card into the card reader on your Computer
3. Select "CHOOSE OS" -> "Use Custom" and select the .img-File you have just downloaded and unzipped (`MicroPOS-<date>.img`)
4. Select "CHOOSE SD CARD" and select the card you have inserted before
5. Select "WRITE" to write the image to your Micro SD card. This will take several minutes.

### Configure WiFi

*Before* you insert the Micro SD card into your Raspberry Pi you need to configure your WiFi settings. In the /boot/ directory, open `wpa_supplicant.conf` and enter your Wifi parameters (ssid and password):
```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=<Insert 2 letter ISO 3166-1 country code here>

network={
 ssid="<Name of your wireless LAN>"
 psk="<Password for your wireless LAN>"
}
```
*Attention: Depending on the OS and editor you are creating this on, the file could have incorrect newlines or the wrong file extension so make sure you use an editor that accounts for this. On Windows we suggest to use [Notepad++](https://notepad-plus-plus.org/).*

If needed, you find more detailed istructions [here](https://www.raspberrypi.org/documentation/configuration/wireless/headless.md). 

When you have done this, insert the SD card into the Raspberry and power it on. It will now automatically connect to your WiFi and receive an IP address from your DHCP server. 

You can login via ssh on `raspi-fabman.local` with username `pi` and password `raspberry`.
For security reasons you are strongly advised to change the password of the default user on your Raspberry Pi according to this [Howto](https://www.theurbanpenguin.com/raspberry-pi-changing-the-default-users-password-and-creating-addtional-accounts/).

### Update raspi-fabman Library

Get the latest version of the `raspi-fabman` library:
- Login to your Raspberry Pi via ssh (user pi)
- go to the fabman directory: `cd /home/pi/raspi-fabman`
- get newest version: `git pull origin master`

Now continue with the instructions for the specific use case you want to implement: go to section [RasPi Bridge](https://github.com/HappylabWien/raspi-fabman/blob/master/README.md#raspi-bridge), [MicroPOS](https://github.com/HappylabWien/raspi-fabman/blob/master/README.md#micropos), or [Vending Machine](https://github.com/HappylabWien/raspi-fabman/blob/master/README.md#vending-machine)

## RasPi Bridge

RasPi Bridge is an open source alternative to the Fabman Bridge. It currently only offers the essential basic functions of a Fabman Bridge (checking authorizations, switching a device on / off). The source code can, however, be adapted and expanded as required. The RasPi Bridge is primarily intended as a basis for customer-specific hardware integrations that cannot be covered with the standard Fabman Bridge.

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/RasPiBridge.jpg" height="400" />

Functionality:
1. Swipe member card
2. If access is granted, the relay is switched on
3. Press the button to switch off

### Hardware Setup

#### Bill of Materials

All you need is 
- a [RasPi 3 B+](https://www.amazon.de/UCreate-Raspberry-Pi-Desktop-Starter/dp/B07BNPZVR7), 
- a [display](https://www.amazon.de/AZDelivery-Display-Arduino-Raspberry-Gratis/dp/B078J78R45), 
- a [push button](https://www.amazon.de/dp/B08CDJY57F) (basic soldering skills required to solder jumper wires to the contact pins of the push button), 
- a [card reader module](https://www.amazon.de/RFID-Arduino-deutscher-Anleitung-RFID-Schl%C3%BCsselanh%C3%A4nger/dp/B00L6Z14T4),
- a [relay module](https://www.amazon.de/AZDelivery-1-Relais-KY-019-High-Level-Trigger-Arduino/dp/B07TYG14N6) to switch your equipment on/off, and
- some [jumper wires (female to female)](https://www.amazon.de/AZDelivery-Jumper-Arduino-Raspberry-Breadboard/dp/B07KYHBVR7)

#### Wiring

Install display, card reader, relay, and stop button according to the wiring plan below. **Attention: There are two versions of the OLED display with different pinouts. On some the pins VCC and GND can also be positioned in reverse order. Please take this into account when wiring!**

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/RasPiBridgeWiring.PNG" height="800" />

#### Enclosure

3D-printed enclosure:
- STL-Files: [bottom](https://github.com/HappylabWien/raspi-fabman/blob/master/RasPiBridgeEnclosureBottom.stl) and [cover](https://github.com/HappylabWien/raspi-fabman/blob/master/RasPiBridgeEnclosureCover.stl)
- [Matching Screws](https://minischrauben.com/blech-holzschrauben-bund-linsenkopf--46209.html) (20x)

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/RasPiBridge_inside.jpg" height="600" />

### Configuration

Before you can start with the configuration, the library must be available on your Raspberry Pi. If you have not already done so, please follow the steps in the section [Software Installation](https://github.com/HappylabWien/raspi-fabman#software-installation) before continuing.

#### Connect to Fabman

[Create a Fabman Bridge API key](https://help.fabman.io/article/32-create-a-bridge-api-key) for your corresponding equipment in Fabman. If it doesn’t yet exist, create a new equipment in Fabman first and then create an API key for it. 

Login to the Raspberry Pi (`raspi-fabman.local`) via ssh and configure your fabman settings in `/home/pi/raspi-fabman/fabman.json`:
```
{
	"api_url_base"       : "https://fabman.io/api/v1/",
	"reader_type"        : "MFRC522",
	"display"            : "sh1106",
	"api_token"          : "XXXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXX",
	"left_button"        : 24,
	"relay"              : 26
}
```
You just need to set the `api_token` created before.

### Run RasPi Bridge

To start the program run:
```
cd /home/pi/raspi-fabman
python3 bridge.py
```

If you like to start MicroPOS automatically during the boot process of the Raspberry Pi add the following line to `/etc/rc.local` *before* the line `exit 0`:
```
runuser -l pi -c "cd /home/pi/raspi-fabman;/usr/bin/python3 /home/pi/raspi-fabman/bridge.py >> /home/pi/raspi-fabman/log/bridge.log 2>&1 &"
```

### Add Custom Features to RasPi Bridge

Use the following `/home/pi/raspi-fabman/bridge.py` as basis for further development:

```python
#!/usr/bin/python3

'''
Minimal Example for Fabman Bridge:
* Switch on with member card
* A relay is switched on, when access is granted
* Switch off by pressing a button
'''

import RPi.GPIO as GPIO
import time, logging, pprint
from raspifabman import FabmanBridge, Fabman

bridge = FabmanBridge(config_file="bridge.json")

# Handle stop button
def callback_left_button(channel):
	if (bridge.is_on()):
		logging.debug("Switching off")
		bridge.stop()
		bridge.relay.off()
GPIO.add_event_detect(bridge.config["left_button"], GPIO.FALLING, callback=callback_left_button, bouncetime=300)

# Run bridge
logging.info("Bridge started")
while (True):
	if (bridge.is_off()):		
		bridge.display_text("Show card to start")
		logging.debug("Waiting for key")
		key = bridge.read_key()
		if (key != False and key is not None):
			if (bridge.access(key)):
				bridge.display_text("Access granted\n\n\n<-STOP")
				logging.debug("Switching on")
				bridge.relay.on()
			else:
				bridge.display_text("Access denied",3)
				logging.debug("Access denied")
```

## MicroPOS

MicroPOS is a simple point of sale solution for Fabman based on a Raspberry Pi. 

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/MicroPOS.jpg" height="400" />

The sales process is then very simple and intuitive:
1. Scan the items you want
2. Swipe a member card to complete the sale
3. An invoice line is then automatically created for the member.

### Hardware Setup

#### Bill of Materials

All you need is 
- a [RasPi 3 B+](https://www.amazon.de/UCreate-Raspberry-Pi-Desktop-Starter/dp/B07BNPZVR7), 
- a [display](https://www.amazon.de/AZDelivery-Display-Arduino-Raspberry-Gratis/dp/B078J78R45), 
- a [barcode scanner](https://www.amazon.de/NETUM-Barcodescanner-Bar-code-USB-Kabel-USB-Anschluss/dp/B01M73VPXI), 
- a [card reader module](https://www.amazon.de/RFID-Arduino-deutscher-Anleitung-RFID-Schl%C3%BCsselanh%C3%A4nger/dp/B00L6Z14T4), and
- some [jumper wires (female to female)](https://www.amazon.de/AZDelivery-Jumper-Arduino-Raspberry-Breadboard/dp/B07KYHBVR7)

#### Wiring

Connect the barcode scanner to a USB port of the Raspberry Pi and install the display and the card reader according to the wiring plan below. **Attention: There are two versions of the OLED display with different pinouts. On some the pins VCC and GND can also be positioned in reverse order. Please take this into account when wiring!**

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/MicroPosWiring.PNG" height="800" />

#### Enclosure

3D-printed enclosure:
- STL-Files: [bottom](https://github.com/HappylabWien/raspi-fabman/blob/master/MicroPosEnclosureBottom.stl) and [cover](https://github.com/HappylabWien/raspi-fabman/blob/master/MicroPosEnclosureCover.stl)
- [Matching Screws](https://minischrauben.com/blech-holzschrauben-bund-linsenkopf--46209.html) (16x)
- [Barcode label for Reset an Undo](https://github.com/HappylabWien/raspi-fabman/blob/master/barcodes_RESET_UNDO.pdf)
   - Scan RESET to cancel current sale
   - Scan UNDO to remove the last item you scanned from the cart

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/MicroPOS_inside.jpg" height="600" />

### Configuration

Before you can start with the configuration, the library must be available on your Raspberry Pi. If you have not already done so, please follow the steps in the section [Software Installation](https://github.com/HappylabWien/raspi-fabman#software-installation) before continuing.

#### Connect to Fabman

[Create a Fabman Bridge API key](https://help.fabman.io/article/32-create-a-bridge-api-key) for your MicroPOS equipment in Fabman. If it doesn’t yet exist, create a new equipment in Fabman first and then create an API key for it. 

Login to the Raspberry Pi (`raspi-fabman.local`) via ssh and configure your fabman settings in `/home/pi/raspi-fabman/fabman.json`:
```
{
	"api_url_base"       : "https://fabman.io/api/v1/",
	"reader_type"        : "MFRC522",
	"display"            : "sh1106",
	"api_token"          : "XXXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXX"
}
```
You just need to set the `api_token` created before.

#### Articles Database

The article list with the prices are saved in a CSV file. An unique number is assigned to each article, which can then be printed out as a barcode. Here's an example for `/home/pi/raspi-fabman/articles.csv` (columns: id for barcode, article name, article price):
```
1234567,Plywood,1.00
7654321,Screw,2.00
1111111,Endmill,3.00
```

### Run MicroPOS

To start the program run:
```
cd /home/pi/raspi-fabman
python3 micropos.py
```

If you like to start MicroPOS automatically during the boot process of the Raspberry Pi add the following line to `/etc/rc.local` *before* the line `exit 0`:
```
runuser -l pi -c "cd /home/pi/raspi-fabman;/usr/bin/python3 /home/pi/raspi-fabman/micropos.py >> /home/pi/raspi-fabman/log/micropos.log 2>&1 &"
```

## Vending Machine

We are currently working on an open source extension for Fabman for material sales. In principle, it is a cabinet with many scales inside. The products are placed on the scales.

The use case then looks like this for the members:
1. Open the cabinet using a chip card
2. Remove the required items
3. Close the cabinet door
3. Weighing is done before and after the transaction. The system therefore knows who has withdrawn how many of which articles. Charges are then automatically generated in Fabman for the articles.

The system is currently being tested at [Happylab](https://www.happylab.at) in Vienna. As soon as I find the time, I'll document it here. Thank you for your patience!

## Hardware Options

### 125kHz EM4100 RFID Support

If you want to support 125kHz EM4100 RFID chips instead of NFC you need to replace the MFRC522 reader by the [Gwiot7941E reader](https://www.amazon.de/gp/product/B082FYKD4B). The library doesn't support to run both readers at the same time. Wire the 

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/Gwiot7941E.jpg" height="400" />

Set the parameter `reader_type` in `/home/pi/raspi-fabman/fabman.json` to `Gwiot7941E` (instead of `MFRC522`). Use the supplied cable to connect the module to the Raspberry PI. In order to be able to connect the cable to the pin headers of the Raspberry Pi, you have to solder suitable sockets to the open ends of the cable.

| Pin on 7941E | Color |  Pin on RasPi   |
|:------------:|:-----:|:---------------:|
| 5V           | red   | Pin 4 - 5V      |
| TXD          | green | Pin 10 - GPIO15 |
| GND          | black | Pin 6 - GND     |

