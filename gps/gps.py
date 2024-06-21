#sudo nano /boot/firmware/config.txt
#enable_uart=1
#sudo reboot
#sudo apt-get update
#sudo apt-get install gpsd gpsd-clients python3-gps
#pip install pyserial

import serial
import time

# Configure the serial port
ser = serial.Serial(
    port='/dev/serial0',  # Use '/dev/serial0' for UART on Raspberry Pi
    baudrate=9600,  # Baud rate for GPS module
    timeout=1
)

def read_gps_data():
    try:
        while True:
            if ser.in_waiting > 0:
                gps_data = ser.readline().decode('utf-8').strip()
                print(gps_data)
    except KeyboardInterrupt:
        print("Exiting Program")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ser.close()

if __name__ == "__main__":
    print("Reading GPS data...")
    read_gps_data()

