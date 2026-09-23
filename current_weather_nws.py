#!/usr/bin/env -S uv run -q -s

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
#     "argparse",
#     "pytz",
#     "rich"
# ]
# ///

import argparse
import json
import os
from datetime import datetime

import pytz
import requests
from rich.console import Console
from rich.table import Table

degree_sign = "\N{DEGREE SIGN}"


class NWSManager:
    def __init__(
        self,
        latitude,
        longitude,
        stationid,
        max_width,
        detail_count,
        alert_count,
        alert_detail,
        alert_expiration,
        show_header,
        detail_indent=2,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.stationid = stationid
        self.max_width = max_width
        self.detail_count = detail_count
        self.alert_count = alert_count
        self.alert_detail = alert_detail
        self.alert_expiration = alert_expiration
        self.show_header = show_header
        self.detail_indent = detail_indent
        self.leading_spaces = NWSHelpers.get_padded_string(detail_indent)
        self.service_url = "https://api.weather.gov"
        self.headers = {
            "User-Agent": "current-weather-nws2",
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        self.sunrise_sunset_url = "https://api.sunrise-sunset.org/json?"
        self.get_points_station_info()

        self.current_conditions = ""
        self.sunrise = ""
        self.sunset = ""
        self.immediate_forecast = ""
        self.active_alert_count = 0

    def get_points_station_info(self):
        response = requests.get(
            f"{self.service_url}/points/{self.latitude},{self.longitude}",
            headers=self.headers,
        )

        if response.status_code == 200:
            # print (json.dumps(response.json(), indent=4))
            data_object = json.loads(response.text)

            self.gridX = data_object["properties"]["gridX"]
            self.gridY = data_object["properties"]["gridY"]
            self.city = data_object["properties"]["relativeLocation"]["properties"][
                "city"
            ]
            self.state = data_object["properties"]["relativeLocation"]["properties"][
                "state"
            ]
            self.wfo = data_object["properties"]["gridId"]

            response = requests.get(
                f"{self.service_url}/gridpoints/{self.wfo}/{self.gridX},{self.gridY}/stations",
                headers=self.headers,
            )

            if response.status_code == 200:
                data_object = json.loads(response.text)

                self.closestStationIdentifier = None
                if self.stationid != "NONE":
                    for feature in data_object["features"]:
                        if feature["properties"]["stationIdentifier"] == self.stationid:
                            self.closestStationIdentifier = self.stationid
                            self.closestStationName = feature["properties"]["name"]
                            self.time_zone = feature["properties"]["timeZone"]
                if self.closestStationIdentifier is None:
                    self.closestStationIdentifier = data_object["features"][0][
                        "properties"
                    ]["stationIdentifier"]
                    self.closestStationName = data_object["features"][0]["properties"][
                        "name"
                    ]
                    self.time_zone = data_object["features"][0]["properties"][
                        "timeZone"
                    ]

    def display_current_conditions(self, include_time_in_text_summary=False):
        try:
            response = requests.get(
                f"{self.service_url}/stations/{self.closestStationIdentifier}/observations/latest",
                headers=self.headers,
            )

            if response.status_code == 200:
                # print (json.dumps(response.json(), indent=4))  # DEBUG ONLY!
                data_object = json.loads(response.text)

                updated_utc = data_object["properties"]["timestamp"]
                local_update = NWSHelpers.get_local_time(
                    updated_utc, self.time_zone
                ).lstrip("0")
                self.local_update = local_update

                print(f"{self.city}, {self.state}")
                NWSHelpers.display_wrapped_text(
                    f"{self.closestStationName} @ {local_update}",
                    indent_spaces=self.detail_indent,
                    max_width=self.max_width,
                )

                current_temperature = NWSHelpers.get_whole_number(
                    NWSHelpers.get_fahrenheit_value(
                        data_object["properties"]["temperature"]["value"],
                        data_object["properties"]["temperature"]["unitCode"],
                    )
                )

                feels_like = data_object["properties"]["windChill"]["value"]
                feels_like_unit_code = data_object["properties"]["windChill"][
                    "unitCode"
                ]
                if feels_like is None:
                    feels_like = data_object["properties"]["heatIndex"]["value"]
                    feels_like_unit_code = data_object["properties"]["heatIndex"][
                        "unitCode"
                    ]
                if feels_like is None:
                    feels_like = current_temperature
                else:
                    feels_like = NWSHelpers.get_whole_number(
                        NWSHelpers.get_fahrenheit_value(
                            feels_like, feels_like_unit_code
                        )
                    )

                if current_temperature == feels_like:
                    feels_like_description = ""
                else:
                    feels_like_description = f" (feels like {feels_like}{degree_sign})"

                relative_humidity = NWSHelpers.get_whole_number(
                    data_object["properties"]["relativeHumidity"]["value"]
                )
                dew_point = data_object["properties"]["dewpoint"]["value"]
                dew_point_unit_code = data_object["properties"]["dewpoint"]["unitCode"]
                dew_point = NWSHelpers.get_whole_number(
                    NWSHelpers.get_fahrenheit_value(dew_point, dew_point_unit_code)
                )

                wind_speed = data_object["properties"]["windSpeed"]["value"]
                if wind_speed is not None:
                    wind_speed_unit_code = data_object["properties"]["windSpeed"][
                        "unitCode"
                    ]
                    wind_speed = NWSHelpers.get_whole_number(
                        NWSHelpers.get_miles_value(wind_speed, wind_speed_unit_code)
                    )

                    wind_gust = data_object["properties"]["windGust"]["value"]
                    wind_gust_unit_code = data_object["properties"]["windGust"][
                        "unitCode"
                    ]
                    wind_gust = NWSHelpers.get_whole_number(
                        NWSHelpers.get_miles_value(wind_gust, wind_gust_unit_code)
                    )

                    wind_direction = data_object["properties"]["windDirection"]["value"]
                    # wind_direction_unit_code = data_object['properties']['windDirection']['unitCode']
                    wind_direction = NWSHelpers.get_cardinal_direction(wind_direction)

                if wind_speed is None:
                    wind_description = "Wind Speed is not available"
                elif wind_speed == "???" or wind_speed == "0":
                    wind_description = "Wind is Calm"
                else:
                    wind_description = (
                        f"Wind ({wind_direction}) Speed is {wind_speed} MPH"
                    )
                    if wind_gust != "???":
                        wind_description = (
                            f"{wind_description}, gusting to {wind_gust} MPH"
                        )

                condition_summary = (
                    "Current Temperature is not available"
                    if current_temperature == "???"
                    else f"{current_temperature}{degree_sign}{feels_like_description}"
                )
                condition_summary = f"{condition_summary}, {data_object['properties']['textDescription']}"
                NWSHelpers.display_wrapped_text(
                    condition_summary,
                    indent_spaces=self.detail_indent,
                    max_width=self.max_width,
                )

                self.current_conditions = condition_summary
                if include_time_in_text_summary:
                    self.current_conditions = (
                        f"{self.current_conditions} @ {local_update}"
                    )

                NWSHelpers.display_wrapped_text(
                    f"Relative Humidity is {'not available' if relative_humidity == '???' else f'{relative_humidity}%'}, Dewpoint is {'not available' if dew_point == '???' else f'{dew_point}{degree_sign}'}",
                    indent_spaces=self.detail_indent,
                    max_width=self.max_width,
                )

                NWSHelpers.display_wrapped_text(
                    f"{wind_description}",
                    indent_spaces=self.detail_indent,
                    max_width=self.max_width,
                )

        except Exception as ex:
            NWSHelpers.display_wrapped_text(
                f"Error retrieving current conditions: {ex}",
                indent_spaces=self.detail_indent,
                max_width=self.max_width,
            )

    def display_alerts(self):
        try:
            self.active_alert_count = 0

            response = requests.get(
                f"{self.service_url}/alerts/active?point={self.latitude},{self.longitude}",
                headers=self.headers,
            )

            if response.status_code == 200:
                data_object = json.loads(response.text)

                if len(data_object["features"]) > 0:
                    self.display_separator()
                    alert_iteration = 1
                    for feature in data_object["features"]:
                        if alert_iteration > self.alert_count:
                            break
                        self.active_alert_count = self.active_alert_count + 1
                        alert_endtime = feature["properties"]["ends"]
                        if alert_endtime is None:
                            alert_endtime = feature["properties"]["expires"]
                        current_datetime = NWSHelpers.get_current_datetime(
                            self.time_zone
                        )

                        if alert_endtime is None or alert_endtime >= current_datetime:
                            alert_text = f"{feature['properties']['event']}"

                            if self.alert_detail:
                                alert_description = f"{feature['properties']['description'].replace('\n', ' ')[:30]}..."
                                alert_text = f"{alert_text}: {alert_description}"

                            if alert_endtime is not None and self.alert_expiration:
                                alert_text = f"{alert_text} (expires on {NWSHelpers.get_local_day_of_week(alert_endtime, self.time_zone)} at {NWSHelpers.get_local_time(alert_endtime, self.time_zone).lstrip('0')})"

                            NWSHelpers.display_wrapped_text(
                                alert_text,
                                indent_spaces=self.detail_indent,
                                max_width=self.max_width,
                            )

                        alert_iteration = alert_iteration + 1

        except Exception as ex:
            NWSHelpers.display_wrapped_text(
                f"Error retrieving alerts: {ex}",
                indent_spaces=self.detail_indent,
                max_width=self.max_width,
            )

    def display_separator(self, blank_line=True):
        NWSHelpers.display_wrapped_text(
            " " if blank_line else "-" * 10,
            indent_spaces=self.detail_indent,
            max_width=self.max_width,
        )

    def display_sunrise_sunset(self):
        sunrise = None
        sunset = None

        try:
            response_sr_ss = requests.get(
                f"{self.sunrise_sunset_url}lat={self.latitude}&lng={self.longitude}&tzid={self.time_zone}",
                headers=self.headers,
            )

            day_length = None
            if response_sr_ss.status_code == 200:
                data_object_sr_sr = json.loads(response_sr_ss.text)
                sunrise = data_object_sr_sr["results"]["sunrise"]
                sunset = data_object_sr_sr["results"]["sunset"]
                day_length = data_object_sr_sr["results"]["day_length"]
                if sunrise.count(":") > 1:
                    last_colon_index = sunrise.rfind(":")
                    sunrise = (
                        sunrise[:last_colon_index] + sunrise[last_colon_index + 3 :]
                    )
                if sunset.count(":") > 1:
                    last_colon_index = sunset.rfind(":")
                    sunset = sunset[:last_colon_index] + sunset[last_colon_index + 3 :]
                if day_length.count(":") > 1:
                    last_colon_index = day_length.rfind(":")
                    day_length = (
                        day_length[:last_colon_index]
                        + day_length[last_colon_index + 3 :]
                    )

            if sunrise is not None and sunset is not None:
                self.sunrise = sunrise
                self.sunset = sunset

                NWSHelpers.display_wrapped_text(
                    f"Sun rise/set, daylight: {sunrise}/{sunset}, {day_length}",
                    indent_spaces=self.detail_indent,
                    max_width=self.max_width,
                )
            else:
                self.sunrise = ""
                self.sunset = ""

                NWSHelpers.display_wrapped_text(
                    "Sunrise and Sunset data unavailable",
                    indent_spaces=self.detail_indent,
                    max_width=self.max_width,
                )
        except Exception:
            NWSHelpers.display_wrapped_text(
                "Error retrieving sunrise/sunset times",
                indent_spaces=self.detail_indent,
                max_width=self.max_width,
            )

    def display_hourly(self, display_periods=8, interval=1, show_day=False):
        try:
            response = requests.get(
                f"{self.service_url}/gridpoints/{self.wfo}/{self.gridX},{self.gridY}/forecast/hourly",
                headers=self.headers,
            )
            if response.status_code == 200:
                # print(json.dumps(response.json(), indent=4))  # DEBUG ONLY!
                data_object = json.loads(response.text)

                table = Table(
                    box=None,
                    safe_box=True,
                    show_header=self.show_header,
                    padding=(0, 1),
                    expand=False,
                )

                table.add_column("Time")
                table.add_column("Temp")
                table.add_column("Prec")
                table.add_column("Forecast")

                start_item = 0
                for period in data_object["properties"]["periods"]:
                    if not NWSHelpers.is_stale_datetime(
                        period["startTime"], self.time_zone
                    ):
                        break
                    start_item = start_item + 1

                hourly_iteration = 1
                for i in range(
                    start_item, len(data_object["properties"]["periods"]), interval
                ):
                    # for period in data_object["properties"]["periods"]:
                    current_item = data_object["properties"]["periods"][i]
                    if NWSHelpers.is_stale_datetime(
                        current_item["startTime"], self.time_zone
                    ):
                        continue

                    hourly_period_starttime = NWSHelpers.get_formatted_time(
                        current_item["startTime"]
                    )
                    if show_day:
                        hourly_period_starttime = f"{NWSHelpers.get_day_of_week(current_item['startTime'])} {hourly_period_starttime}"

                    hourly_period_temperature = (
                        f"{current_item['temperature']}{degree_sign}"
                    )
                    hourly_period_precip = (
                        f"{current_item['probabilityOfPrecipitation']['value']}%"
                    )
                    hourly_period_short_forecast = f"{current_item['shortForecast']}"

                    table.add_row(
                        hourly_period_starttime,
                        hourly_period_temperature,
                        hourly_period_precip,
                        hourly_period_short_forecast,
                    )

                    if hourly_iteration == display_periods:
                        break
                    hourly_iteration = hourly_iteration + 1

                console = Console()
                console.print(table, width=self.max_width)

        except Exception as ex:
            NWSHelpers.display_wrapped_text(
                f"Error retrieving forecast: {ex}",
                indent_spaces=self.detail_indent,
                max_width=self.max_width,
            )

    def display_forecast(self, forecast_count=8):
        try:
            response = requests.get(
                f"{self.service_url}/gridpoints/{self.wfo}/{self.gridX},{self.gridY}/forecast",
                headers=self.headers,
            )

            if response.status_code == 200:
                # print (json.dumps(response.json(), indent=4))  # DEBUG ONLY!
                data_object = json.loads(response.text)

                table = Table(
                    box=None,
                    safe_box=True,
                    show_header=self.show_header,
                    padding=(0, 1),
                    expand=False,
                )

                table.add_column("When")
                table.add_column("Temp")
                table.add_column("Prec")
                table.add_column("Forecast")

                forecast_iteration = 1
                self.immediate_forecast = ""
                for period in data_object["properties"]["periods"]:
                    forecast_period_endtime = period["endTime"]
                    current_datetime = NWSHelpers.get_current_datetime(self.time_zone)
                    if forecast_period_endtime >= current_datetime:
                        name = period["name"]
                        temperature = f"{period['temperature']}{degree_sign}"
                        if forecast_iteration <= self.detail_count:
                            short_forecast = f"{period['detailedForecast']}"
                        else:
                            short_forecast = f"{period['shortForecast']}"
                        precip = f"{period['probabilityOfPrecipitation']['value']}%"
                        if forecast_iteration in (1, 2, 3):
                            self.immediate_forecast = f"{self.immediate_forecast}{name}: {temperature}, {period['shortForecast']} ({precip})\n"

                        table.add_row(name, temperature, precip, short_forecast)

                        if forecast_iteration == forecast_count:
                            break
                        forecast_iteration = forecast_iteration + 1
                console = Console()
                console.print(table, width=self.max_width)
        except Exception as ex:
            NWSHelpers.display_wrapped_text(
                f"Error retrieving forecast: {ex}",
                indent_spaces=self.detail_indent,
                max_width=self.max_width,
            )

    def write_current_weather_summary(self):
        file_path_conditions = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "current_weather_conditions.txt",
        )
        file_path_sun = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "current_weather_sun.txt"
        )
        file_path_forecast = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "current_weather_forecast.txt",
        )

        current_conditions = (
            f"{self.current_conditions.strip().rstrip(',')} @ {self.local_update}"
        )

        current_forecast = self.immediate_forecast

        with open(file_path_conditions, "w") as f:
            output_text = f"{current_conditions}"

            if self.active_alert_count > 0:
                output_text = f"{output_text} {'*' * self.active_alert_count}"

            f.write(output_text)

        if self.sunrise != "" and self.sunset != "":
            with open(file_path_sun, "w") as f:
                output_text = f"Sunrise: {self.sunrise}, Sunset: {self.sunset}"

                f.write(output_text)

        with open(file_path_forecast, "w") as f:
            output_text = f"{current_forecast}"

            f.write(f"{output_text.strip()}")

    def list_stations(self, name_filter=""):
        try:
            next = f"{self.service_url}/stations"

            table = Table(
                width=self.max_width,
                box=None,
                safe_box=True,
                show_header=self.show_header,
            )

            table.add_column("ID")
            table.add_column("Name")
            table.add_column("Time Zone")
            table.add_column("Latitude")
            table.add_column("Longitude")

            reached_last = False

            while next != "":
                response = requests.get(
                    next,
                    headers=self.headers,
                )

                if response.status_code == 200:
                    # print(json.dumps(response.json(), indent=4))  # DEBUG ONLY!
                    data_object = json.loads(response.text)

                    next = data_object["pagination"]["next"]

                    for feature in data_object["features"]:
                        station_identifier = feature["properties"]["stationIdentifier"]
                        feature_name = feature["properties"]["name"]
                        time_zone = feature["properties"]["timeZone"]
                        longitude = feature["geometry"]["coordinates"][0]
                        latitude = feature["geometry"]["coordinates"][1]

                        if name_filter == "" or (
                            name_filter.lower() in feature_name.lower()
                        ):
                            table.add_row(
                                station_identifier,
                                feature_name,
                                time_zone,
                                str(latitude),
                                str(longitude),
                            )

                        if station_identifier == "ZZZI1":
                            reached_last = True

                if reached_last:
                    break

            console = Console()
            console.print(table)

        except Exception as ex:
            NWSHelpers.display_wrapped_text(
                f"Error retrieving station ids: {ex}",
                indent_spaces=self.detail_indent,
                max_width=self.max_width,
            )


