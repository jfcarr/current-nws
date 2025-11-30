# current-nws

Displays a text summary of recent conditions, along with a forecast. Information comes from the [National Weather Service API](https://www.weather.gov/documentation/services-web-api).

This project requires [uv](https://docs.astral.sh/uv/).

Example:

```bash
uv run current_weather_nws.py --latitude 39.747222 --longitude -84.536389
```

Output (nearest NWS station):

```txt
Richmond Municipal Airport @ 07:35 AM
  54°
  Clear
  relative humidity is 94%, dewpoint is 52°
  wind (NE) speed is 7 mph
  -----
  Overnight: 55°, Mostly Clear (0% precip)
  Sunday: 81°, Sunny (1% precip)
  Sunday Night: 59°, Mostly Clear (0% precip)
  Monday: 83°, Mostly Sunny (7% precip)
  Monday Night: 63°, Mostly Cloudy (11% precip)
  Tuesday: 84°, Partly Sunny then Slight Chance
    Showers And Thunderstorms (23% precip)
  Tuesday Night: 64°, Slight Chance Showers And
    Thunderstorms (23% precip)
  Wednesday: 82°, Slight Chance Rain Showers then
    Chance Showers And Thunderstorms (25% precip)
```
