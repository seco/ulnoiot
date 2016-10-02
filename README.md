# micropython-extra-ulno
Ulno's (http://ulno.net) extensions to [micropython](http://www.micropython.org/)
enabling IoT classes and easy getting started using [micropython](http://www.micropython.org/).

The tools here make heavily use of [mpfshell](https://github.com/wendlers/mpfshell).

The tools allow an easy way to deploy the firmware and the small libraries supporting
the follwing shields:
- [devel](shields/devel/README.md): a shield with two leds and 3 buttons, pressing the right one when booting up, will
  delete the wifi configuration file and prevent the user_boot.py to be started
- [display](shields/display/README.md): supports using an i2c-based 128x64 LCD (ssd1306) on d5 and d2
- [ht](shields/ht/README.md): a shield emplying a DHT11 temperature and humidity sensor (connected to d1)
- [mpr121](shields/mpr121/README.md): this is a shield using the mpr121 multi touch and gpio chip over i2c
- [relay](shields/relay/README.md): supporting the default relay shield for the wemos d1 mini attached to d1

To setup wifi connect to the wireless network of the esp8266, when in access mode and use 
[webrepl](http://micropython.org/webrepl/) or your own local copy of it from https://github.com/micropython/webrepl.
Adapt [wifi_config.py](/examples/wifi_config.py) and copy it through webrepl. If you have mpfshell installed and run
Linux, you can also run the [setup script](bin/program_wifi).

If you create a user_boot.py file with your own context, this will be started automatically,
when the system boots.

To use interrupts and other advanced features, take a look at the
[micropython reference](https://docs.micropython.org/en/latest/esp8266/esp8266/quickref.html).