class NWSHelpers:
    @staticmethod
    def get_current_datetime(local_tz):
        timezone = pytz.timezone(local_tz)
        current_time = datetime.now(timezone)

        formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S%z")
        formatted_time = formatted_time[:-2] + ":" + formatted_time[-2:]

        return formatted_time

    @staticmethod
    def get_formatted_time(input_time):
        dt = datetime.fromisoformat(input_time)
        formatted_time = (
            dt
            .strftime("%-I%p")
            .lower()
            .replace("am", "am")
            .replace("pm", "pm")
            .replace(" ", "")
        )

        return formatted_time

    @staticmethod
    def get_day_of_week(input_time):
        dt = datetime.fromisoformat(input_time)
        day_of_week = dt.strftime("%a")

        return day_of_week

    @staticmethod
    def is_stale_datetime(input_datetime, local_tz):
        """
        Is the input datetime older than the current datetime?
        """
        timezone = pytz.timezone(local_tz)
        current_dt = datetime.now(timezone)

        input_dt = datetime.fromisoformat(input_datetime)

        return input_dt <= current_dt

    @staticmethod
    def get_fahrenheit_value(temperature, unit_code):
        if temperature is None:
            return "???"
        else:
            return (
                (temperature * 9 / 5) + 32
                if unit_code == "wmoUnit:degC"
                else temperature
            )

    @staticmethod
    def get_miles_value(value, unit_code):
        if value is None:
            return "???"
        else:
            return (value * 0.621371) if unit_code == "wmoUnit:km_h-1" else value

    @staticmethod
    def get_cardinal_direction(azimuth):
        """
        Give an azimuth value in degrees, return a cardinal direction, e.g., "NE".
        """
        if azimuth is None:
            return ""

        if azimuth < 0 or azimuth > 360:
            raise ValueError("Azimuth must be in the range [0, 360) degrees.")

        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
            "N",
        ]

        index = round(azimuth / 22.5) % 16

        return directions[index]

    @staticmethod
    def get_whole_number(input_number):
        try:
            rounded_number = round(input_number, 0)
            rounded_number = 0 if abs(rounded_number) == 0 else rounded_number
            formatted_number = f"{rounded_number:.2f}".rstrip("0").rstrip(".")

            return formatted_number
        except:  # noqa: E722
            return "???"

    @staticmethod
    def get_padded_string(length):
        return " " * length

    @staticmethod
    def get_local_day_of_week(utc_time_str, local_tz):
        utc_time = datetime.fromisoformat(utc_time_str)

        local_tz = pytz.timezone(local_tz)

        local_time = utc_time.astimezone(local_tz)

        day_of_week = local_time.strftime("%A")

        return day_of_week

    @staticmethod
    def get_local_time(utc_time_str, local_tz):
        utc_time = datetime.fromisoformat(utc_time_str)

        local_tz = pytz.timezone(local_tz)

        local_time = utc_time.astimezone(local_tz)

        time_in_am_pm = local_time.strftime("%I:%M %p")

        return time_in_am_pm

    @staticmethod
    def display_wrapped_text(input_string, indent_spaces=2, max_width=55):
        result = []

        while len(input_string) > 0:
            if len(input_string) > max_width:
                last_space_index = input_string.rfind(" ", 0, max_width)
                if last_space_index == -1:
                    last_space_index = max_width
                result.append(input_string[:last_space_index])
                input_string = input_string[last_space_index:].lstrip()
            else:
                result.append(input_string)
                break

        for i in range(1, len(result)):
            result[i] = f"{NWSHelpers.get_padded_string(indent_spaces)}{result[i]}"

        for item in result:
            print(f"{NWSHelpers.get_padded_string(indent_spaces)}{item}")


