"""Constants for the Redfish integration."""

from datetime import timedelta

DOMAIN = "redfish"
CONF_BASE_URL = "base_url"
UPDATE_INTERVAL = timedelta(minutes=1)
PLATFORMS = ["button", "sensor", "switch"]
