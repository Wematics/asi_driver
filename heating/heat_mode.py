import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import math
import RPi.GPIO as GPIO
import signal
import sys

# GPIO setup
HEATER_EN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(HEATER_EN, GPIO.OUT)

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c, address=0x49)

# Constants for NTC temperature calculation
R1 = 10000  # Pull-up resistor value in ohms
Vcc = 3.3  # Supply voltage
Bc = 3380  # B-constant of the NTC thermistor
Tnom = 25  # Nominal temperature in °C for Rntc value
Rntc = 10000  # Resistance of the NTC thermistor at nominal temperature

def calculate_ntc_temperature(voltage):
    if voltage <= 0 or voltage >= Vcc:  # Prevent division by zero and invalid voltage
        return float('inf')
    # Calculate the resistance of the NTC thermistor
    R2 = voltage * R1 / (Vcc - voltage)
    print(f"Debug: NTC Voltage = {voltage:.6f} V, R2 = {R2:.2f} Ohms")  # Debug print

    # Steinhart-Hart equation
    steinhart = R2 / Rntc
    steinhart = math.log(steinhart)
    steinhart /= Bc
    steinhart += 1 / (Tnom + 273.15)
    steinhart = 1 / steinhart
    steinhart -= 273.15
    return steinhart

def heater_control(mode):
    ON_TIME = OFF_TIME = 0
    if mode == 1:
        ON_TIME = 2
        OFF_TIME = 20
    elif mode == 2:
        ON_TIME = 5
        OFF_TIME = 20
    elif mode == 3:
        ON_TIME = 10
        OFF_TIME = 20

    try:
        while True:
            if mode in [1, 2, 3]:
                print(f"Turning heater on for {ON_TIME} seconds...")
                GPIO.output(HEATER_EN, GPIO.HIGH)
                end_time = time.time() + ON_TIME
                while time.time() < end_time:
                    temperature = read_ntc_temperature()
                    print(f"Current Temperature: {temperature:.2f} °C")
                    time.sleep(1)
                print(f"Turning heater off for {OFF_TIME} seconds...")
                GPIO.output(HEATER_EN, GPIO.LOW)
                time.sleep(OFF_TIME)
            elif mode == 4:
                while True:
                    temperature = read_ntc_temperature()
                    print(f"Current Temperature: {temperature:.2f} °C")
                    if temperature < 15:
                        GPIO.output(HEATER_EN, GPIO.HIGH)
                        print("Heater turned ON (temperature below 15°C)")
                        on_time_start = time.time()
                        while time.time() - on_time_start < 120:
                            temperature = read_ntc_temperature()
                            print(f"Current Temperature: {temperature:.2f} °C")
                            time.sleep(1)
                    elif temperature > 45:
                        GPIO.output(HEATER_EN, GPIO.LOW)
                        print("Heater turned OFF (temperature above 45°C)")
                        off_time_start = time.time()
                        while time.time() - off_time_start < 120:
                            temperature = read_ntc_temperature()
                            print(f"Current Temperature: {temperature:.2f} °C")
                            time.sleep(1)
                    else:
                        time.sleep(5)  # Check temperature every 5 seconds in this mode
    except KeyboardInterrupt:
        print("Script interrupted. Turning off heater.")
        GPIO.output(HEATER_EN, GPIO.LOW)
        GPIO.cleanup()
        sys.exit(0)

def read_ntc_temperature():
    ads.gain = 1
    ntc_channel = AnalogIn(ads, ADS.P2)
    ntc_voltage = ntc_channel.voltage
    temperature = calculate_ntc_temperature(ntc_voltage)
    return temperature

def signal_handler(sig, frame):
    print("Signal received. Turning off heater.")
    GPIO.output(HEATER_EN, GPIO.LOW)
    GPIO.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Select mode: 1, 2, 3, or 4")
    mode = int(input("Enter mode: "))
    if mode not in [1, 2, 3, 4]:
        print("Invalid mode selected. Exiting.")
    else:
        heater_control(mode)
