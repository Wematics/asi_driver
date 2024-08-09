import csv
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun


def generate_sun_times(location_name, latitude, longitude, delay_minutes):
    location = LocationInfo(location_name, "Earth", "UTC", latitude, longitude)
    sun_times = []

    # Loop over all months and days, including February 29 in leap years
    for month in range(1, 13):
        for day in range(1, 32):
            try:
                # Handle the case of February in both leap and non-leap years
                if month == 2 and day > 29:
                    continue  # Skip invalid days in February
                if month in [4, 6, 9, 11] and day > 30:
                    continue  # Skip invalid days in months with only 30 days
                # Use 2020 as a reference year because it is a leap year
                date = datetime(2020, month, day)
                s = sun(location.observer, date=date, tzinfo="UTC")
                sunrise = s['sunrise'] + timedelta(minutes=delay_minutes)
                sunset = s['sunset'] - timedelta(minutes=delay_minutes)
                sun_times.append([date.strftime("%m-%d"), sunrise.strftime("%H:%M"), sunset.strftime("%H:%M")])
            except ValueError:
                # Skip any invalid dates
                continue

    return sun_times


def save_to_csv(filename, sun_times):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Day", "Sunrise", "Sunset"])
        for sun_time in sun_times:
            writer.writerow(sun_time)


if __name__ == "__main__":
    # Default options
    default_locations = {
        "1": {"name": "Dresden", "latitude": 51.0504, "longitude": 13.7373},
        "2": {"name": "Stanford", "latitude": 37.4275, "longitude": -122.1697}
    }

    # Ask user to select a location or input a custom one
    print("Select a location:")
    print("1. Dresden")
    print("2. Stanford")
    print("3. Enter custom location")
    choice = input("Enter the number corresponding to your choice: ")

    if choice in default_locations:
        location_name = default_locations[choice]["name"]
        latitude = default_locations[choice]["latitude"]
        longitude = default_locations[choice]["longitude"]
    else:
        # User-defined location details
        location_name = input("Enter location name: ")
        latitude = float(input("Enter latitude: "))
        longitude = float(input("Enter longitude: "))

    # User-defined parameters
    delay_minutes = 90

    # Generate sun times based on selected location
    sun_times = generate_sun_times(location_name, latitude, longitude, delay_minutes)

    # Prepare output filename with location and UTC in the name
    output_file = f"sun_times_{location_name.replace(' ', '_')}_UTC.csv"

    # Save the generated sun times to a CSV file
    save_to_csv(output_file, sun_times)
    print(f"Sun times for {location_name} saved to {output_file}")
