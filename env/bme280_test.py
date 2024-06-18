import time
import board
from adafruit_bme280 import basic as adafruit_bme280
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

# Read and print the sensor data
while True:
    temperature = bme280.get_temperature()
    humidity = bme280.get_humidity()
    pressure = bme280.get_pressure()

    print(f"Temperature: {temperature} °C")
    print(f"Humidity: {humidity} %")
    print(f"Pressure: {pressure} hPa")

    time.sleep(1)
