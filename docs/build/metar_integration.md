# 📡 AviationWeather.gov METAR API – Integration Report

**Version:** v4.5 (as of November 2025)

**Source:** [https://aviationweather.gov/data/api/](https://aviationweather.gov/data/api/)

---

## 1. Overview

The **Aviation Weather Center (AWC)** provides a REST-based Data API to retrieve worldwide aviation weather datasets, including **METAR**, **TAF**, **SIGMET**, and related products.

This report summarizes all relevant information needed to integrate METAR data into the Zeus backend system — including endpoint specifications, parameters, schema, limits, error handling, and example usage.

---

## 2. Base Endpoint

**Primary METAR API:**

```
https://aviationweather.gov/api/data/metar
```

* Supports `GET` requests only.
* Returns **decoded** and optionally **raw** weather observations.
* Replaces all deprecated `/cgi-bin` endpoints.

---

## 3. Query Parameters

| Parameter | Description                                     | Example                      |
| --------- | ----------------------------------------------- | ---------------------------- |
| `ids`     | ICAO station codes (comma-separated)            | `ids=EGLC,KLGA`              |
| `start`   | Start of time range (UTC ISO8601)               | `start=2025-11-08T00:00:00Z` |
| `end`     | End of time range (UTC ISO8601)                 | `end=2025-11-08T23:59:59Z`   |
| `format`  | Output format (`json`, `geojson`, `xml`, `csv`) | `format=json`                |

### Notes

* Time values **must be UTC**.
* **Max window:** 15 days historical data.
* **Max results per query:** 400 records.
* Use time-splitting for full 24-hour retrievals.
* All timestamps returned in **ISO8601 UTC**.

---

## 4. Example API Calls

### Latest METAR for a Station

```
GET https://aviationweather.gov/api/data/metar?ids=KMCI&format=json
```

### All Observations for One UTC Day

```
GET https://aviationweather.gov/api/data/metar?ids=EGLC&start=2025-11-08T00:00:00Z&end=2025-11-08T23:59:59Z&format=json
```

### Chunked Retrieval (for long datasets)

```
GET https://aviationweather.gov/api/data/metar?ids=KLGA&start=2025-11-08T00:00:00Z&end=2025-11-08T12:00:00Z&format=json

GET https://aviationweather.gov/api/data/metar?ids=KLGA&start=2025-11-08T12:00:01Z&end=2025-11-08T23:59:59Z&format=json
```

---

## 5. Response Schema (`METARproperties`)

### Key Fields

| Field       | Type    | Units       | Description                      |
| ----------- | ------- | ----------- | -------------------------------- |
| `station`   | string  | —           | ICAO code (e.g. EGLC)            |
| `time`      | string  | UTC ISO8601 | Observation timestamp            |
| `temp`      | number  | °C          | Air temperature                  |
| `dewpoint`  | number  | °C          | Dew point                        |
| `windDir`   | integer | °           | Wind direction                   |
| `windSpeed` | integer | knots       | Wind speed                       |
| `altim`     | number  | inHg        | Altimeter                        |
| `fltCat`    | string  | —           | Flight category (VFR, IFR, etc.) |
| `rawOb`     | string  | —           | Raw METAR text                   |
| `clouds`    | array   | —           | Cloud layers (added Sept 2025)   |

### Example JSON

```json
{
  "station": "EGLC",
  "time": "2025-11-08T15:50:00Z",
  "temp": 15.0,
  "dewpoint": 11.0,
  "windDir": 220,
  "windSpeed": 10,
  "altim": 30.05,
  "fltCat": "VFR",
  "rawOb": "EGLC 081550Z 22010KT 9999 FEW020 15/11 Q1018"
}
```

### Python Mapping

```python
class MetarObservation(BaseModel):
    station_code: str
    time: datetime
    temp_C: float
    temp_F: float
    raw: Optional[str]
```

---

## 6. Cache Datasets (Bulk Access)

| File                              | Format | Description        | Frequency   |
| --------------------------------- | ------ | ------------------ | ----------- |
| `/data/cache/metars.cache.xml.gz` | XML    | All current METARs | Every 1 min |
| `/data/cache/metars.cache.csv.gz` | CSV    | All current METARs | Every 1 min |

Use these cache files instead of large or frequent API queries.

---

## 7. Rate Limits & Access Rules

| Rule                     | Limit / Note                |
| ------------------------ | --------------------------- |
| Max requests             | 100 per minute (global)     |
| Per-thread limit         | 1 request/minute            |
| Max records per response | 400                         |
| History retention        | 15 days                     |
| CORS                     | Disabled (server-side only) |
| HTTPS                    | Required                    |
| User-Agent               | Must set a custom value     |
| Data updates             | Once per minute             |

Recommended retry: exponential backoff (30–60s) on HTTP 429.

---

## 8. Error Handling

| HTTP Code   | Meaning                          | Typical Cause                    |
| ----------- | -------------------------------- | -------------------------------- |
| **204**     | Valid request, no data available | No METARs for time/station       |
| **400**     | Invalid request                  | Bad parameters or missing fields |
| **404**     | Not found                        | Invalid endpoint or ID           |
| **429**     | Too many requests                | Rate limit exceeded              |
| **500–504** | Server or gateway error          | Temporary issue                  |

---

## 9. Schema & Endpoint Changes (Sept 2025)

| Change                                               | Details                          |
| ---------------------------------------------------- | -------------------------------- |
| `metar_id` removed                                   | Use `station` + `time` instead   |
| `fltCat` added                                       | Indicates flight rules category  |
| `clouds` array added                                 | Replaces individual cloud fields |
| `recent`, `order`, `vfr`, `output`, `filter` removed | No longer valid params           |
| `/cgi-bin` endpoints retired                         | Use `/api/data`                  |
| CSV TAF format discontinued                          | JSON/XML only                    |

---

## 10. Best Practices

* Always include `format=json` unless you need XML.
* Use a **unique User-Agent header** (e.g., `"ZeusWeatherBot/1.0"`).
* Store historical METARs locally if running daily backtests.
* Use the cache datasets for bulk access instead of repeated API calls.
* Implement exponential backoff retry logic for rate limit errors (HTTP 429).
* Split large time ranges into chunks (max 400 records per query).
* Convert temperatures from Celsius to Fahrenheit for consistency with Hermes.
* Handle HTTP 204 (no data) gracefully - it's a valid response, not an error.

---

## 11. Integration with Hermes

### Stage 7D-1: METAR API Integration

This document serves as the reference for implementing the METAR service in `venues/metar/metar_service.py`.

**Key Requirements:**
- Fetch observations for station/date
- Calculate daily high/low temperatures
- Convert Celsius to Fahrenheit
- Handle rate limits and errors
- Support historical data (up to 15 days)
- Cache responses appropriately

**See:** `docs/build/STAGE_7D_SPECIFICATION.md` - Stage 7D-1 for implementation details.

---

**Author**: Hermes Development Team  
**Date**: November 13, 2025  
**Related**: Stage 7D-1 (METAR API Integration)

