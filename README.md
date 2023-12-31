# Eggcess - chicken coop door for nerds

This is a fun, useful and educative project that combines mechanical design,
3D printing, electronics, IOT technologies and embedded programming.

This is not "just another" chicken coop door opener. In fact, this is a 4th generation
that I've built, with the main goal to improve *reliability* ... and a good reason to play with Micropython and learn something new.

**Features**

* sensorless operation - no risk of sensor malfunction
* safe torque - no risk of breaking something if software malfunctions
* stand-alone operation - can go without wifi connection for a long time
* auto-recovery - automatic recalibration if power was lost during movement
* MQTT interface - connect to anything
* logging saved to non-volatile memory
* web server,
* compact electronics, can be built without soldering, just use jumper wires.

## Bill of materials

* [Seed Studio XIAO - ESP32-S3](https://www.tinytronics.nl/shop/nl/development-boards/microcontroller-boards/met-wi-fi/seeed-studio-xiao-esp32-s3) - 9 €
* 2x 608ZZ ball bearing - 2x 1 €
* [BYJ48 stepper + ULN2003 driver](https://www.tinytronics.nl/shop/nl/mechanica-en-actuatoren/motoren/stappenmotoren/stappen-motor-met-uln2003-motoraansturing) - 4 €

Total of just 15 euro!

## Quick start

1. Start up VSCode devcontainer. The `Dockerfile` contains all the development goodies,
like micropython stubs. You may need to set `AMPY_PORT` in `devcontainer.json`
2. generate lookup table for open and close times using `calculations/calculate_lut.ipynb`
3. create `src/my_secrets.py` (see example file) and set correct ssid, password etc.
4. use `invoke` to upload code to the device. (`invoke upload-src`)

## Homeassistant integration

Install `mqtt` integration.

modify `mqtt` section in `configuration.yaml`:

```yaml
mqtt:
  switch:
      - unique_id: eggcess
        name: "eggcess"
        state_topic: "/eggcess/state"
        command_topic: "/eggcess/cmd"
        payload_on: "open"
        payload_off: "close"
        state_on: "open"
        state_off: "closed"
        retain: false

```


## Mechanics

![](img/eggcess_mechanics.png)

Mechanical design is available on

* [onshape](https://cad.onshape.com/documents/9d1e9d13503836a93d923c99/w/cf41e9abcfc58e38551d4ef1/e/91ab2b97868868ebff4768e5?renderMode=0&uiState=6590590c9a15484af8e68a46)
* `stl` folder contains ready-to-print files.
