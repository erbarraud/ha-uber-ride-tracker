# Uber Ride Tracker - Setup Guide

## Prerequisites

1. **Uber Developer Account**: Create one at https://developer.uber.com
2. **Uber App Registration**: Register your app in the Uber Developer Dashboard
3. **Home Assistant**: Accessible via `https://home.erbarraud.com`

## Step 1: Configure Your Uber App

1. Go to https://developer.uber.com/dashboard
2. Select your app "HA Test App"
3. Under **Redirect URIs**, ensure you have:
   ```
   https://home.erbarraud.com/local/uber_callback.html
   ```
4. Note your **Application ID** and **Secret**

## Step 2: Install the Integration

1. Copy the `custom_components/uber_ride_tracker` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to **Settings** → **Devices & Services** → **Add Integration**
4. Search for "Uber Ride Tracker"
5. Enter your:
   - **Application ID**: `g7UPHAGKIBhPE8dEcXTQ3-Wa8UPl1b-elf`
   - **Secret**: (your client secret from Uber dashboard)

## Step 3: Authorize with Uber

### Option A: Using Home Assistant Service

1. Go to **Developer Tools** → **Services**
2. Search for `uber_ride_tracker.test_api_access`
3. Click **Call Service**
4. A notification will appear with an authorization URL
5. Click the URL to authorize with Uber
6. After authorization, copy the code from the callback page
7. Use the `uber_ride_tracker.authorize` service with the code

### Option B: Using Test Script

1. Edit `test_uber_auth.py` and add your CLIENT_SECRET
2. Run:
   ```bash
   python test_uber_auth.py
   ```
3. Follow the URL provided to authorize
4. Run again with the auth code:
   ```bash
   python test_uber_auth.py YOUR_AUTH_CODE
   ```

## Step 4: Verify Setup

1. Call the `uber_ride_tracker.test_api_access` service
2. Check the notification for API access status
3. If successful, you should see:
   - ✅ User Profile
   - ✅ Ride History
   - ✅ Available Products

## Available Services

- `uber_ride_tracker.authorize` - Complete OAuth authorization
- `uber_ride_tracker.test_api_access` - Test API connectivity
- `uber_ride_tracker.get_ride_history` - Get recent rides
- `uber_ride_tracker.check_current_ride` - Check for active ride
- `uber_ride_tracker.setup_callback` - Manually setup callback page

## Troubleshooting

### "Invalid Scope" Error
- The integration requests basic scopes: `profile history`
- For privileged scopes (like `request`), you need Full Access from Uber

### "Unauthorized" Error
- Your token may have expired
- Re-run the authorization process

### Callback Page Not Found
- Run the `uber_ride_tracker.setup_callback` service
- Restart Home Assistant after setup

## API Endpoints Used

| Endpoint | Description | Required Scope |
|----------|-------------|----------------|
| `/v1.2/me` | User profile | `profile` |
| `/v1.2/history` | Ride history | `history` |
| `/v1.2/requests/current` | Current ride | `request` (privileged) |
| `/v1/products` | Available products | None (public) |

## Notes

- Some scopes like `request` are privileged and require Full Access approval from Uber
- The integration starts with basic scopes that work in development
- Token expires after ~3600 seconds and needs refresh
- All ride tracking features require proper OAuth authorization