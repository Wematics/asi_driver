#!/usr/bin/env python3
import csv
import json
import os
import logging
from datetime import datetime, timedelta, timezone
import pytz
import subprocess
from logging.handlers import RotatingFileHandler

# Set up logging with log rotation
log_file = '/home/pi/Desktop/skycam/scripts/sleep/sleep_wake.log'
handler = RotatingFileHandler(log_file, maxBytes=50*1024*1024, backupCount=3)  # 50 MB per log file, keep 3 backups
logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s - %(message)s')

logging.info("Script started.")

# Load configuration
CONFIG_FILE = "/home/pi/Desktop/skycam/scripts/sleep/config.json"
if not os.path.exists(CONFIG_FILE):
    logging.error(f"Configuration file not found: {CONFIG_FILE}")
    exit(1)

with open(CONFIG_FILE, 'r') as config_file:
    config = json.load(config_file)
    location_name = config['location_name']
    timezone_name = config['timezone']

logging.info(f"Loaded configuration: location_name={location_name}, timezone_name={timezone_name}")

# Path to the lookup table
CSV_FILE = f"/home/pi/Desktop/skycam/scripts/sleep/sun_times_{location_name.replace(' ', '_')}_UTC.csv"
if not os.path.exists(CSV_FILE):
    logging.error(f"Sun times CSV file not found: {CSV_FILE}")
    exit(1)

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
        if not sunrise or not sunset:
            logging.warning(f"No sun times found for day-month: {day_month}")
    except FileNotFoundError:
        logging.error(f"CSV file not found: {csv_file}")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")

    return sunrise, sunset

def set_rtc_wake_alarm(seconds_until_wake):
    try:
        logging.info(f"Setting RTC wake alarm for {seconds_until_wake} seconds from now.")
        subprocess.run(["sudo", "bash", "-c", f"echo +{seconds_until_wake} > /sys/class/rtc/rtc0/wakealarm"], check=True)
        logging.info("RTC wake alarm successfully set.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set RTC wake alarm: {e}")
        return False

def shutdown_system():
    logging.info("Shutting down system in 90 seconds.")
    subprocess.run(["sleep", "90"])
    try:
        logging.info("Initiating system shutdown.")
        subprocess.run(["sudo", "shutdown", "-h", "+1"], check=True)  # Shutdown in 1 minute
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to initiate system shutdown: {e}")

if __name__ == "__main__":
    try:
        # Load the timezone
        logging.info("Loading timezone.")
        local_tz = pytz.timezone(timezone_name)

        # Get current time in UTC from RTC and convert to local time
        logging.info("Getting current UTC time from RTC and converting to local time.")
        current_time_utc = datetime.now(timezone.utc)
        current_time_local = current_time_utc.astimezone(local_tz)
        logging.info(f"Current time: UTC={current_time_utc}, Local={current_time_local}")

        current_day_month = current_time_local.strftime("%m-%d")
        logging.info(f"Current day-month: {current_day_month}")

        sunrise_utc, sunset_utc = read_sun_times(CSV_FILE, current_day_month)

        if sunrise_utc and sunset_utc:
            sunrise_time_local = datetime.strptime(f"{current_day_month} {sunrise_utc}", "%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(local_tz)
            sunset_time_local = datetime.strptime(f"{current_day_month} {sunset_utc}", "%m-%d %H:%M").replace(tzinfo=timezone.utc).astimezone(local_tz)

            logging.info(f"Sunrise time local: {sunrise_time_local}, Sunset time local: {sunset_time_local}")

            if current_time_local > sunset_time_local:
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
