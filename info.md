# Uber Ride Tracker for Home Assistant

## Features
- 🚗 Real-time ride tracking with OAuth authentication
- 📍 Live GPS tracking of driver location
- 📊 Trip progress percentage
- 👤 Driver information (name, rating, photo)
- 🚙 Vehicle details (make, model, color, license plate)
- ⏱️ Smart polling (10s active, 60s idle)
- 🗺️ Map integration for location tracking

## Quick Setup

1. **Get Uber API Credentials**:
   - Go to [Uber Developer Dashboard](https://developer.uber.com/)
   - Create an app
   - Add redirect URI: `https://my.home-assistant.io/redirect/oauth`
   - Copy Client ID and Secret

2. **Install via HACS**:
   - Add this repository to HACS
   - Install "Uber Ride Tracker"
   - Restart Home Assistant

3. **Configure Integration**:
   - Settings → Devices & Services → Add Integration
   - Search "Uber Ride Tracker"
   - Enter Client ID and Secret
   - Complete OAuth authorization

## Entities Created
- `sensor.uber_ride_tracker_ride_status` - Main ride status
- `sensor.uber_ride_tracker_ride_progress` - Trip completion %
- `sensor.uber_ride_tracker_driver_location` - GPS coordinates
- `binary_sensor.uber_ride_tracker_ride_active` - Active ride indicator
- `device_tracker.uber_ride_tracker_driver` - Map tracking

## Support
- [Documentation](https://github.com/yourusername/ha-uber-ride-tracker)
- [Issues](https://github.com/yourusername/ha-uber-ride-tracker/issues)