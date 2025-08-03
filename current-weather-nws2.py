#!/usr/bin/env -S uv run -q -s

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
#     "argparse",
#     "pytz"
# ]
# ///

import argparse
import json
import requests
from datetime import datetime
import pytz

degree_sign = u'\N{DEGREE SIGN}'

class NWSManager:
    def __init__(self, latitude, longitude, detail_indent=2):
        self.latitude = latitude
        self.longitude = longitude
        self.detail_indent = detail_indent
        self.leading_spaces = NWSHelpers.get_padded_string(detail_indent)
        self.service_url = 'https://api.weather.gov'
        self.sunrise_sunset_url = 'https://api.sunrise-sunset.org/json?'
        self.get_points_station_info()

    def get_points_station_info(self):
        response = requests.get(
            f"{self.service_url}/points/{self.latitude},{self.longitude}"
        )

        if response.status_code == 200:
            #print (json.dumps(response.json(), indent=4))
            data_object = json.loads(response.text)

            self.gridX = data_object['properties']['gridX']
            self.gridY = data_object['properties']['gridY']
            self.city = data_object['properties']['relativeLocation']['properties']['city']
            self.state = data_object['properties']['relativeLocation']['properties']['state']
            self.wfo = data_object['properties']['gridId']

            response = requests.get(
                f"{self.service_url}/gridpoints/{self.wfo}/{self.gridX},{self.gridY}/stations"
            )

            if response.status_code == 200:
                data_object = json.loads(response.text)

                self.closestStationIdentifier = data_object['features'][0]['properties']['stationIdentifier']
                self.closestStationName = data_object['features'][0]['properties']['name']

                response = requests.get(
                    f"{self.service_url}/stations/{self.closestStationIdentifier}"
                )

                if response.status_code == 200:
                    data_object = json.loads(response.text)
                    self.time_zone = data_object['properties']['timeZone']

    def display_current_conditions(self):
        response = requests.get(
            f"{self.service_url}/stations/{self.closestStationIdentifier}/observations/latest"
        )

        if response.status_code == 200:
            #print (json.dumps(response.json(), indent=4))  # DEBUG ONLY!
            data_object = json.loads(response.text)

            updated_utc = data_object['properties']['timestamp']
            local_update = NWSHelpers.get_local_time(updated_utc, self.time_zone)

            print(f"{self.city}, {self.state}")
            print(f"{self.closestStationName} @ {local_update}")

            current_temperature = NWSHelpers.get_whole_number(
                NWSHelpers.get_fahrenheit_value(
                    data_object['properties']['temperature']['value'],
                    data_object['properties']['temperature']['unitCode']
                )
            )

            feels_like = data_object['properties']['windChill']['value']
            feels_like_unit_code = data_object['properties']['windChill']['unitCode']
            if feels_like == None:
                feels_like = data_object['properties']['heatIndex']['value']
                feels_like_unit_code = data_object['properties']['heatIndex']['unitCode']
            if feels_like == None:
                feels_like = current_temperature
            else:
                feels_like = NWSHelpers.get_whole_number(NWSHelpers.get_fahrenheit_value(feels_like, feels_like_unit_code))

            if current_temperature == feels_like:
                feels_like_description = ""
            else:
                feels_like_description = f" (feels like {feels_like}{degree_sign})"

            relative_humidity = NWSHelpers.get_whole_number(data_object['properties']['relativeHumidity']['value'])
            dew_point = data_object['properties']['dewpoint']['value']
            dew_point_unit_code = data_object['properties']['dewpoint']['unitCode']
            dew_point = NWSHelpers.get_whole_number(NWSHelpers.get_fahrenheit_value(dew_point, dew_point_unit_code))

            wind_speed = data_object['properties']['windSpeed']['value']
            wind_speed_unit_code = data_object['properties']['windSpeed']['unitCode']
            wind_speed = NWSHelpers.get_whole_number(NWSHelpers.get_miles_value(wind_speed, wind_speed_unit_code))

            wind_gust = data_object['properties']['windGust']['value']
            wind_gust_unit_code = data_object['properties']['windGust']['unitCode']
            wind_gust = NWSHelpers.get_whole_number(NWSHelpers.get_miles_value(wind_gust, wind_gust_unit_code))

            wind_direction = data_object['properties']['windDirection']['value']
            #wind_direction_unit_code = data_object['properties']['windDirection']['unitCode']
            wind_direction = NWSHelpers.get_cardinal_direction(wind_direction)

            if wind_speed == "???":
                wind_description = "wind is calm"
            else:
                wind_description = f"wind ({wind_direction}) speed is {wind_speed} mph"
                if wind_gust != "???":
                    wind_description = f"{wind_description}, gusting to {wind_gust} mph"

            print(f"{self.leading_spaces}{current_temperature}{degree_sign}{feels_like_description}")
            NWSHelpers.display_wrapped_text(
                f"{data_object['properties']['textDescription']}",
                f"{self.leading_spaces}"
            )
            #print(f"{self.leading_spaces}{data_object['properties']['textDescription']}")
            print(f"{self.leading_spaces}relative humidity is {relative_humidity}%, dewpoint is {dew_point}{degree_sign}")
            print(f"{self.leading_spaces}{wind_description}")

    def display_separator(self):
        print(f"{self.leading_spaces}-----")

    def display_sunrise_sunset(self):
        response_sr_ss = requests.get(
            f"{self.sunrise_sunset_url}lat={self.latitude}&lng={self.longitude}&tzid={self.time_zone}"
        )

        sunrise = None
        sunset = None
        if response_sr_ss.status_code == 200:
            data_object_sr_sr = json.loads(response_sr_ss.text)
            sunrise = data_object_sr_sr['results']['sunrise']
            sunset = data_object_sr_sr['results']['sunset']

        if sunrise is not None and sunset is not None:
            print(f"{self.leading_spaces}sunrise at {sunrise}, sunset at {sunset}")
        else:
            print(f"{self.leading_spaces}sunrise and sunset data unavailable")

    def display_forecast(self):
        response = requests.get(
            f"{self.service_url}/gridpoints/{self.wfo}/{self.gridX},{self.gridY}/forecast"
        )

        if response.status_code == 200:
            # print (json.dumps(response.json(), indent=4))  # DEBUG ONLY!
            data_object = json.loads(response.text)
            for period in range(0,8):
                name = data_object['properties']['periods'][period]['name']
                temperature = f"{data_object['properties']['periods'][period]['temperature']}{degree_sign}"
                short_forecast = f"{data_object['properties']['periods'][period]['shortForecast']}"
                precip = f"({data_object['properties']['periods'][period]['probabilityOfPrecipitation']['value']}% precip)"
                
                forecast_row = f"{name}: {temperature}, {short_forecast} {precip}"
                
                NWSHelpers.display_wrapped_text(forecast_row, f"{self.leading_spaces}")

