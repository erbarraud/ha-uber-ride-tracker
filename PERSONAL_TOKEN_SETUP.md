# Personal Access Token Setup Guide

Since Uber requires special approval for OAuth scopes, you can use a Personal Access Token for your own use. This guide will help you set it up.

## Step 1: Generate Personal Access Token

1. Go to [Uber Developer Dashboard](https://developer.uber.com/dashboard)
2. Sign in with your Uber account
3. Select your application
4. Go to the **Auth** tab
5. Scroll down to find **"Test with a Personal Access Token"** section
6. Select the scopes you want to test with:
   - ✅ **profile** (required)
   - ✅ **history** (recommended for ride history)
   - ✅ **all_trips** (if available)
   - ✅ **request** (if available, for current ride status)
7. Click **"Generate a new token"**
8. **IMPORTANT: Copy the token immediately!** It will only be shown once
9. Save the token securely - you'll need it for the next step

## Step 2: Add to Home Assistant

### Option A: Through UI Configuration
1. In Home Assistant, go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Uber Ride Tracker"
4. Select **"Use Personal Access Token"** option
5. Paste your token when prompted
6. Click Submit

### Option B: Manual Configuration (configuration.yaml)
```yaml
uber_ride_tracker:
  personal_access_token: "YOUR_PERSONAL_ACCESS_TOKEN_HERE"
```

## Important Notes

⚠️ **Limitations of Personal Access Tokens:**
- Only works for YOUR Uber account
- Cannot be shared with other users
- May expire (typically after 30 days)
- Need to regenerate periodically

⚠️ **Security:**
- Never share your personal access token
- Don't commit it to public repositories
- Store it in `secrets.yaml` if using configuration.yaml:

```yaml
# secrets.yaml
uber_personal_token: "YOUR_PERSONAL_ACCESS_TOKEN_HERE"

# configuration.yaml
uber_ride_tracker:
  personal_access_token: !secret uber_personal_token
```

## Step 3: Verify It's Working

After setup, check if the integration is working:

1. Go to Developer Tools → Services
2. Call service: `uber_ride_tracker.test_connection`
3. Check the logs for successful API calls

## Troubleshooting

### Token Expired
- Generate a new token from Uber Dashboard
- Update it in Home Assistant

### Insufficient Scopes
- Generate a new token with more scopes selected
- Make sure to select all available scopes when generating

### API Rate Limits
- Personal tokens have the same rate limits as OAuth
- Default: 2000 requests per hour

## Switching to OAuth Later

If Uber approves your OAuth scope request later:
1. Remove the personal token configuration
2. Reconfigure using OAuth flow
3. This will allow other users to authenticate with their own accounts