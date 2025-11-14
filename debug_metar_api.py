#!/usr/bin/env python3
"""Debug script to see raw METAR API response."""

import requests
from datetime import date, datetime

def main():
    """Check what the API actually returns."""
    
    api_base = "https://aviationweather.gov/api/data/metar"
    station = "EGLC"
    target_date = date(2025, 11, 12)
    
    # Try different date ranges
    start_time = datetime.combine(target_date, datetime.min.time())
    end_time = start_time.replace(hour=23, minute=59, second=59)
    
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    params = {
        "ids": station,
        "start": start_str,
        "end": end_str,
        "format": "json"
    }
    
    print(f"API Call:")
    print(f"  URL: {api_base}")
    print(f"  Params: {params}")
    print()
    
    headers = {"User-Agent": "HermesTradingSystem/1.0"}
    
    try:
        response = requests.get(api_base, params=params, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            print(f"Response Length: {len(data) if isinstance(data, list) else 'N/A'}")
            print()
            
            if isinstance(data, list) and data:
                print(f"First observation fields: {list(data[0].keys())}")
                print()
                print("First observation:")
                import json
                print(json.dumps(data[0], indent=2, default=str))
                print()
                
                if len(data) > 1:
                    print(f"Total observations: {len(data)}")
                    print(f"Last observation time: {data[-1].get('obsTime') or data[-1].get('time')}")
        elif response.status_code == 204:
            print("204 No Content - No data available for this date range")
        else:
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

