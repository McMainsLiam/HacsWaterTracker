# Plano Water Usage Home Assistant Integration

A custom Home Assistant integration that pulls water usage data from the City of Plano, TX utility portal (cus.plano.gov) and creates sensors for monitoring your water consumption.

## Features

- **Current Hour Usage**: Shows your most recent hourly water usage
- **Daily Usage**: Aggregated daily water consumption  
- **Last Reading Time**: Timestamp of the last meter reading
- **Automatic Updates**: Polls the portal every hour for new data
- **Device Information**: Creates a device with your account details

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL: `https://github.com/McMainsLiam/HacsWaterTracker`
5. Select "Integration" as the category
6. Click "Add"
7. Find "Plano Water Usage" in HACS and install it
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/plano_water` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Plano Water Usage"
4. Enter your Plano utility portal credentials:
   - **Username**: Your login username for cus.plano.gov
   - **Password**: Your login password
   - **Account Number** (optional): If you have multiple accounts

## Sensors Created

The integration creates the following sensors:

- `sensor.plano_water_current_hour_usage` - Most recent hourly usage in gallons
- `sensor.plano_water_daily_usage` - Total daily usage in gallons  
- `sensor.plano_water_last_reading_time` - Timestamp of last meter reading

## Usage Examples

### Basic Automation - High Usage Alert

```yaml
automation:
  - alias: "High Water Usage Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.plano_water_current_hour_usage
        above: 50  # Alert if using more than 50 gallons in an hour
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "High water usage detected: {{ states('sensor.plano_water_current_hour_usage') }} gallons in the last hour"
```

### Pool/Irrigation Monitoring

```yaml
automation:
  - alias: "Possible Water Leak or Pool Fill"
    trigger:
      - platform: numeric_state
        entity_id: sensor.plano_water_current_hour_usage
        above: 100
        for:
          hours: 2  # Sustained high usage for 2+ hours
    action:
      - service: notify.family
        data:
          message: "Sustained high water usage detected. Check for leaks or running pool equipment."
```

### Daily Usage Tracking

```yaml
automation:
  - alias: "Daily Water Usage Report"
    trigger:
      - platform: time
        at: "23:00:00"  # 11 PM daily
    action:
      - service: notify.mobile_app_your_phone
        data:
          message: "Today's water usage: {{ states('sensor.plano_water_daily_usage') }} gallons"
```

## Troubleshooting

### Login Issues
- Verify your credentials work on the Plano portal website
- Check that your account has access to meter readings
- Ensure 2FA is not enabled (not currently supported)

### No Data
- The Plano portal sometimes has outages (check the green warning banner on their site)
- Try reloading the integration: Settings → Devices & Services → Plano Water → Options → Reload

### Debug Logging

Add this to your `configuration.yaml` to enable debug logging:

```yaml
logger:
  logs:
    custom_components.plano_water: debug
```

## Limitations

- Only works with City of Plano, TX utility accounts
- Requires valid portal credentials
- Data depends on Plano's meter reading schedule (usually hourly)
- Does not support accounts with 2FA enabled

## Contributing

Feel free to submit issues and pull requests to improve this integration!

## License

This project is licensed under the MIT License.