# Uber Ride Tracker - Setup Guide

## Your Uber App Credentials

Based on your Uber Developer Dashboard:

- **Client ID**: `gyUPRACf08NFEBoEcXTG3-Wa8U3FB-Bf`
- **Client Secret**: `wzo8V7ivmB1DRPbewGiFQtXtl27wDP9T9e3QVYWJ`

## Installation Steps

### 1. Add to HACS

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add your GitHub repository URL
4. Category: **Integration**
5. Click **Add**

### 2. Install Integration

1. In HACS, search for "Uber Ride Tracker"
2. Click **Download**
3. Restart Home Assistant

### 3. Configure Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **"Uber Ride Tracker"**
4. Enter your credentials:
   - Client ID: `gyUPRACf08NFEBoEcXTG3-Wa8U3FB-Bf`
   - Client Secret: `wzo8V7ivmB1DRPbewGiFQtXtl27wDP9T9e3QVYWJ`
5. Click **Submit**
6. You'll be redirected to Uber to authorize
7. Login and grant permissions
8. You'll be redirected back to Home Assistant

## Testing the Integration

### Check Entities
After setup, verify these entities exist:
- `sensor.uber_ride_tracker_ride_status`
- `sensor.uber_ride_tracker_ride_progress`
- `sensor.uber_ride_tracker_driver_location`
- `binary_sensor.uber_ride_tracker_ride_active`
- `device_tracker.uber_ride_tracker_driver`

### Test Without Active Ride
Without an active ride, entities will show:
- Status: "no_active_ride"
- Progress: 0%
- Binary sensor: Off

### Test With Active Ride
1. Request an Uber ride via the Uber app
2. Watch entities update in real-time
3. Check the map for driver location
4. Monitor progress percentage

## Dashboard Setup

Add this card to test:

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Uber Status
    entities:
      - entity: sensor.uber_ride_tracker_ride_status
      - entity: sensor.uber_ride_tracker_ride_progress
      - entity: binary_sensor.uber_ride_tracker_ride_active
  
  - type: conditional
    conditions:
      - entity: binary_sensor.uber_ride_tracker_ride_active
        state: "on"
    card:
      type: map
      entities:
        - device_tracker.uber_ride_tracker_driver
```

## Troubleshooting

### OAuth Error
- Verify redirect URI in Uber app: `https://my.home-assistant.io/redirect/oauth`
- Check external URL is configured in Home Assistant

### No Data
- Normal without active ride
- Request a ride to see real data
- Check logs: Settings → System → Logs

### Token Issues
- Integration auto-refreshes tokens
- If issues persist, remove and re-add integration

## Support

- GitHub Issues: [Report problems](https://github.com/yourusername/ha-uber-ride-tracker/issues)
- Home Assistant Logs: Check for error messages
- Developer Tools → States: Verify entity states