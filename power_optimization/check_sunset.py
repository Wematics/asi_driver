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

def set_rtc_wake_alarm(seconds_until_wake):
    # Set RTC wake alarm
    try:
        subprocess.run(["sudo", "bash", "-c", f"echo +{seconds_until_wake} > /sys/class/rtc/rtc0/wakealarm"], check=True)
        logging.info(f"RTC wake alarm set for {seconds_until_wake} seconds from now")
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
        # Get the current date and time
        current_time = datetime.now()
        today_date = current_time.strftime("%Y-%m-%d")
        
        # Convert sunrise and sunset times to datetime objects using today's date
        sunrise_time = datetime.strptime(f"{today_date} {sunrise}", "%Y-%m-%d %H:%M")
        sunset_time = datetime.strptime(f"{today_date} {sunset}", "%Y-%m-%d %H:%M")

        # Check if the current time is past sunset
        if current_time > sunset_time:
            # Calculate the time difference in seconds between sunset and the next sunrise
            time_diff = abs((sunrise_time - sunset_time).total_seconds())  # Ensure positive number
            logging.info(f"Current time is past sunset: {sunset_time}. Setting wake time for sunrise.")
            set_rtc_wake_alarm(int(time_diff))
        else:
            logging.info(f"Current time is before sunset: {sunset_time}. System will remain on.")
    else:
        logging.error("Sunrise and sunset times not found for the current month.")
