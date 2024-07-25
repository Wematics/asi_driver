import time
import board
import busio
import adafruit_bme280.basic as adafruit_bme280
import adafruit_lis2mdl
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import serial
import subprocess
import os
import math

# BME280 Sensor
i2c = board.I2C()
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

# LIS2MDL Magnetometer
mag_sensor = adafruit_lis2mdl.LIS2MDL(i2c)

# ADS1115 ADC for Apogee and NTC sensors
ads = ADS.ADS1115(i2c, address=0x49)
calibration_factor_apogee = 23
R1 = 10000
Vcc = 3.3
Bc = 3380
Tnom = 25
Rntc = 10000

def calculate_ntc_temperature(voltage):
    if voltage <= 0 or voltage >= Vcc:
        return float('inf')
    R2 = voltage * R1 / (Vcc - voltage)
    steinhart = R2 / Rntc
    steinhart = math.log(steinhart)
    steinhart /= Bc
    steinhart += 1 / (Tnom + 273.15)
    steinhart = 1 / steinhart
    steinhart -= 273.15
    return steinhart

# GPS
ser = serial.Serial(port='/dev/serial0', baudrate=9600, timeout=1)

def read_cpu_temperature():
    temp_file = "/sys/class/hwmon/hwmon0/temp1_input"
    if os.path.exists(temp_file):
        with open(temp_file, "r") as f:
            temp = int(f.read().strip()) / 1000.0
            return temp
    else:
        return None

def read_housing_temperature():
    hwmon_path = "/sys/class/hwmon"
    for device in os.listdir(hwmon_path):
        device_path = os.path.join(hwmon_path, device)
        name_file = os.path.join(device_path, "name")
        if os.path.exists(name_file):
            with open(name_file, "r") as f:
                name = f.read().strip()
                if name == "lm75":
                    temp_file = os.path.join(device_path, "temp1_input")
                    with open(temp_file, "r") as tf:
                        temp = int(tf.read().strip()) / 1000.0
                        return temp
    return None

def read_voltage(component):
    try:
        result = subprocess.run(['vcgencmd', 'measure_volts', component], stdout=subprocess.PIPE, text=True)
        voltage = result.stdout.strip()
        return voltage
    except FileNotFoundError:
        return "vcgencmd command not found."

def set_fan_speed(speed):
    with open("/sys/class/hwmon/hwmon2/pwm1", "w") as f:
        f.write(str(speed))

while True:
    # BME280
    temperature = bme280.temperature
    humidity = bme280.humidity
    pressure = bme280.pressure
    print(f"BME280 - Temperature: {temperature:.2f} °C, Humidity: {humidity:.2f} %, Pressure: {pressure:.2f} hPa")

    # LIS2MDL
    mag_x, mag_y, mag_z = mag_sensor.magnetic
    print(f"LIS2MDL - Magnetometer (uT): ({mag_x:.3f}, {mag_y:.3f}, {mag_z:.3f})")

    # ADS1115
    ads.gain = 16
    apogee_channel = AnalogIn(ads, ADS.P0, ADS.P1)
    apogee_voltage = apogee_channel.voltage * 1000
    irradiance = max(apogee_voltage * calibration_factor_apogee, 0)
    ads.gain = 1
    ntc_channel = AnalogIn(ads, ADS.P2)
    ntc_voltage = ntc_channel.voltage
    temperature_ntc = calculate_ntc_temperature(ntc_voltage)
    print(f"Apogee - Irradiance: {irradiance:.2f} W/m², NTC - Temperature: {temperature_ntc:.2f} °C")

    # GPS
    if ser.in_waiting > 0:
        gps_data = ser.readline().decode('utf-8').strip()
        print(f"GPS - Data: {gps_data}")

    # CPU Temperature
    cpu_temp = read_cpu_temperature()
    if cpu_temp:
        print(f"CPU Temperature: {cpu_temp:.2f} °C")

    # Housing Temperature
    housing_temp = read_housing_temperature()
    if housing_temp:
        print(f"Housing Temperature: {housing_temp:.2f} °C")
        # Control fan based on housing temperature
        if housing_temp > 60:
            set_fan_speed(255)
        elif housing_temp > 50:
            set_fan_speed(128)
        else:
            set_fan_speed(0)

    # Pi Voltages
    components = ['core', 'sdram_c', 'sdram_i', 'sdram_p']
    for component in components:
        voltage = read_voltage(component)
        print(f"{component} voltage: {voltage}")

    time.sleep(1)
