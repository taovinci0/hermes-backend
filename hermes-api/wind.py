import os
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_URL = "https://api.zeussubnet.com/forecast"
headers = {"Authorization": f"Bearer {API_KEY}"}
latitude = -27.470125
longitude = 153.021072
v_variable = "100m_v_component_of_wind"
u_variable = "100m_u_component_of_wind"
start_time = "2025-10-26T21:00:00"
end_time = "2025-10-26T22:00:00"
predict_hours = 2


print("Example 1: Fetching 100m_v_component_of_wind using start_time and end_time")
params = {
    "latitude": latitude, 
    "longitude": longitude, 
    "variable": v_variable, 
    "start_time": start_time, 
    "end_time": end_time
}
response = requests.get(API_URL, headers=headers, params=params).json()
print(response)


print("\nExample 2: Fetching 100m_u_component_of_wind using start_time and predict_hours")
params = {
    "latitude": latitude, 
    "longitude": longitude, 
    "variable": u_variable, 
    "start_time": start_time, 
    "predict_hours": predict_hours
}
response = requests.get(API_URL, headers=headers, params=params).json()
print(response)



print("\nExample 3: Calculating wind speed and direction from 100m_v_component_of_wind and 100m_u_component_of_wind")
# 100m_v_component_of_wind
v_params = {
    "latitude": latitude, 
    "longitude": longitude, 
    "variable": v_variable, 
    "start_time": start_time, 
    "end_time": end_time
}
v_response = requests.get(API_URL, headers=headers, params=v_params).json()
print(f"V response time data: {v_response.get('time', {}).get('data', 'No time data')}")

# 100m_u_component_of_wind
u_params = {
    "latitude": latitude, 
    "longitude": longitude, 
    "variable": u_variable, 
    "start_time": start_time, 
    "end_time": end_time
}
u_response = requests.get(API_URL, headers=headers, params=u_params).json()
print(f"U response time data: {u_response.get('time', {}).get('data', 'No time data')}")

# Calculating wind speed and direction
def degrees_to_compass(degrees):
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = int((degrees + 11.25) / 22.5) % 16
    return directions[index]

v_component = np.array(v_response[v_variable]["data"])
u_component = np.array(u_response[u_variable]["data"])

print(f"V component: {v_component} m/s")
print(f"U component: {u_component} m/s")

wind_speed = np.sqrt(v_component**2 + u_component**2)
wind_direction_degrees = (np.arctan2(u_component, v_component) * 180 / np.pi + 180) % 360
wind_direction_compass = [degrees_to_compass(deg) for deg in wind_direction_degrees]

print(f"Wind speed: {wind_speed} m/s")
print(f"Wind direction: {wind_direction_degrees}° ({wind_direction_compass})")
