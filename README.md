# raspi-fabman

**This project is under development and not yet tested!!!**

## MicroPOS

MicroPOS is a simple point of sale solution for Fabman. All you need is a [RasPi 3](https://www.amazon.de/UCreate-Raspberry-Pi-Desktop-Starter/dp/B07BNPZVR7), a [display](https://www.amazon.de/AZDelivery-Display-Arduino-Raspberry-Gratis/dp/B078J78R45), a [barcode scanner](https://www.amazon.de/NETUM-Barcodescanner-Bar-code-USB-Kabel-USB-Anschluss/dp/B01M73VPXI), and a [card reader module](https://www.amazon.de/RFID-Arduino-deutscher-Anleitung-RFID-Schl%C3%BCsselanh%C3%A4nger/dp/B00L6Z14T4).

The sales process is then very simple and intuitive:
1. Scan the items you want
2. Swipe a member card to complete the sale
3. An invoice line is then automatically created for the member.

The article list with the prices are saved in a CSV file. An unique number is assigned to each article, which can then be printed out as a barcode. Here's an example for `articles.csv` (columns: id for barcode, article name, article price):
```
1234567,Schraube,1.00
7654321,Plexiglas,2.00
1111111,Fräser,3.00
```
