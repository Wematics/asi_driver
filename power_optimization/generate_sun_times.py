#pip install astral
import csv
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun

def generate_sun_times(location_name, latitude, longitude, start_year, years_ahead):
    location = LocationInfo(location_name, "Earth", "UTC", latitude, longitude)
    sun_times = []

    for year in range(start_year, start_year + years_ahead):
        for month in range(1, 13):
            date = datetime(year, month, 15)  # Using 15th as representative for the month
            s = sun(location.observer, date=date, tzinfo="UTC")
            sunrise = s['sunrise'] + timedelta(minutes=90)
            sunset = s['sunset'] - timedelta(minutes=90)
            sun_times.append([date.strftime("%Y-%m"), sunrise.strftime("%H:%M"), sunset.strftime("%H:%M")])

    return sun_times

def save_to_csv(filename, sun_times):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Month", "90 min after Sunrise", "90 min before Sunset"])
        for sun_time in sun_times:
            writer.writerow(sun_time)

if __name__ == "__main__":
    # Parameters for Dresden
    location_name_dresden = "Dresden"
    latitude_dresden = 51.0504
    longitude_dresden = 13.7373
    start_year = 2024
    years_ahead = 10
    output_file_dresden = "sun_times_dresden.csv"

    # Generate and save sun times for Dresden
    sun_times_dresden = generate_sun_times(location_name_dresden, latitude_dresden, longitude_dresden, start_year, years_ahead)
    save_to_csv(output_file_dresden, sun_times_dresden)
    print(f"Sun times for Dresden saved to {output_file_dresden}")

    # Parameters for Stanford
    location_name_stanford = "Stanford"
    latitude_stanford = 37.4275
    longitude_stanford = -122.1697
    output_file_stanford = "sun_times_stanford.csv"

    # Generate and save sun times for Stanford
    sun_times_stanford = generate_sun_times(location_name_stanford, latitude_stanford, longitude_stanford, start_year, years_ahead)
    save_to_csv(output_file_stanford, sun_times_stanford)
    print(f"Sun times for Stanford saved to {output_file_stanford}")
