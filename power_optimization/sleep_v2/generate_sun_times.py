import csv
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun

def generate_sun_times(location_name, latitude, longitude, delay_minutes):
    location = LocationInfo(location_name, "Earth", "UTC", latitude, longitude)
    sun_times = []

    for month in range(1, 13):
        for day in range(1, 32):
            try:
                date = datetime(2024, month, day)  # Using a fixed year since only day and month matter
                s = sun(location.observer, date=date, tzinfo="UTC")
                sunrise = s['sunrise'] + timedelta(minutes=delay_minutes)
                sunset = s['sunset'] - timedelta(minutes=delay_minutes)
                sun_times.append([date.strftime("%m-%d"), sunrise.strftime("%H:%M"), sunset.strftime("%H:%M")])
            except ValueError:
                # Handle days that don't exist, e.g., February 30th
                continue

    return sun_times

def save_to_csv(filename, sun_times):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Day", "Sunrise", "Sunset"])
        for sun_time in sun_times:
            writer.writerow(sun_time)

if __name__ == "__main__":
    # User-defined parameters
    delay_minutes = 90

    # Parameters for Dresden
    location_name_dresden = "Dresden"
    latitude_dresden = 51.0504
    longitude_dresden = 13.7373
    output_file_dresden = "sun_times_dresden.csv"

    # Generate and save sun times for Dresden
    sun_times_dresden = generate_sun_times(location_name_dresden, latitude_dresden, longitude_dresden, delay_minutes)
    save_to_csv(output_file_dresden, sun_times_dresden)
    print(f"Sun times for Dresden saved to {output_file_dresden}")

    # Parameters for Stanford
    location_name_stanford = "Stanford"
    latitude_stanford = 37.4275
    longitude_stanford = -122.1697
    output_file_stanford = "sun_times_stanford.csv"

    # Generate and save sun times for Stanford
    sun_times_stanford = generate_sun_times(location_name_stanford, latitude_stanford, longitude_stanford, delay_minutes)
    save_to_csv(output_file_stanford, sun_times_stanford)
    print(f"Sun times for Stanford saved to {output_file_stanford}")

