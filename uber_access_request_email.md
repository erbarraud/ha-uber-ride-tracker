# Email to Uber Developer Support

**To:** developer-support@uber.com (or your Uber business development representative)  
**Subject:** Request for OAuth Scope Access - Home Assistant Integration for Personal Use

---

Dear Uber Developer Support Team,

I am developing a personal, non-commercial integration between Uber's API and Home Assistant (an open-source home automation platform) for my own use. The integration aims to display my Uber ride information on my home dashboard for personal tracking and home automation purposes.

## Project Details

**Application Name:** Home Assistant Uber Ride Tracker  
**Purpose:** Personal use only - tracking my own Uber rides on my home automation dashboard  
**Type:** Non-commercial, open-source integration  
**GitHub Repository:** https://github.com/erbarraud/ha-uber-ride-tracker

## What the Integration Does

This Home Assistant integration allows users to:
- View their recent Uber ride history
- Display current trip status (if any)
- Show trip details like pickup/dropoff locations, fare, and duration
- Track ride statistics over time
- All data is accessed only by the authenticated user for their own account

## OAuth Scopes Requested

I am requesting access to the following OAuth scopes for my application:

1. **profile** - To identify the authenticated user
2. **history** (or **all_trips**) - To retrieve the user's ride history
3. **request** (optional) - To check current ride status

Currently, my application shows the error "Your application currently does not have access to Authorization Code scopes" when attempting to use OAuth authentication.

## Technical Implementation

- The integration uses OAuth 2.0 Authorization Code flow
- It follows Uber's API best practices and rate limiting guidelines
- User credentials are never stored; only OAuth tokens are retained
- The integration is fully open-source and transparent
- Each user authenticates with their own Uber account to access only their own data

## Security and Privacy

- The integration only accesses data for the authenticated user
- No data is shared with third parties
- All tokens are stored securely within the user's Home Assistant instance
- The code is open-source and available for review

## Request

I kindly request that you enable OAuth scope access for my application, particularly the "profile" and "history" scopes, so that users can authenticate and access their own Uber data through Home Assistant.

If there are any additional requirements, documentation, or compliance steps needed to obtain this access, please let me know. I am happy to comply with all necessary guidelines and restrictions.

Thank you for considering this request. I look forward to your response.

Best regards,  
[Your Name]  
[Your Email]  
[Your Phone Number - if applicable]

---

## Additional Information to Include (if you have it):

- **Uber App Client ID:** [Your Client ID]
- **Registered Redirect URI:** https://home.erbarraud.com/local/uber_callback.html
- **Estimated Number of Users:** Personal use only (1 user) or small scale