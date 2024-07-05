import csv
from datetime import datetime, timedelta
import subprocess
import logging

# Set up logging
logging.basicConfig(filename='/home/pi/sun_times_project/sleep_wake.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Path to the lookup table
CSV_FILE = "/home/pi/sun_times_project/sun_times_dresden.csv"

def read_sun_times(csv_file):
    current_year_month = datetime.now().strftime("%Y-%m")
    logging.info(f"Current year-month: {current_year_month}")
    sunrise = sunset = None

    try:
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                logging.info(f"Reading row: {row}")
                if row['Month'] == current_year_month:
                    sunrise = row['Sunrise']
                    sunset = row['Sunset']
                    logging.info(f"Found sunrise: {sunrise}, sunset: {sunset} for month: {current_year_month}")
                    break
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")

    return sunrise, sunset

def set_rtc_wake_alarm(sunrise, sunset):
    # Convert sunrise and sunset to datetime objects
    today = datetime.now().strftime("%Y-%m-%d")
    wake_time = datetime.strptime(f"{today} {sunrise}", "%Y-%m-%d %H:%M")
    sleep_time = datetime.strptime(f"{today} {sunset}", "%Y-%m-%d %H:%M")

    # If the current time is past the sunset time, set the wake time for the next day
    if datetime.now() > sleep_time:
        wake_time = wake_time + timedelta(days=1)

    # Calculate the time difference in seconds for wake time
    wake_diff = int((wake_time - datetime.now()).total_seconds())

    # Set RTC wake alarm
    try:
        subprocess.run(["sudo", "bash", "-c", f"echo +{wake_diff} > /sys/class/rtc/rtc0/wakealarm"], check=True)
        logging.info(f"RTC wake alarm set for {wake_time}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set RTC wake alarm: {e}")

    # Shutdown the system 30 seconds after setting the wake alarm
    logging.info("Shutting down system in 30 seconds")
    subprocess.run(["sleep", "30"])
    try:
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
        logging.info("System shutdown")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to shutdown the system: {e}")

if __name__ == "__main__":
    sunrise, sunset = read_sun_times(CSV_FILE)
    if sunrise and sunset:
        set_rtc_wake_alarm(sunrise, sunset)
    else:
        logging.error("Sunrise and sunset times not found for the current month.")
