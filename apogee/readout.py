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
ads.gain = 16

# Initialize channel (single-ended on channel 0)
chan = AnalogIn(ads, ADS.P1)

print("{:>5}\t{:>5}".format('Raw', 'Volts'))

try:
    while True:
        print("{:>5}\t{:>5.3f}".format(chan.value, chan.voltage))
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Script interrupted by user.")
except Exception as e:
    print(f"An error occurred: {e}")
