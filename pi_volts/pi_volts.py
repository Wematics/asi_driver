import subprocess

def read_voltage(component):
    try:
        result = subprocess.run(['vcgencmd', 'measure_volts', component], stdout=subprocess.PIPE, text=True)
        voltage = result.stdout.strip()
        return voltage
    except FileNotFoundError:
        return f"vcgencmd command not found. Make sure you are running this on a Raspberry Pi with vcgencmd installed."

def main():
    components = ['core', 'sdram_c', 'sdram_i', 'sdram_p']
    for component in components:
        voltage = read_voltage(component)
        print(f"{component} voltage: {voltage}")

if __name__ == "__main__":
    main()
