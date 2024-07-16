## Configuration Instructions

To edit the configuration file, use the following command:

sudo nano boot/firmware/config.txt

Add or modify the following lines in the file:
```
dtoverlay=uart3
usb_max_current_enable=1
dtparam=rtc_bbat_vchg=3000000
```

sudo raspi-config 

enable VNC; I2C; SERIAL; REMOTE GPIO

