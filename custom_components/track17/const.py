"""Constants for the 17TRACK integration."""

DOMAIN = "track17"
DEFAULT_SCAN_INTERVAL_MINUTES = 15
DEFAULT_BASE_URL = "https://api.17track.net/track/v2.4"
SERVICE_DELETE_DELIVERED_PACKAGES = "delete_delivered_packages"
SERVICE_REGISTER_PACKAGE = "register_package"
SERVICE_DELETE_PACKAGE = "delete_package"

# 17TRACK error code returned when it cannot auto-detect a tracking number's carrier.
ERROR_CODE_CARRIER_NOT_DETECTED = -18019903

# Carrier to retry with when auto-detection fails - Zasilkovna/Packeta (17TRACK carrier key 100419),
# the household's actual courier, whose tracking numbers 17TRACK's auto-detection doesn't reliably
# recognize.
FALLBACK_CARRIER = 100419
