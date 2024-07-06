import csv
from datetime import datetime, timedelta
import subprocess
import logging

# Set up logging
logging.basicConfig(filename='/home/pi/sun_times_project/sleep_wake.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Path to the lookup table
CSV_FILE = "/home/pi/sun_times_project/sun_times_dresden.csv"

def read_sun_times(csv_file, target_date):
    sunrise = sunset = None

    try:
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Date'] == target_date:
                    sunrise = row['Sunrise']
                    sunset = row['Sunset']
                    logging.info(f"Found sunrise: {sunrise}, sunset: {sunset} for date: {target_date}")
                    break
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")

    return sunrise, sunset

def set_rtc_wake_alarm(wake_time):
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
    current_date = datetime.now().strftime("%Y-%m-%d")
    sunrise, sunset = read_sun_times(CSV_FILE, current_date)

    if sunrise and sunset:
        # Convert sunrise and sunset to datetime objects for the current date
        sunrise_time = datetime.strptime(f"{current_date} {sunrise}", "%Y-%m-%d %H:%M")
        sunset_time = datetime.strptime(f"{current_date} {sunset}", "%Y-%m-%d %H:%M")

        # Get the current time
        current_time = datetime.now()

        # Check if the current time is past sunset
        if current_time > sunset_time:
            # Set the wake time for the next day's sunrise
            next_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            next_sunrise, _ = read_sun_times(CSV_FILE, next_date)
            if next_sunrise:
                next_sunrise_time = datetime.strptime(f"{next_date} {next_sunrise}", "%Y-%m-%d %H:%M")
                logging.info(f"Current time is past sunset: {sunset_time}. Setting wake time for next sunrise: {next_sunrise_time}")
                set_rtc_wake_alarm(next_sunrise_time)
            else:
                logging.error("Sunrise time not found for the next date.")
        else:
            logging.info(f"Current time is before sunset: {sunset_time}. System will remain on.")
    else:
        logging.error("Sunrise and sunset times not found for the current date.")
