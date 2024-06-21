import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import math

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

print("{:>15}\t{:>5}\t{:>7}\t{:>10}".format('Channel', 'Raw', 'Volts', 'W/m² / °C'))

while True:
    try:
        # Measure Apogee sensor with high gain
        ads.gain = 16
        apogee_channel = AnalogIn(ads, ADS.P0, ADS.P1)
        apogee_voltage = apogee_channel.voltage * 1000  # Convert to mV
        irradiance = max(apogee_voltage * calibration_factor_apogee, 0)  # Ensure no negative values

        # Measure NTC temperature sensor with appropriate gain
        ads.gain = 1
        ntc_channel = AnalogIn(ads, ADS.P2)
        ntc_voltage = ntc_channel.voltage
        
        # Debug print
        print(f"Debug: NTC Raw Value = {ntc_channel.value}, NTC Voltage = {ntc_voltage:.6f} V")
        
        # Calculate temperature using the revised function
        temperature = calculate_ntc_temperature(ntc_voltage)
        
        print("Channel 0 (Apogee): {:>5}\t{:>7.6f} V\t{:>10.2f} W/m²".format(apogee_channel.value, apogee_channel.voltage, irradiance))
        print("Channel 1 (NTC___): {:>5}\t{:>7.6f} V\t{:>10.2f} °C".format(ntc_channel.value, ntc_channel.voltage, temperature))

        # Channel 3 (floating, ignore values)
        ads.gain = 4  # Reset gain to a default value for the floating channel
        float_channel = AnalogIn(ads, ADS.P3)
        print("Channel 2 (Float_): {:>5}\t{:>7.6f} V".format(float_channel.value, float_channel.voltage))

    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(0.5)
