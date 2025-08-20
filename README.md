# Home Assistant Uber Ride Tracker

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/yourusername/ha-uber-ride-tracker.svg)](https://github.com/yourusername/ha-uber-ride-tracker/releases)
[![License](https://img.shields.io/github/license/yourusername/ha-uber-ride-tracker)](LICENSE)

A comprehensive Home Assistant integration that provides real-time Uber ride tracking with OAuth authentication, similar to Apple's Live Activities feature.

## 🎯 Features

### Real-Time Ride Tracking
- **Live Status Updates**: Track your ride status in real-time
- **Driver Information**: View driver name, rating, photo, and contact
- **Vehicle Details**: See vehicle make, model, color, and license plate
- **Location Tracking**: Real-time GPS tracking of driver location on map
- **Trip Progress**: Visual progress indicator showing completion percentage
- **Smart Polling**: 10-second updates during active rides, 60 seconds when idle

### Home Assistant Integration
- **OAuth Authentication**: Secure token-based authentication
- **Multiple Entities**: Sensors, binary sensors, and device tracker
- **Service Calls**: Force refresh and ride history retrieval
- **Dashboard Ready**: Example cards and automations included
- **HACS Compatible**: Easy installation via HACS

## 📋 Prerequisites

1. **Uber Developer Account**
   - Sign up at [Uber Developer Dashboard](https://developer.uber.com/)
   - Create a new app
   - Note your Client ID and Client Secret

2. **Home Assistant Requirements**
   - Home Assistant 2024.12.0 or newer
   - HTTPS enabled (required for OAuth)
   - External URL configured

## 🚀 Installation

### Method 1: HACS (Recommended)

1. **Add Custom Repository**:
   - Open HACS in Home Assistant
   - Click three dots menu → Custom repositories
   - Add: `https://github.com/yourusername/ha-uber-ride-tracker`
   - Category: Integration

2. **Install Integration**:
   - Search for "Uber Ride Tracker"
   - Click Install
   - Restart Home Assistant

### Method 2: Manual Installation

1. Download the latest release
2. Copy `custom_components/uber_ride_tracker` to your `custom_components` folder
3. Restart Home Assistant

## ⚙️ Configuration

### Step 1: Uber App Setup

1. Go to [Uber Developer Dashboard](https://developer.uber.com/)
2. Create or edit your app
3. Add OAuth Redirect URI:
   ```
   https://my.home-assistant.io/redirect/oauth
   ```
4. Enable required scopes (if available):
   - profile
   - request
   - request.receipt
   - all_trips
   - ride.request

### Step 2: Home Assistant Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Uber Ride Tracker**
4. Enter your **Client ID** and **Client Secret**
5. Complete OAuth authorization
6. Integration will be configured automatically

## 📊 Entities

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.uber_ride_tracker_ride_status` | Sensor | Main ride status with all attributes |
| `sensor.uber_ride_tracker_ride_progress` | Sensor | Trip completion percentage |
| `sensor.uber_ride_tracker_driver_location` | Sensor | Driver GPS coordinates |
| `binary_sensor.uber_ride_tracker_ride_active` | Binary Sensor | Whether a ride is currently active |
| `device_tracker.uber_ride_tracker_driver` | Device Tracker | Driver location for map tracking |

## 🎨 Dashboard Examples

### Basic Status Card
```yaml
type: entities
title: Uber Ride
entities:
  - entity: sensor.uber_ride_tracker_ride_status
  - entity: sensor.uber_ride_tracker_ride_progress
  - entity: binary_sensor.uber_ride_tracker_ride_active
```

### Map Card
```yaml
type: map
entities:
  - entity: device_tracker.uber_ride_tracker_driver
default_zoom: 14
```

### Conditional Card (Shows only during active ride)
```yaml
type: conditional
conditions:
  - entity: binary_sensor.uber_ride_tracker_ride_active
    state: "on"
card:
  type: markdown
  content: |
    ## 🚗 Active Uber Ride
    **Driver:** {{ state_attr('sensor.uber_ride_tracker_ride_status', 'driver_name') }}
    **Vehicle:** {{ state_attr('sensor.uber_ride_tracker_ride_status', 'vehicle_make') }} {{ state_attr('sensor.uber_ride_tracker_ride_status', 'vehicle_model') }}
    **Progress:** {{ states('sensor.uber_ride_tracker_ride_progress') }}%
```

## 🤖 Automations

### Arrival Notification
```yaml
automation:
  - alias: "Uber Arrival Alert"
    trigger:
      - platform: state
        entity_id: sensor.uber_ride_tracker_ride_status
        to: "arriving"
    action:
      - service: notify.mobile_app
        data:
          title: "Uber is arriving!"
          message: "Your driver is approaching"
```

## 🛠️ Services

### Force Refresh Status
```yaml
service: uber_ride_tracker.refresh_status
```

### Get Ride History
```yaml
service: uber_ride_tracker.get_ride_history
data:
  limit: 10
```

## 📝 Attributes Available

The main sensor provides these attributes:
- `driver_name`, `driver_rating`, `driver_phone`
- `vehicle_make`, `vehicle_model`, `vehicle_color`, `vehicle_license_plate`
- `pickup_address`, `pickup_eta`
- `destination_address`, `destination_eta`
- `fare_estimate`, `surge_multiplier`
- `map_url`, `share_url`

## 🐛 Troubleshooting

### No Data Showing
- Ensure you have an active or recent Uber ride
- Check Home Assistant logs for errors
- Verify OAuth tokens are valid

### Authentication Issues
- Verify Client ID and Secret are correct
- Check redirect URI matches exactly
- Ensure required scopes are enabled

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- Home Assistant Community
- Uber Technologies Inc. for the API
- Contributors and testers

## ⚠️ Disclaimer

This integration is not affiliated with or endorsed by Uber Technologies Inc. Use at your own risk.

## 📧 Support

- [Report Issues](https://github.com/yourusername/ha-uber-ride-tracker/issues)
- [Discussions](https://github.com/yourusername/ha-uber-ride-tracker/discussions)

---

Made with ❤️ for the Home Assistant Community