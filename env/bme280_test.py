import time
import board
from adafruit_bme280 import basic as adafruit_bme280

i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

# Read and print the sensor data
while True:
    temperature = bme280.temperature
    humidity = bme280.humidity
    pressure = bme280.pressure

    print(f"Temperature: {temperature:.2f} °C")
    print(f"Humidity: {humidity:.2f} %")
    print(f"Pressure: {pressure:.2f} hPa")
 
    time.sleep(1)
