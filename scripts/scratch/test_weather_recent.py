import requests

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 18.5204,
    "longitude": 73.8567,
    "start_date": "2025-01-01",
    "end_date": "2026-10-20",
    "daily": ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "precipitation_sum", "relative_humidity_2m_mean", "wind_speed_10m_max"],
    "timezone": "Asia/Kolkata"
}

resp = requests.get(url, params=params, timeout=30)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    daily = data.get('daily', {})
    print(f"Successfully fetched {len(daily.get('time', []))} daily records!")
    print(f"First date: {daily['time'][0]}, Last date: {daily['time'][-1]}")
else:
    print(resp.status_code, resp.text)
