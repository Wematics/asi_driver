import os

def read_temperature():
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
                        print(f"Temperature: {temp:.2f} °C")
                        return temp

read_temperature()
