#pip install adafruit-circuitpython-lis2mdl

import time
import board
import adafruit_lis2mdl

i2c = board.I2C()  # uses board.SCL and board.SDA
sensor = adafruit_lis2mdl.LIS2MDL(i2c)

while True:
    mag_x, mag_y, mag_z = sensor.magnetic
    print('Magnetometer (uT): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(mag_x, mag_y, mag_z))
    print('')
    time.sleep(1.0)
