"""Constants for OPNsense component."""

DOMAIN = "opnsense"
OPNSENSE_DATA = DOMAIN

# Key used to namespace legacy YAML configuration data within
# hass.data[OPNSENSE_DATA], mirroring the per-entry_id namespacing used for
# config entries so the two setup paths never share top-level keys.
OPNSENSE_LEGACY_ENTRY = "yaml"

CONF_API_SECRET = "api_secret"
CONF_INTERFACE_CLIENT = "interface_client"
CONF_TRACKER_INTERFACES = "tracker_interfaces"
CONF_TRACKER_MAC_ADDRESSES = "tracker_mac_addresses"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 300
