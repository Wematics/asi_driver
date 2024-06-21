import os

def read_cpu_temperature():
    temp_file = "/sys/class/hwmon/hwmon0/temp1_input"

    if os.path.exists(temp_file):
        with open(temp_file, "r") as f:
            temp = int(f.read().strip()) / 1000.0
            print(f"CPU Temperature: {temp:.2f} °C")
    else:
        print(f"{temp_file} does not exist.")

read_cpu_temperature()
