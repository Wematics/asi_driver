## Configuration Instructions

To edit the configuration file, use the following command:
```
sudo nano boot/firmware/config.txt
```
Add or modify the following lines in the file:
```
dtoverlay=uart3 #GPS
usb_max_current_enable=1 #USB Boot
dtparam=rtc_bbat_vchg=3000000 #RTC 3V
dtoverlay=lm75-overlay #Temp. Housing
dtoverlay=emc2301-overlay #Fan PWM
```

sudo raspi-config 

enable VNC; I2C; SERIAL; REMOTE GPIO

https://support.remote.it/hc/en-us/articles/360054866351-Removing-Uninstalling-the-remoteit-package-or-Desktop-application#:~:text=and%20Linux%20Desktop-,Open%20the%20Desktop%20app%20and%20go%20to%20Settings%2D%3EAdvanced.,it%22%20icon%20to%20the%20trash.

https://support.remote.it/hc/en-us/articles/360046373452-Checking-that-everything-is-running-properly-remoteit-package


sudo journalctl | grep remoteit
