# raspi-fabman

**This project is under development and not yet tested!!!**

## MicroPOS

MicroPOS is a simple point of sale solution for Fabman based on a Raspberry Pi. The sales process is then very simple and intuitive:
1. Scan the items you want
2. Swipe a member card to complete the sale
3. An invoice line is then automatically created for the member.

### Hardware Setup

All you need is 
- a [RasPi 3 B+](https://www.amazon.de/UCreate-Raspberry-Pi-Desktop-Starter/dp/B07BNPZVR7), 
- a [display](https://www.amazon.de/AZDelivery-Display-Arduino-Raspberry-Gratis/dp/B078J78R45), 
- a [barcode scanner](https://www.amazon.de/NETUM-Barcodescanner-Bar-code-USB-Kabel-USB-Anschluss/dp/B01M73VPXI), 
- a [card reader module](https://www.amazon.de/RFID-Arduino-deutscher-Anleitung-RFID-Schl%C3%BCsselanh%C3%A4nger/dp/B00L6Z14T4), and
- some [jumper wires (female to female)](https://www.amazon.de/AZDelivery-Jumper-Arduino-Raspberry-Breadboard/dp/B07KYHBVR7)

Connect the barcode scanner to a USB port of the Raspberry Pi and install the display and the card reader according to the wiring plan below. **Attention: There are two versions of the OLED display with different pinouts. On some the pins VCC and GND can also be positioned in reverse order. Please take this into account when wiring!**

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/MicroPosWiring.PNG" height="800" />

### Software Installation

You can download [this]() image (*coming soon*) and install it on your SD card. These [instructions](https://www.raspberrypi.org/documentation/installation/installing-images/) can be useful.

Prior to the first boot you need to set up the WiFi configuration. Therefore, follow these [instructions](https://www.raspberrypi.org/documentation/configuration/wireless/headless.md). When you have done this, insert the SD card into the Raspberry and power it on. It will now automatically connect to your WiFi and receive an IP address from your DHCP server. 

You can login via ssh on `raspi-fabman.local` with username `pi` and password `raspberry`.

For security reasons you are strongly advised to change the password of the default user on your Raspberry Pi according to this [Howto](https://www.theurbanpenguin.com/raspberry-pi-changing-the-default-users-password-and-creating-addtional-accounts/).

### Configuration

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

### 3D-Printed Enclosure ###

- STL-Files: *coming soon*
- [Matching Screws](https://minischrauben.com/blech-holzschrauben-bund-linsenkopf--46175.html)

*Photo coming soon*
