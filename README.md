# Eggcess - keeps chickens safe

This is a fun, useful and educative project that combines mechanical design,
3D printing, electronics and embedded programming.

This is not "just another" chicken coop door opener. In fact, this is a 4th iteration
that I've built, focusing on *reliability* ... and a good reason to play with Micropython.

**Features**

* sensorless operation - no risk of sensor malfunction
* safe torque - no risk of breaking something if software malfunctions
* stand-alone operation - can go without wifi connection for a long time
* auto-recovery - automatic recalibration if power was lost during movement
* MQTT interface - connect to anything
* compact electronics, can be built without soldering, just use jumper wires.

## Bill of materials

* [Seed Studio XIAO - ESP32-S3](https://www.tinytronics.nl/shop/nl/development-boards/microcontroller-boards/met-wi-fi/seeed-studio-xiao-esp32-s3) - 9 €
* 2x 608ZZ ball bearing - 2x 1 €
* [BYJ48 stepper + ULN2003 driver](https://www.tinytronics.nl/shop/nl/mechanica-en-actuatoren/motoren/stappenmotoren/stappen-motor-met-uln2003-motoraansturing) - 4 €

Total of just 15 euro!



## Mechanics

![](img/eggcess_mechanics.png)

Mechanical design is available on

* [onshape](https://cad.onshape.com/documents/9d1e9d13503836a93d923c99/w/cf41e9abcfc58e38551d4ef1/e/91ab2b97868868ebff4768e5?renderMode=0&uiState=6590590c9a15484af8e68a46)
* `stl` folder contains ready-to-print files.
