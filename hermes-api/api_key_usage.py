import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_URL = "https://api.zeussubnet.com/api-keys/usage"
headers = {"Authorization": f"Bearer {API_KEY}"}
latitude = -27.470125
longitude = 153.021072
variable = "2m_dewpoint_temperature"
start_time = "2025-10-26T21:00:00"
end_time = "2025-10-26T22:00:00"
predict_hours = 2


print("Getting API key usage...\n")
response = requests.get(API_URL, headers=headers)

if response.status_code == 200:
    try:
        usage_data = response.json()
        print(usage_data)
    except Exception as e:
        print(f"Error parsing data: {e}")
else:
    print(f"API call failed: {response.text}")