def main():
    parser = argparse.ArgumentParser(description="A simple argument parser example.")
    parser.add_argument(
        "--latitude", type=float, help="Your latitude, e.g. 39.6142", default=999
    )
    parser.add_argument(
        "--longitude", type=float, help="Your longitude, e.g. -84.5560", default=999
    )
    parser.add_argument(
        "--stationid",
        type=str,
        help='Specific station id to use, e.g., "KGMY"',
        default="NONE",
    )
    parser.add_argument(
        "--maxwidth",
        type=int,
        help="Maximum character width of displayed text. Default is 120.",
        default=120,
    )
    parser.add_argument(
        "--forecastcount",
        type=int,
        help="Forecast periods to show. Default is 8.",
        default=8,
    )
    parser.add_argument(
        "--detailcount",
        type=int,
        help="Periods of detailed forecast to show.",
        default=0,
    )
    parser.add_argument(
        "--alertcount",
        type=int,
        help="Maximum number of alerts to show. Default is 99 (all)",
        default=99,
    )
    parser.add_argument(
        "--alertdetail",
        action="store_true",
        help="Show alert details",
        default=False,
    )
    parser.add_argument(
        "--alertexpiration",
        action="store_true",
        help="Show alert expiration date",
        default=False,
    )
    parser.add_argument(
        "--hourlycount",
        type=int,
        help="Number of hourly periods to show for hourly forecast.",
        default=0,
    )
    parser.add_argument(
        "--hourlyinterval",
        type=int,
        help="Show every # period for hourly forecast.",
        default=1,
    )
    parser.add_argument(
        "--hourlyshowday",
        action="store_true",
        help="Show day of week with hourly conditions.",
        default=False,
    )

    parser.add_argument(
        "--stations",
        action="store_true",
        help="List station IDs. (WARNING: This is SLOW!)",
        default=False,
    )
    parser.add_argument(
        "--stationfilter",
        type=str,
        help="Filter station ID list by name value. Case-insensitive.",
        default="",
    )
    parser.add_argument(
        "--showheader",
        action="store_true",
        help="Show column headers in tables.",
    )
    parser.add_argument(
        "--indent", type=int, help="Number of spaces to indent wrapped text", default=2
    )
    args = parser.parse_args()

    nws_mgr = NWSManager(
        args.latitude,
        args.longitude,
        args.stationid,
        args.maxwidth,
        args.detailcount,
        args.alertcount,
        args.alertdetail,
        args.alertexpiration,
        args.showheader,
        args.indent,
    )
    if args.stations:
        nws_mgr.list_stations(args.stationfilter)
    else:
        if args.latitude == 999 or args.longitude == 999:
            print("Latitude and Longitude are required")
        else:
            nws_mgr.display_current_conditions()
            nws_mgr.display_sunrise_sunset()
            nws_mgr.display_alerts()
            nws_mgr.display_separator()
            if args.hourlycount > 0:
                nws_mgr.display_hourly(
                    args.hourlycount, args.hourlyinterval, args.hourlyshowday
                )
                nws_mgr.display_separator()
            nws_mgr.display_forecast(args.forecastcount)
            nws_mgr.write_current_weather_summary()


if __name__ == "__main__":
    main()