class NWSHelpers:
    @staticmethod
    def get_fahrenheit_value(temperature, unit_code):
        if temperature is None:
            return "???"
        else:
            return (temperature * 9/5) + 32 if unit_code == 'wmoUnit:degC' else temperature

    @staticmethod
    def get_miles_value(value, unit_code):
        if value is None:
            return "???"
        else:
            return (value * 0.621371) if unit_code == 'wmoUnit:km_h-1' else value

    @staticmethod
    def get_cardinal_direction(azimuth):
        '''
        Give an azimuth value in degrees, return a cardinal direction, e.g., "NE".
        '''
        if azimuth is None:
            return ""

        if  azimuth < 0 or azimuth > 360:
            raise ValueError("Azimuth must be in the range [0, 360) degrees.")
        
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW", "N"
        ]
        
        index = round(azimuth / 22.5) % 16
    
        return directions[index]


    @staticmethod
    def get_whole_number(input_number):
        try:
            rounded_number = round(input_number, 0)
            formatted_number = f"{rounded_number:.2f}".rstrip('0').rstrip('.')

            return formatted_number
        except:
            return "???"
    
    @staticmethod
    def get_padded_string(length):
        return ' ' * length

    @staticmethod
    def get_local_time(utc_time_str, local_tz):
        utc_time = datetime.fromisoformat(utc_time_str)

        local_tz = pytz.timezone(local_tz)

        local_time = utc_time.astimezone(local_tz)

        time_in_am_pm = local_time.strftime("%I:%M %p")

        return time_in_am_pm

    @staticmethod
    def display_wrapped_text(input_string, prefix_padding, max_width=50):
        result = []
        
        while len(input_string) > 0:
            if len(input_string) > max_width:
                last_space_index = input_string.rfind(' ', 0, max_width)
                if last_space_index == -1:
                    last_space_index = max_width
                result.append(input_string[:last_space_index])
                input_string = input_string[last_space_index:].lstrip()
            else:
                result.append(input_string)
                break
                
        for i in range(1, len(result)):
            result[i] = f"{prefix_padding}{result[i]}"

        for item in result:
            print(f"{prefix_padding}{item}")

def main():
    parser = argparse.ArgumentParser(description='A simple argument parser example.')
    parser.add_argument('--latitude', type=float, help='Your latitude, e.g. 39.6142', required=True)
    parser.add_argument('--longitude', type=float, help='Your longitude, e.g. -84.5560', required=True)
    args = parser.parse_args()

    nws_mgr = NWSManager(args.latitude, args.longitude)
    nws_mgr.display_current_conditions()
    nws_mgr.display_sunrise_sunset()
    nws_mgr.display_separator()
    nws_mgr.display_forecast()


if __name__ == "__main__":
    main()
