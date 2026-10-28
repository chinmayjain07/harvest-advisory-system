import requests
import json

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 18.5204,
    "longitude": 73.8567,
    "start_date": "2023-01-01",
    "end_date": "2023-01-05",
    "daily": ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean", "wind_speed_10m_max"],
    "timezone": "Asia/Kolkata"
}

resp = requests.get(url, params=params, timeout=10)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print("Keys:", data.keys())
    print("Daily keys:", data.get('daily', {}).keys())
    print("Sample:", {k: v[:3] for k, v in data.get('daily', {}).items()})
else:
    print(resp.text)
