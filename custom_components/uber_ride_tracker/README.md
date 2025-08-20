# Uber Ride Tracker for Home Assistant

A comprehensive Home Assistant integration that provides real-time Uber ride tracking with OAuth authentication, similar to Apple's Live Activities feature.

## Features

### Real-Time Ride Tracking
- **Live Status Updates**: Track your ride status (processing, accepted, arriving, in_progress, completed)
- **Driver Information**: View driver name, rating, photo, and contact information
- **Vehicle Details**: See vehicle make, model, color, and license plate
- **Location Tracking**: Real-time GPS tracking of driver location on map
- **Trip Progress**: Visual progress indicator showing trip completion percentage
- **ETA Updates**: Pickup and destination ETA with real-time updates
- **Fare Estimates**: Current fare estimate for your ride

### Smart Update Intervals
- **Active Ride**: Updates every 10 seconds when ride is active
- **No Active Ride**: Updates every 60 seconds when idle
- **Error Recovery**: Extends to 5 minutes on repeated errors

### Entities Created
- `sensor.uber_ride_tracker_ride_status` - Main ride status with all attributes
- `sensor.uber_ride_tracker_ride_progress` - Trip completion percentage
- `sensor.uber_ride_tracker_driver_location` - Driver GPS coordinates
- `binary_sensor.uber_ride_tracker_ride_active` - Whether a ride is currently active
- `device_tracker.uber_ride_tracker_driver` - Driver location for map tracking

### Services
- `uber_ride_tracker.refresh_status` - Force refresh current ride status
- `uber_ride_tracker.get_ride_history` - Retrieve recent ride history

## Prerequisites

