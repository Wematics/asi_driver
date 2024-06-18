#pip install adafruit-circuitpython-ads1x15
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize ADS1115
ads = ADS.ADS1115(i2c, address=0x48)

# Set gain
ads.gain = 4

# Create single-ended input on channel 0, 1, 2, and 3
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

# Create differential input between channel 0 and 1
chan_diff = AnalogIn(ads, ADS.P0, ADS.P1)

print("{:>5}\t{:>5}".format('Raw', 'Volts'))

try:
    while True:
    print("Channel 0: {:>5}\t{:>5.6f}".format(chan0.value, chan0.voltage))
    print("Channel 1: {:>5}\t{:>5.6f}".format(chan1.value, chan1.voltage))
    print("Channel 2: {:>5}\t{:>5.6f}".format(chan2.value, chan2.voltage))
    print("Channel 3: {:>5}\t{:>5.6f}".format(chan3.value, chan3.voltage))
    print("Differential (0-1): {:>5}\t{:>5.6f}".format(chan_diff.value, chan_diff.voltage))
    time.sleep(0.5)
except KeyboardInterrupt:
    print("Script interrupted by user.")
except Exception as e:
    print(f"An error occurred: {e}")
