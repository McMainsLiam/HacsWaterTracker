"""Constants for the Plano Water integration."""

DOMAIN = "plano_water"

# Default values
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds
DEFAULT_TIMEOUT = 30

# URLs
BASE_URL = "https://cus.plano.gov"
LOGIN_URL = f"{BASE_URL}/Account/Login"
ACCOUNT_SUMMARY_URL = f"{BASE_URL}/AccountSummary"
METER_READS_URL = f"{BASE_URL}/MeterReads.aspx/GetBillHistory"

# Configuration keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_ACCOUNT_NUMBER = "account_number"

# Sensor types
SENSOR_TYPES = {
    "current_usage": {
        "name": "Current Hour Usage",
        "unit": "gal",
        "icon": "mdi:water",
        "device_class": None,
        "state_class": "measurement",
    },
    "daily_usage": {
        "name": "Daily Usage",
        "unit": "gal", 
        "icon": "mdi:water-pump",
        "device_class": None,
        "state_class": "total_increasing",
    },
    "last_reading": {
        "name": "Last Reading Time",
        "unit": None,
        "icon": "mdi:clock",
        "device_class": "timestamp",
        "state_class": None,
    },
}