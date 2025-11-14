# Hermes Snapshotter - Troubleshooting Guide

## Zeus API 401 Unauthorized Error

### Problem
Getting `401 Unauthorized` error when calling Zeus API.

### Common Causes

1. **API key not set in `.env` file**
2. **API key format incorrect**
3. **`.env` file not being loaded**
4. **API key expired or invalid**

### Solution Steps

#### Step 1: Verify `.env` file exists and has correct format

Check that you have a `.env` file in the project root:

```bash
cd hermes-snapshotter
ls -la .env
```

The `.env` file should look like:

```bash
ZEUS_API_KEY=your_actual_api_key_here
ZEUS_API_BASE=https://api.zeussubnet.com
```

**Important**: 
- No quotes around the API key value
- No spaces around the `=` sign
- Make sure the API key is the actual key, not "your_zeus_api_key_here"

#### Step 2: Verify API key is being loaded

Add this debug script to test:

**File: `test_config.py`**
```python
#!/usr/bin/env python3
"""Test configuration loading."""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env
load_dotenv()

print("=" * 70)
print("Configuration Test")
print("=" * 70)

# Check if .env file exists
env_path = Path(".env")
print(f"\n.env file exists: {env_path.exists()}")
if env_path.exists():
    print(f".env file path: {env_path.absolute()}")

# Check environment variables
zeus_key = os.getenv("ZEUS_API_KEY")
zeus_base = os.getenv("ZEUS_API_BASE", "https://api.zeussubnet.com")

print(f"\nZEUS_API_KEY loaded: {zeus_key is not None}")
if zeus_key:
    # Show first 10 chars and last 4 chars for security
    masked = f"{zeus_key[:10]}...{zeus_key[-4:]}" if len(zeus_key) > 14 else "***"
    print(f"ZEUS_API_KEY value: {masked} (length: {len(zeus_key)})")
else:
    print("ZEUS_API_KEY: NOT SET")

print(f"ZEUS_API_BASE: {zeus_base}")

# Test config loading
try:
    from core.config import config
    print(f"\nConfig loaded successfully")
    print(f"Config ZEUS_API_KEY: {config.zeus.api_key[:10] if config.zeus.api_key else 'NOT SET'}...")
    print(f"Config ZEUS_API_BASE: {config.zeus.api_base}")
except Exception as e:
    print(f"\nError loading config: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
```

Run it:
```bash
python test_config.py
```

#### Step 3: Check Zeus API key format

The Zeus API key should be:
- A long string (usually 40+ characters)
- No spaces or special characters that need escaping
- Should start with something like a token prefix (varies by provider)

#### Step 4: Verify API key works

Test the API key directly:

**File: `test_zeus_api.py`**
```python
#!/usr/bin/env python3
"""Test Zeus API directly."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ZEUS_API_KEY")
api_base = os.getenv("ZEUS_API_BASE", "https://api.zeussubnet.com")

if not api_key:
    print("ERROR: ZEUS_API_KEY not set in .env")
    exit(1)

print(f"Testing Zeus API with key: {api_key[:10]}...{api_key[-4:]}")
print(f"API Base: {api_base}")

# Test API call
url = f"{api_base}/forecast"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

params = {
    "latitude": 51.505,
    "longitude": 0.05,
    "variable": "2m_temperature",
    "start_time": "2025-11-13T00:00:00Z",
    "predict_hours": 24,
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 401:
        print("❌ 401 Unauthorized - API key is invalid or expired")
        print(f"Response: {response.text[:200]}")
    elif response.status_code == 200:
        print("✅ API key is valid!")
        data = response.json()
        print(f"Response keys: {list(data.keys())[:5]}")
    else:
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"Error: {e}")
```

Run it:
```bash
python test_zeus_api.py
```

#### Step 5: Common Fixes

**Fix 1: Ensure .env is in project root**
```bash
# Make sure you're in the project root
cd hermes-snapshotter
pwd  # Should show .../hermes-snapshotter

# Check .env exists
ls -la .env
```

**Fix 2: Remove quotes from .env**
```bash
# WRONG:
ZEUS_API_KEY="your_key_here"

# CORRECT:
ZEUS_API_KEY=your_key_here
```

**Fix 3: Check for hidden characters**
```bash
# View .env file (shows hidden characters)
cat -A .env

# Should see:
# ZEUS_API_KEY=actual_key_here$
# (no quotes, no spaces)
```

**Fix 4: Reload environment**
```bash
# If running in terminal, restart it
# Or explicitly reload:
source venv/bin/activate  # Re-activate venv
python run_snapshotter.py
```

**Fix 5: Check API key from source**
- Verify the API key is correct in your Zeus account
- Some APIs require the key to be activated first
- Check if the key has expired

### Debug Mode

Enable debug logging to see what's happening:

**In `.env`:**
```bash
LOG_LEVEL=DEBUG
```

This will show:
- Whether the API key is being loaded
- The exact API request being made
- The full error response

### Still Not Working?

1. **Double-check the API key** - Copy it fresh from your Zeus account
2. **Check API documentation** - Verify the authentication method hasn't changed
3. **Test with curl**:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        "https://api.zeussubnet.com/forecast?latitude=51.505&longitude=0.05&variable=2m_temperature&start_time=2025-11-13T00:00:00Z&predict_hours=24"
   ```

4. **Check for API key prefix** - Some APIs require a prefix like `sk-` or `pk-`

### Quick Checklist

- [ ] `.env` file exists in project root
- [ ] `ZEUS_API_KEY` is set in `.env` (no quotes)
- [ ] API key is the actual key (not placeholder text)
- [ ] No extra spaces in `.env` file
- [ ] Virtual environment is activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] API key is valid and not expired
- [ ] API base URL is correct

---

## Other Common Issues

### Issue: ModuleNotFoundError

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Permission denied on data directory

**Solution**: Create directories with proper permissions
```bash
mkdir -p data/snapshots/dynamic/{zeus,polymarket,metar}
chmod -R 755 data/
```

### Issue: METAR API rate limiting

**Solution**: This is normal. The retry logic will handle it. If persistent, increase retry delays in `venues/metar/metar_service.py`.

---

**Last Updated**: November 13, 2025

