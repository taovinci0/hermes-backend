import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_URL = "https://api.zeussubnet.com/forecast"
headers = {"Authorization": f"Bearer {API_KEY}"}
latitude = -27.470125
longitude = 153.021072
variable = "2m_dewpoint_temperature"
start_time = "2025-10-26T21:00:00"
end_time = "2025-10-26T22:00:00"
predict_hours = 2


print("Example 1: Fetching 2m_dewpoint_temperature using start_time and end_time")
params = {
    "latitude": latitude, 
    "longitude": longitude, 
    "variable": variable, 
    "start_time": start_time, 
    "end_time": end_time
}
response = requests.get(API_URL, headers=headers, params=params).json()
print(response)


print("\nExample 2: Fetching 2m_dewpoint_temperature using start_time and predict_hours")
params = {
    "latitude": latitude, 
    "longitude": longitude, 
    "variable": variable, 
    "start_time": start_time, 
    "predict_hours": predict_hours
}
response = requests.get(API_URL, headers=headers, params=params).json()
print(response)