1. **Uber Developer Account**
   - Sign up at [Uber Developer Dashboard](https://developer.uber.com/)
   - Create a new app
   - Note your Client ID and Client Secret

2. **Home Assistant Requirements**
   - Home Assistant 2024.12.0 or newer
   - HTTPS enabled (required for OAuth)
   - External URL configured in Home Assistant

## Installation

### HACS Installation (Recommended)
1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add repository URL: `https://github.com/yourusername/ha-uber-ride-tracker`
5. Select category: "Integration"
6. Click "Add"
7. Search for "Uber Ride Tracker" and install
8. Restart Home Assistant

### Manual Installation
1. Copy the `uber_ride_tracker` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

### Step 1: Uber App Setup
1. Go to [Uber Developer Dashboard](https://developer.uber.com/)
2. Click "Create App"
3. Fill in app details:
   - App Name: "Home Assistant Ride Tracker"
   - Description: "Personal ride tracking for Home Assistant"
4. Add OAuth Redirect URI:
   - `https://my.home-assistant.io/redirect/oauth`
   - Or your custom redirect URL if using a different setup
5. Select required scopes:
   - `profile`
   - `request`
   - `request.receipt`
   - `all_trips`
   - `ride.request`
6. Save your Client ID and Client Secret

### Step 2: Home Assistant Setup
1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Uber Ride Tracker"
4. Enter your Client ID and Client Secret
5. Click "Submit"
6. You'll be redirected to Uber to authorize the app
7. Grant the requested permissions
8. You'll be redirected back to Home Assistant
9. The integration will be configured automatically

## Dashboard Setup

### Basic Card
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

### Advanced Dashboard
See [dashboard_example.yaml](dashboard_example.yaml) for comprehensive dashboard examples including:
- Conditional cards that show only during active rides
- Progress bars and gauges
- Driver information cards
- Custom button cards for services
- Mushroom card examples
- Automation examples

## Automations

### Arrival Notification
```yaml
automation:
  - alias: "Uber Arrival Notification"
    trigger:
      - platform: state
        entity_id: sensor.uber_ride_tracker_ride_status
        to: "arriving"
    action:
      - service: notify.mobile_app
        data:
          title: "Uber is arriving!"
          message: "Your driver is approaching the pickup location."
```

### Porch Light Automation
```yaml
automation:
  - alias: "Turn on porch light for Uber"
    trigger:
      - platform: state
        entity_id: sensor.uber_ride_tracker_ride_status
        to: "arriving"
    condition:
      - condition: sun
        after: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.porch
```

## Attributes Available

### Ride Status Sensor Attributes
- `status` - Current ride status
- `trip_id` - Unique ride identifier
- `driver_name` - Driver's name
- `driver_rating` - Driver rating (1-5)
- `driver_phone` - Driver phone number
- `driver_photo_url` - URL to driver's photo
- `vehicle_make` - Vehicle manufacturer
- `vehicle_model` - Vehicle model
- `vehicle_color` - Vehicle color
- `vehicle_license_plate` - License plate number
- `pickup_address` - Pickup location address
- `pickup_eta` - Estimated pickup time
- `destination_address` - Destination address
- `destination_eta` - Estimated arrival time
- `fare_estimate` - Current fare estimate
- `surge_multiplier` - Surge pricing multiplier
- `map_url` - URL to track ride on Uber website
- `share_url` - URL to share ride status

## Troubleshooting

### Authentication Issues
- **Token Expired**: The integration will automatically refresh tokens
- **Invalid Credentials**: Double-check your Client ID and Secret
- **Permission Denied**: Ensure all required scopes are enabled in your Uber app

### No Data Showing
- Check that you have an active or recent Uber ride
- Use the `uber_ride_tracker.refresh_status` service to force an update
- Check Home Assistant logs for any error messages

### Rate Limiting
- The integration respects Uber's rate limits (2000 calls/hour)
- If rate limited, the integration will automatically back off
- Update intervals adjust based on ride status to minimize API calls

### Common Issues

1. **"No active ride" status**
   - This is normal when you don't have an active Uber ride
   - The integration will automatically detect when a new ride starts

2. **Location not updating**
   - Driver location only updates during active rides
   - Ensure location permissions are granted in the Uber app

3. **Missing attributes**
   - Some attributes are only available during certain ride states
   - Driver information is only available after ride is accepted

## API Limitations

- **Rate Limits**: 2000 API calls per hour
- **Data Availability**: Some data only available during active rides
- **Historical Data**: Limited to recent trip history
- **Real-time Updates**: Polling-based (not WebSocket)

## Security Considerations

- OAuth tokens are stored securely in Home Assistant's credential storage
- Never share your Client ID or Client Secret
- Use HTTPS for your Home Assistant instance
- Tokens are automatically refreshed before expiration
- No sensitive data is logged

## Support

### Getting Help
- Check the [Issues](https://github.com/yourusername/ha-uber-ride-tracker/issues) page
- Enable debug logging for detailed information:
  ```yaml
  logger:
    logs:
      custom_components.uber_ride_tracker: debug
  ```

### Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

### Feature Requests
Open an issue with the "enhancement" label to request new features.

## Advanced Configuration

### Custom Update Intervals
While not exposed in the UI, you can modify update intervals by editing the constants in `const.py`:
- `UPDATE_INTERVAL_ACTIVE`: Default 10 seconds
- `UPDATE_INTERVAL_INACTIVE`: Default 60 seconds
- `UPDATE_INTERVAL_ERROR`: Default 300 seconds

### Multiple Accounts
Currently, the integration supports one Uber account per Home Assistant instance. Multi-account support is planned for future releases.

## Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Uber Eats order tracking
- [ ] Multi-account support
- [ ] Trip analytics and statistics
- [ ] Cost tracking and budgeting
- [ ] Integration with calendar for scheduled rides
- [ ] Support for Uber for Business accounts

## License

This integration is provided as-is under the MIT License. It is not affiliated with or endorsed by Uber Technologies Inc.

## Acknowledgments

- Home Assistant Community for testing and feedback
- Uber for providing the Riders API
- Contributors and maintainers

---

**Note**: This integration requires an active Uber account and only tracks rides initiated through the Uber app. It cannot book rides or modify existing bookings.