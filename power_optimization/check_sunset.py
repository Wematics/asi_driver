#sudo chmod +x check_sunset.py
import csv
from datetime import datetime, timedelta
import subprocess
import logging

# Set up logging
logging.basicConfig(filename='/home/pi/sleep_mode/sleep_wake.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Path to the lookup table
CSV_FILE = "/home/pi/sleep_mode/sun_times_dresden.csv"

MAX_SLEEP_DURATION = 20 * 3600  # 20 hours in seconds

def read_sun_times(csv_file, year_month):
    logging.info(f"Reading sun times for year-month: {year_month}")
    sunrise = sunset = None

    try:
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Month'] == year_month:
                    sunrise = row['Sunrise']
                    sunset = row['Sunset']
                    logging.info(f"Found sunrise: {sunrise}, sunset: {sunset} for month: {year_month}")
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
    logging.info("Shutting down system in 45 seconds")
    subprocess.run(["sleep", "45"])
    try:
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
        logging.info("System shutdown")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to shutdown the system: {e}")

if __name__ == "__main__":
    current_time = datetime.now()
    current_year_month = current_time.strftime("%Y-%m")
    today_date = current_time.strftime("%Y-%m-%d")

    sunrise, sunset = read_sun_times(CSV_FILE, current_year_month)

    if sunrise and sunset:
        sunrise_time = datetime.strptime(f"{today_date} {sunrise}", "%Y-%m-%d %H:%M")
        sunset_time = datetime.strptime(f"{today_date} {sunset}", "%Y-%m-%d %H:%M")

        if current_time > sunset_time:
            next_day = current_time + timedelta(days=1)
            next_year_month = next_day.strftime("%Y-%m")
            next_day_date = next_day.strftime("%Y-%m-%d")

            if next_year_month != current_year_month:
                sunrise_next_day, _ = read_sun_times(CSV_FILE, next_year_month)
                if sunrise_next_day:
                    sunrise_time = datetime.strptime(f"{next_day_date} {sunrise_next_day}", "%Y-%m-%d %H:%M")
                else:
                    logging.error("Sunrise time not found for the next month.")
                    sunrise_time = None
            else:
                sunrise_time = datetime.strptime(f"{next_day_date} {sunrise}", "%Y-%m-%d %H:%M")

            if sunrise_time:
                time_diff = (sunrise_time - current_time).total_seconds()
                if time_diff > MAX_SLEEP_DURATION:
                    time_diff = MAX_SLEEP_DURATION
                    logging.info(f"Sleep duration exceeds 20 hours, setting maximum sleep duration of {MAX_SLEEP_DURATION} seconds.")
                logging.info(f"Current time is past sunset: {sunset_time}. Setting wake time for sunrise.")
                if set_rtc_wake_alarm(int(time_diff)):
                    shutdown_system()
                else:
                    logging.info("Wake-up alarm not set, system will remain on.")
        else:
            logging.info(f"Current time is before sunset: {sunset_time}. System will remain on.")
    else:
        logging.error("Sunrise and sunset times not found for the current month.")
