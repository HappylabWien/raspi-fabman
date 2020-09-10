# raspi-fabman

**This project is under development and not yet tested!!!**

## MicroPOS

MicroPOS is a simple point of sale solution for Fabman. All you need is 
- a [RasPi 3 B+](https://www.amazon.de/UCreate-Raspberry-Pi-Desktop-Starter/dp/B07BNPZVR7), 
- a [display](https://www.amazon.de/AZDelivery-Display-Arduino-Raspberry-Gratis/dp/B078J78R45), 
- a [barcode scanner](https://www.amazon.de/NETUM-Barcodescanner-Bar-code-USB-Kabel-USB-Anschluss/dp/B01M73VPXI), 
- a [card reader module](https://www.amazon.de/RFID-Arduino-deutscher-Anleitung-RFID-Schl%C3%BCsselanh%C3%A4nger/dp/B00L6Z14T4), and
- some [jumper wires (female to female)](https://www.amazon.de/AZDelivery-Jumper-Arduino-Raspberry-Breadboard/dp/B07KYHBVR7)

The sales process is then very simple and intuitive:
1. Scan the items you want
2. Swipe a member card to complete the sale
3. An invoice line is then automatically created for the member.

The article list with the prices are saved in a CSV file. An unique number is assigned to each article, which can then be printed out as a barcode. Here's an example for `/home/pi/raspi-fabman/articles.csv` (columns: id for barcode, article name, article price):
```
1234567,Schraube,1.00
7654321,Plexiglas,2.00
1111111,Fräser,3.00
```

Configure your fabman settings in `/home/pi/raspi-fabman/fabman.json`:
```
{
	"api_url_base"       : "https://fabman.io/api/v1/",
	"reader_type"        : "MFRC522",
	"display"            : "sh1106",
	"api_token"          : "XXXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXX"
}
```
You just need to set the `api_token`.

Connect the barcode scanner to a USB port of the Raspberry Pi and install the display and the card reader according to the wiring plan below. **Attention: There are two versions of the OLED display with different pinouts. On some the pins VCC and GND can also be positioned in reverse order. Please take this into account when wiring!**

<img src="https://github.com/HappylabWien/raspi-fabman/blob/master/MicroPosWiring.PNG" height="800" />

To start the program login via ssh on `raspi-fabman.local` (username `pi`, password `raspberry`) and run:
```
cd /home/pi/raspi-fabman
python3 micropos.py
```
If you like to start MicroPOS automatically during the boot process of the Raspberry Pi add the following line to `/etc/rc.local` *before* the line `exit 0`:
```
runuser -l pi -c "cd /home/pi/raspi-fabman;/usr/bin/python3 /home/pi/raspi-fabman/micropos.py >> /home/pi/raspi-fabman/log/micropos.log 2>&1 &"
```
