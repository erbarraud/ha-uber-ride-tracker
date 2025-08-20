"""Constants for the Uber Ride Tracker integration."""
from datetime import timedelta
from typing import Final

DOMAIN: Final = "uber_ride_tracker"
NAME: Final = "Uber Ride Tracker"
MANUFACTURER: Final = "Uber Technologies Inc."

# OAuth2 Configuration
OAUTH2_AUTHORIZE_URL: Final = "https://login.uber.com/oauth/v2/authorize"
OAUTH2_TOKEN_URL: Final = "https://login.uber.com/oauth/v2/token"
OAUTH2_SCOPES: Final = [
    "profile",
    "request",
    "request.receipt",
    "all_trips",
    "ride.request"
]

# API Configuration
API_BASE_URL: Final = "https://api.uber.com"
API_VERSION: Final = "v1.2"
API_TIMEOUT: Final = 30

# API Endpoints
ENDPOINT_CURRENT_REQUEST: Final = f"/{API_VERSION}/requests/current"
ENDPOINT_REQUEST_DETAILS: Final = f"/{API_VERSION}/requests/{{request_id}}"
ENDPOINT_REQUEST_RECEIPT: Final = f"/{API_VERSION}/requests/{{request_id}}/receipt"
ENDPOINT_REQUEST_MAP: Final = f"/{API_VERSION}/requests/{{request_id}}/map"
ENDPOINT_USER_PROFILE: Final = f"/{API_VERSION}/me"
ENDPOINT_TRIP_HISTORY: Final = f"/{API_VERSION}/history"

# Update Intervals
UPDATE_INTERVAL_ACTIVE: Final = timedelta(seconds=10)
UPDATE_INTERVAL_INACTIVE: Final = timedelta(seconds=60)
UPDATE_INTERVAL_ERROR: Final = timedelta(seconds=300)

# Ride Status Values
RIDE_STATUS_PROCESSING: Final = "processing"
RIDE_STATUS_NO_DRIVERS: Final = "no_drivers_available"
RIDE_STATUS_ACCEPTED: Final = "accepted"
RIDE_STATUS_ARRIVING: Final = "arriving"
RIDE_STATUS_IN_PROGRESS: Final = "in_progress"
RIDE_STATUS_DRIVER_CANCELED: Final = "driver_canceled"
RIDE_STATUS_RIDER_CANCELED: Final = "rider_canceled"
RIDE_STATUS_COMPLETED: Final = "completed"

ACTIVE_RIDE_STATUSES: Final = [
    RIDE_STATUS_PROCESSING,
    RIDE_STATUS_ACCEPTED,
    RIDE_STATUS_ARRIVING,
    RIDE_STATUS_IN_PROGRESS,
]

# Entity Keys
CONF_CLIENT_ID: Final = "client_id"
CONF_CLIENT_SECRET: Final = "client_secret"
CONF_AUTH_CODE: Final = "auth_code"
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"
CONF_TOKEN_EXPIRES: Final = "token_expires"

# Attributes
ATTR_STATUS: Final = "status"
ATTR_DRIVER_NAME: Final = "driver_name"
ATTR_DRIVER_PHOTO_URL: Final = "driver_photo_url"
ATTR_DRIVER_RATING: Final = "driver_rating"
ATTR_DRIVER_PHONE: Final = "driver_phone"
ATTR_VEHICLE_MAKE: Final = "vehicle_make"
ATTR_VEHICLE_MODEL: Final = "vehicle_model"
ATTR_VEHICLE_COLOR: Final = "vehicle_color"
ATTR_VEHICLE_LICENSE_PLATE: Final = "vehicle_license_plate"
ATTR_ETA_MINUTES: Final = "eta_minutes"
ATTR_PICKUP_ETA: Final = "pickup_eta"
ATTR_DESTINATION_ETA: Final = "destination_eta"
ATTR_PICKUP_ADDRESS: Final = "pickup_address"
ATTR_DESTINATION_ADDRESS: Final = "destination_address"
ATTR_FARE_ESTIMATE: Final = "fare_estimate"
ATTR_DISTANCE_REMAINING: Final = "distance_remaining"
ATTR_DURATION_REMAINING: Final = "duration_remaining"
ATTR_MAP_URL: Final = "map_url"
ATTR_SHARE_URL: Final = "share_url"
ATTR_TRIP_ID: Final = "trip_id"
ATTR_PRODUCT_NAME: Final = "product_name"
ATTR_SURGE_MULTIPLIER: Final = "surge_multiplier"
ATTR_DRIVER_LOCATION: Final = "driver_location"
ATTR_TRIP_PROGRESS: Final = "trip_progress_percentage"

# Services
SERVICE_REFRESH_STATUS: Final = "refresh_status"
SERVICE_GET_RIDE_HISTORY: Final = "get_ride_history"

# Defaults
DEFAULT_NAME: Final = "Uber Ride"
DEFAULT_SCAN_INTERVAL: Final = UPDATE_INTERVAL_INACTIVE

# Rate Limiting
RATE_LIMIT_CALLS: Final = 2000
RATE_LIMIT_WINDOW: Final = 3600  # 1 hour in seconds

# Error Messages
ERROR_AUTH_FAILED: Final = "authentication_failed"
ERROR_API_ERROR: Final = "api_error"
ERROR_RATE_LIMITED: Final = "rate_limited"
ERROR_TOKEN_EXPIRED: Final = "token_expired"
ERROR_NO_ACTIVE_RIDE: Final = "no_active_ride"
ERROR_INVALID_RESPONSE: Final = "invalid_response"