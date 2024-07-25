import time
import os
import board
import busio
import subprocess
import math
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_bme280 import basic as adafruit_bme280
import adafruit_lis2mdl

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object using the I2C bus
ads = ADS.ADS1115(i2c, address=0x49)

# Calibration factors and constants
calibration_factor_apogee = 23  # W/m²/mV for Apogee sensor
R1 = 10000  # Pull-up resistor value in ohms
Vcc = 3.3  # Supply voltage
Bc = 3380  # B-constant of the NTC thermistor
Tnom = 25  # Nominal temperature in °C for Rntc value
Rntc = 10000  # Resistance of the NTC thermistor at nominal temperature

# Create BME280 sensor object
try:
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
except Exception as e:
    bme280 = None
    print(f"Error initializing BME280: {e}")

# Create LIS2MDL magnetometer sensor object
try:
    sensor = adafruit_lis2mdl.LIS2MDL(i2c)
except Exception as e:
    sensor = None
    print(f"Error initializing LIS2MDL: {e}")

def calculate_ntc_temperature(voltage):
    if voltage <= 0 or voltage >= Vcc:  # Prevent division by zero and invalid voltage
        return float('inf')
    # Calculate the resistance of the NTC thermistor
    R2 = voltage * R1 / (Vcc - voltage)
    
    # Steinhart-Hart equation
    steinhart = R2 / Rntc
    steinhart = math.log(steinhart)
    steinhart /= Bc
    steinhart += 1 / (Tnom + 273.15)
    steinhart = 1 / steinhart
    steinhart -= 273.15
    return steinhart

def read_cpu_temperature():
    temp_file = "/sys/class/hwmon/hwmon0/temp1_input"
    if os.path.exists(temp_file):
        try:
            with open(temp_file, "r") as f:
                temp = int(f.read().strip()) / 1000.0
                return temp
        except Exception as e:
            print(f"Error reading CPU temperature: {e}")
    else:
        print(f"{temp_file} does not exist.")
    return None

def read_fan_speed():
    fan_speed_path = "/sys/class/hwmon/hwmon2/pwm1"
    try:
        with open(fan_speed_path, 'r') as f:
            fan_speed = f.read().strip()
            return int(fan_speed)
    except Exception as e:
        print(f"Error reading fan speed: {e}")
        return None

def read_lm75_temperature():
    hwmon_path = "/sys/class/hwmon"
    for device in os.listdir(hwmon_path):
        device_path = os.path.join(hwmon_path, device)
        name_file = os.path.join(device_path, "name")
        if os.path.exists(name_file):
            try:
                with open(name_file, "r") as f:
                    name = f.read().strip()
                    if name == "lm75":
                        temp_file = os.path.join(device_path, "temp1_input")
                        with open(temp_file, "r") as tf:
                            temp = int(tf.read().strip()) / 1000.0
                            return temp
            except Exception as e:
                print(f"Error reading LM75 temperature: {e}")
    return None

def main():
    print("{:>15}\t{:>5}\t{:>7}\t{:>15}".format('Channel', 'Raw', 'Volts', 'W/m² / °C'))

    while True:
        try:
            # Measure Apogee sensor with high gain
            ads.gain = 16
            try:
                apogee_channel = AnalogIn(ads, ADS.P0, ADS.P1)
                apogee_voltage = apogee_channel.voltage * 1000  # Convert to mV
                irradiance = max(apogee_voltage * calibration_factor_apogee, 0)  # Ensure no negative values
                print("Channel 0 (Apogee): {:>5}\t{:>7.6f} V\t{:>15.2f} W/m²".format(apogee_channel.value, apogee_channel.voltage, irradiance))
            except Exception as e:
                print(f"Error reading Apogee sensor: {e}")

            # Measure NTC temperature sensor with appropriate gain
            ads.gain = 1
            try:
                ntc_channel = AnalogIn(ads, ADS.P2)
                ntc_voltage = ntc_channel.voltage
                temperature = calculate_ntc_temperature(ntc_voltage)
                if temperature < -40:
                    temperature = None
                if temperature is not None:
                    print("Channel 1 (NTC___): {:>5}\t{:>7.6f} V\t{:>15.2f} °C".format(ntc_channel.value, ntc_channel.voltage, temperature))
                else:
                    print("Channel 1 (NTC___): {:>5}\t{:>7.6f} V\t{:>15} (Not Connected)".format(ntc_channel.value, ntc_channel.voltage, ''))
            except Exception as e:
                print(f"Error reading NTC sensor: {e}")

            # Read magnetometer data
            if sensor:
                try:
                    mag_x, mag_y, mag_z = sensor.magnetic
                    print('Magnetometer (uT): ({0:10.3f}, {1:10.3f}, {2:10.3f})'.format(mag_x, mag_y, mag_z))
                except Exception as e:
                    print(f"Error reading magnetometer: {e}")

            # Read BME280 data
            if bme280:
                try:
                    bme_temperature = bme280.temperature
                    humidity = bme280.humidity
                    pressure = bme280.pressure
                    print(f"Env. Temperature: {bme_temperature:.2f} °C")
                    print(f"Env. Humidity: {humidity:.2f} %")
                    print(f"Env. Pressure: {pressure:.2f} hPa")
                except Exception as e:
                    print(f"Error reading BME280 sensor: {e}")

            # Read CPU temperature
            cpu_temp = read_cpu_temperature()
            if cpu_temp is not None:
                print(f"CPU Temperature: {cpu_temp:.2f} °C")

            # Read fan speed
            fan_speed = read_fan_speed()
            if fan_speed is not None:
                print(f"Current fan speed: {fan_speed} (PWM value)")
            else:
                print("Failed to read fan speed.")

            # Read LM75 temperature sensor
            lm75_temp = read_lm75_temperature()
            if lm75_temp is not None:
                print(f"LM75 Temperature: {lm75_temp:.2f} °C")

        except Exception as e:
            print(f"Error in main loop: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    main()
