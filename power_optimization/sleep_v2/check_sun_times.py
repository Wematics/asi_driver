import csv
import json
from datetime import datetime, timedelta, timezone
import pytz
import subprocess
import logging

# Set up logging
logging.basicConfig(filename='/home/pi/sleep_mode/sleep_wake.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Load configuration
CONFIG_FILE = "/home/pi/sleep_mode/config.json"
with open(CONFIG_FILE, 'r') as config_file:
    config = json.load(config_file)
    location_name = config['location_name']
    timezone_name = config['timezone']

# Path to the lookup table
CSV_FILE = f"/home/pi/sleep_mode/sun_times_{location_name.replace(' ', '_')}_UTC.csv"

MAX_SLEEP_DURATION = 20 * 3600  # 20 hours in seconds

def read_sun_times(csv_file, day_month):
    logging.info(f"Reading sun times for day-month: {day_month}")
    sunrise = sunset = None

    try:
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Day'] == day_month:
                    sunrise = row['Sunrise']
                    sunset = row['Sunset']
                    logging.info(f"Found sunrise: {sunrise}, sunset: {sunset} for day-month: {day_month}")
                    break
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")

    return sunrise, sunset

def set_rtc_wake_alarm(seconds_until_wake):
    try:
        subprocess.run(["sudo", "bash", "-c", f"echo +{seconds_until_wake} > /sys/class/rtc/rtc0/wakealarm"], check=True)
        logging.info(f"RTC wake alarm set for {seconds_until_wake} seconds from now")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set RTC wake alarm: {e}")
        return False

def shutdown_system():
    logging.info("Shutting down system in 60 seconds")
    subprocess.run(["sleep", "60"])
    try:
        subprocess.run(["sudo", "shutdown", "-h", "+1"], check=True)  # Shutdown in 1 minute
        logging.info("System shutdown initiated")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to initiate system shutdown: {e}")

if __name__ == "__main__":
    # Load the timezone
    local_tz = pytz.timezone(timezone_name)

    # Get current time in UTC and convert it to local time
    current_time_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    current_time_local = current_time_utc.astimezone(local_tz)

    current_day_month = current_time_local.strftime("%m-%d")
    today_date = current_time_local.strftime("%Y-%m-%d")

    sunrise_utc, sunset_utc = read_sun_times(CSV_FILE, current_day_month)

    if sunrise_utc and sunset_utc:
        sunrise_time_local = datetime.strptime(f"{today_date} {sunrise_utc}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(local_tz)
        sunset_time_local = datetime.strptime(f"{today_date} {sunset_utc}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(local_tz)

        if current_time_local > sunset_time_local:
            next_day = current_time_local + timedelta(days=1)
            next_day_month = next_day.strftime("%m-%d")
            next_day_date = next_day.strftime("%Y-%m-%d")

            sunrise_next_day_utc, _ = read_sun_times(CSV_FILE, next_day_month)
            if sunrise_next_day_utc:
                sunrise_time_next_day_local = datetime.strptime(f"{next_day_date} {sunrise_next_day_utc}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(local_tz)

            if current_time_local < sunrise_time_next_day_local:
                time_diff = (sunrise_time_next_day_local - current_time_local).total_seconds()
                if time_diff > MAX_SLEEP_DURATION:
                    time_diff = MAX_SLEEP_DURATION
                    logging.info(f"Sleep duration exceeds 20 hours, setting maximum sleep duration of {MAX_SLEEP_DURATION} seconds.")
                logging.info(f"Current time is between sunset and the next sunrise. Setting wake time for sunrise.")
                if set_rtc_wake_alarm(int(time_diff)):
                    shutdown_system()
                else:
                    logging.info("Wake-up alarm not set, system will remain on.")
            else:
                logging.info("Current time is after sunrise, system remains online.")
        else:
            logging.info(f"Current time is before sunset: {sunset_time_local}. System will remain on.")
    else:
        logging.error("Sunrise and sunset times not found for the current day.")
