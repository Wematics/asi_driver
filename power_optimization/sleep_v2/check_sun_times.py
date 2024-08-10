#!/usr/bin/env python3
import csv
import json
import os
import logging
from datetime import datetime, timedelta, timezone
import pytz
import subprocess
from logging.handlers import RotatingFileHandler

# Set up logging with log rotation to ensure logs do not exceed a certain size.
# This helps in maintaining logs without consuming too much disk space.
log_file = '/home/pi/Desktop/skycam/scripts/sleep/sleep_wake.log'
handler = RotatingFileHandler(log_file, maxBytes=50*1024*1024, backupCount=3)  # 50 MB per log file, keep 3 backups
logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s - %(message)s')

logging.info("Script started.")

# Load configuration from the specified JSON file.
# The configuration includes location name and timezone information.
CONFIG_FILE = "/home/pi/Desktop/skycam/scripts/sleep/config.json"
if not os.path.exists(CONFIG_FILE):
    logging.error(f"Configuration file not found: {CONFIG_FILE}")
    exit(1)

with open(CONFIG_FILE, 'r') as config_file:
    config = json.load(config_file)
    location_name = config['location_name']
    timezone_name = config['timezone']

logging.info(f"Loaded configuration: location_name={location_name}, timezone_name={timezone_name}")

# Path to the CSV file containing sunrise and sunset times in UTC.
# The path is constructed based on the location name provided in the configuration.
CSV_FILE = f"/home/pi/Desktop/skycam/scripts/sleep/sun_times_{location_name.replace(' ', '_')}_UTC.csv"
if not os.path.exists(CSV_FILE):
    logging.error(f"Sun times CSV file not found: {CSV_FILE}")
    exit(1)

# Define the maximum sleep duration to prevent the system from sleeping for too long.
MAX_SLEEP_DURATION = 20 * 3600  # 20 hours in seconds

def read_sun_times(csv_file, day_month):
    """
    Reads the sunrise and sunset times for a given day from the CSV file.

    Parameters:
    - csv_file: Path to the CSV file containing sunrise and sunset times.
    - day_month: String representing the current day and month in the format "MM-DD".

    Returns:
    - sunrise: String representing the sunrise time in UTC.
    - sunset: String representing the sunset time in UTC.
    """
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
        if not sunrise or not sunset:
            logging.warning(f"No sun times found for day-month: {day_month}")
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")

    return sunrise, sunset

def set_rtc_wake_alarm(seconds_until_wake):
    """
    Sets the RTC wake alarm to wake the system after a specified number of seconds.

    Parameters:
    - seconds_until_wake: Number of seconds after which the system should wake up.

    Returns:
    - True if the RTC wake alarm was set successfully, False otherwise.
    """
    try:
        logging.info(f"Setting RTC wake alarm for {seconds_until_wake} seconds from now.")
        subprocess.run(["sudo", "bash", "-c", f"echo +{seconds_until_wake} > /sys/class/rtc/rtc0/wakealarm"], check=True)
        logging.info("RTC wake alarm successfully set.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set RTC wake alarm: {e}")
        return False

def shutdown_system():
    """
    Shuts down the system after a brief delay to ensure all processes are closed properly.
    """
    logging.info("Shutting down system in 90 seconds.")
    subprocess.run(["sleep", "90"])
    try:
        logging.info("Initiating system shutdown.")
        subprocess.run(["sudo", "shutdown", "-h", "+1"], check=True)  # Shutdown in 1 minute
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to initiate system shutdown: {e}")

if __name__ == "__main__":
    try:
        # Load the timezone specified in the configuration.
        logging.info("Loading timezone.")
        local_tz = pytz.timezone(timezone_name)

        # Get the current time in UTC and convert it to the local time.
        logging.info("Getting current UTC time from RTC and converting to local time.")
        current_time_utc = datetime.now(timezone.utc)
        current_time_local = current_time_utc.astimezone(local_tz)
        logging.info(f"Current time: UTC={current_time_utc}, Local={current_time_local}")

        # Extract the current day and month for looking up sunrise and sunset times.
        current_day_month = current_time_local.strftime("%m-%d")
        logging.info(f"Current day-month: {current_day_month}")

        # Read the sunrise and sunset times from the CSV file.
        sunrise_utc, sunset_utc = read_sun_times(CSV_FILE, current_day_month)

        if sunrise_utc and sunset_utc:
            # Convert the sunrise and sunset times from UTC to local time.
            sunrise_time_local = datetime.strptime(f"{current_day_month} {sunrise_utc}", "%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(local_tz)
            sunset_time_local = datetime.strptime(f"{current_day_month} {sunset_utc}", "%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(local_tz)

            logging.info(f"Sunrise time local: {sunrise_time_local}, Sunset time local: {sunset_time_local}")

            if current_time_local > sunset_time_local:
                # If the current time is after sunset, calculate the time until the next sunrise.
                logging.info("Current time is after sunset.")
                next_day = current_time_local + timedelta(days=1)
                next_day_month = next_day.strftime("%m-%d")
                sunrise_next_day_utc, _ = read_sun_times(CSV_FILE, next_day_month)
                if sunrise_next_day_utc:
                    sunrise_time_next_day_local = datetime.strptime(f"{next_day_month} {sunrise_next_day_utc}", "%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(local_tz)
                    logging.info(f"Next day's sunrise time local: {sunrise_time_next_day_local}")

                    time_diff = (sunrise_time_next_day_local - current_time_local).total_seconds()
                    if time_diff > MAX_SLEEP_DURATION:
                        time_diff = MAX_SLEEP_DURATION
                        logging.info(f"Sleep duration exceeds 20 hours, setting maximum sleep duration of {MAX_SLEEP_DURATION} seconds.")

                    # Set the RTC wake alarm and shut down the system.
                    logging.info("Setting RTC wake alarm and shutting down.")
                    if set_rtc_wake_alarm(int(time_diff)):
                        shutdown_system()
                    else:
                        logging.info("Wake-up alarm not set, system will remain on.")
                else:
                    logging.error(f"No sunrise time found for next day ({next_day_month}). Staying online.")
            else:
                logging.info("Current time is before sunset. System will remain on.")
        else:
            logging.error(f"Sunrise and sunset times not found for {current_day_month}. Staying online.")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit(1)
