"""Config flow for OPNsense integration."""

from __future__ import annotations

import logging
from typing import Any

from pyopnsense import diagnostics
from pyopnsense.exceptions import APIException
import requests
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.typing import UNDEFINED

from .const import (
    CONF_API_SECRET,
    CONF_SCAN_INTERVAL,
    CONF_TRACKER_INTERFACES,
    CONF_TRACKER_MAC_ADDRESSES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import devices_by_mac

_LOGGER = logging.getLogger(__name__)

# pyopnsense raises APIException for HTTP errors but lets connection errors
# (requests) and invalid JSON bodies (ValueError) propagate unwrapped.
CONNECTION_ERRORS = (APIException, requests.RequestException, ValueError)


def normalize_url(url: str) -> str:
    """Normalize URL: default to https when no scheme is given, add /api."""
    url = url.strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        # Never guess plain http: that would send the API credentials
        # unencrypted. Users who really want http must type it explicitly.
        url = f"https://{url}"
    if not url.endswith("/api"):
        url = f"{url}/api"
    return url


def entry_title(url: str) -> str:
    """Return the config entry title for a normalized URL."""
    return f"OPNsense {url.removesuffix('/api')}"


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Returns the normalized URL, the available interfaces and the current
    ARP table. Raises APIException, requests.RequestException or ValueError
    (invalid JSON) when the router can't be reached or rejects the request.
    """
    url = normalize_url(data[CONF_URL])
    api_key = data[CONF_API_KEY]
    api_secret = data[CONF_API_SECRET]
    verify_ssl = data.get(CONF_VERIFY_SSL, False)

    interface_client = diagnostics.InterfaceClient(
        api_key, api_secret, url, verify_ssl, timeout=20
    )
    devices = await hass.async_add_executor_job(interface_client.get_arp)

    netinsight_client = diagnostics.NetworkInsightClient(
        api_key, api_secret, url, verify_ssl, timeout=20
    )
    interfaces = await hass.async_add_executor_job(netinsight_client.get_interfaces)

    return {
        "url": url,
        "interfaces": dict(interfaces),
        "devices": devices_by_mac(devices),
    }


def _connection_schema(
    default_url: str = "",
    default_api_key: str = "",
    default_verify_ssl: bool = False,
) -> vol.Schema:
    """Build the connection data schema with optional defaults."""
    return vol.Schema(
        {
            vol.Required(CONF_URL, default=default_url): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.URL,
                    autocomplete="url",
                )
            ),
            vol.Required(CONF_API_KEY, default=default_api_key): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.TEXT,
                    autocomplete="username",
                )
            ),
            vol.Required(CONF_API_SECRET): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD,
                    autocomplete="current-password",
                )
            ),
            vol.Optional(
                CONF_VERIFY_SSL, default=default_verify_ssl
            ): BooleanSelector(),
        }
    )


class OPNsenseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OPNsense."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._interfaces: dict[str, str] = {}
        self._devices: dict[str, dict[str, Any]] = {}
        self._user_input: dict[str, Any] = {}
        self._selected_interfaces: list[str] = []

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OPNsenseOptionsFlowHandler:
        """Create the options flow."""
        return OPNsenseOptionsFlowHandler()

    async def _async_try_connect(self, credentials: dict[str, Any]) -> dict[str, str]:
        """Validate credentials and cache interfaces/devices; return errors."""
        try:
            info = await validate_input(self.hass, credentials)
        except CONNECTION_ERRORS as err:
            _LOGGER.debug("Unable to connect to OPNsense: %s", err)
            return {"base": "cannot_connect"}
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected exception")
            return {"base": "unknown"}

        self._interfaces = info["interfaces"]
        self._devices = info["devices"]
        self._user_input = {
            CONF_URL: info["url"],
            CONF_API_KEY: credentials[CONF_API_KEY],
            CONF_API_SECRET: credentials[CONF_API_SECRET],
            CONF_VERIFY_SSL: credentials.get(CONF_VERIFY_SSL, False),
        }
        return {}

    def _entry_data(self, selected_macs: list[str]) -> dict[str, Any]:
        """Build the config entry data from the collected flow state."""
        return {
            **self._user_input,
            CONF_TRACKER_INTERFACES: self._selected_interfaces,
            CONF_TRACKER_MAC_ADDRESSES: selected_macs,
        }

    def _interface_select_options(self) -> list[SelectOptionDict]:
        """Build select options from the currently known interfaces."""
        interface_options = {
            description: f"{description} ({name})"
            if name != description
            else description
            for name, description in self._interfaces.items()
        }
        return [
            SelectOptionDict(value=key, label=label)
            for key, label in interface_options.items()
        ]

    def _device_options(self, extra_macs: list[str] | None = None) -> dict[str, str]:
        """Build a mapping of MAC address to a human readable label.

        `extra_macs` are MAC addresses that should remain selectable even if
        they weren't seen in the current ARP scan (e.g. a previously tracked
        device that is temporarily offline), so reconfiguring doesn't
        silently drop them from the tracked set.
        """
        device_options: dict[str, str] = {}
        for mac, device in self._devices.items():
            hostname = device.get("hostname") or "Unknown"
            ip = device.get("ip", "Unknown")
            interface = device.get("intf_description", "Unknown")
            if not self._selected_interfaces or interface in self._selected_interfaces:
                device_options[mac] = f"{mac} - {hostname} ({ip}) - {interface}"

        for mac in extra_macs or []:
            device_options.setdefault(mac, f"{mac} - (currently offline)")

        return device_options

    def _show_interfaces_form(
        self, step_id: str, default: list[str], errors: dict[str, str]
    ) -> ConfigFlowResult:
        """Show the interface selection form."""
        valid_interfaces = set(self._interfaces.values())
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TRACKER_INTERFACES,
                    default=[i for i in default if i in valid_interfaces],
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=self._interface_select_options(),
                        multiple=True,
                        translation_key="tracker_interfaces",
                        mode="list",
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id=step_id,
            data_schema=data_schema,
            description_placeholders={
                "interfaces": ", ".join(self._interfaces.values())
            },
            errors=errors,
        )

    def _show_devices_form(
        self,
        step_id: str,
        device_options: dict[str, str],
        default: list[str],
        errors: dict[str, str],
    ) -> ConfigFlowResult:
        """Show the device selection form."""
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TRACKER_MAC_ADDRESSES, default=default
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=mac, label=label)
                            for mac, label in device_options.items()
                        ],
                        multiple=True,
                        translation_key="tracker_mac_addresses",
                        mode="list",
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id=step_id,
            data_schema=data_schema,
            description_placeholders={
                "device_count": str(len(device_options)),
            },
            errors=errors,
        )

    def _validate_interfaces(self, selected: list[str]) -> dict[str, str]:
        """Return errors if any selected interface is unknown."""
        valid_interfaces = set(self._interfaces.values())
        if any(interface not in valid_interfaces for interface in selected):
            return {"base": "invalid_interface"}
        return {}

    @staticmethod
    def _validate_macs(
        selected: list[str], device_options: dict[str, str]
    ) -> dict[str, str]:
        """Return errors if any selected MAC is not a known option."""
        if any(mac not in device_options for mac in selected):
            return {"base": "invalid_mac"}
        return {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._async_try_connect(user_input)
            if not errors:
                await self.async_set_unique_id(self._user_input[CONF_URL])
                self._abort_if_unique_id_configured()
                return await self.async_step_interfaces()

        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(),
            errors=errors,
        )

    async def async_step_interfaces(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle interface selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_interfaces = user_input.get(CONF_TRACKER_INTERFACES, [])
            errors = self._validate_interfaces(selected_interfaces)
            if not errors:
                self._selected_interfaces = selected_interfaces
                return await self.async_step_devices()

        return self._show_interfaces_form("interfaces", [], errors)

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device MAC address selection step."""
        errors: dict[str, str] = {}
        device_options = self._device_options()

        if user_input is not None or not device_options:
            selected_macs = (user_input or {}).get(CONF_TRACKER_MAC_ADDRESSES, [])
            errors = self._validate_macs(selected_macs, device_options)
            if not errors:
                return self.async_create_entry(
                    title=entry_title(self._user_input[CONF_URL]),
                    data=self._entry_data(selected_macs),
                )

        return self._show_devices_form("devices", device_options, [], errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration.

        On first call (user_input=None) try existing credentials automatically
        and skip directly to interface/device selection.  Only show the
        credential form if the automatic attempt fails or the user submitted
        new credentials that need to be validated.
        """
        reconfigure_entry = self._get_reconfigure_entry()
        credentials = user_input if user_input is not None else reconfigure_entry.data

        errors = await self._async_try_connect(credentials)
        if not errors:
            url = self._user_input[CONF_URL]
            if any(
                entry.unique_id == url and entry.entry_id != reconfigure_entry.entry_id
                for entry in self._async_current_entries(include_ignore=False)
            ):
                errors["base"] = "already_configured"
            else:
                return await self.async_step_reconfigure_interfaces()

        # Show credential form only when connection failed
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_connection_schema(
                default_url=reconfigure_entry.data.get(CONF_URL, ""),
                default_api_key=reconfigure_entry.data.get(CONF_API_KEY, ""),
                default_verify_ssl=reconfigure_entry.data.get(CONF_VERIFY_SSL, False),
            ),
            errors=errors,
        )

    async def async_step_reconfigure_interfaces(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle interface reconfiguration step."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_interfaces = user_input.get(CONF_TRACKER_INTERFACES, [])
            errors = self._validate_interfaces(selected_interfaces)
            if not errors:
                self._selected_interfaces = selected_interfaces
                return await self.async_step_reconfigure_devices()

        return self._show_interfaces_form(
            "reconfigure_interfaces",
            reconfigure_entry.data.get(CONF_TRACKER_INTERFACES, []),
            errors,
        )

    async def async_step_reconfigure_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device MAC address reconfiguration step."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        existing_mac_addresses = [
            format_mac(mac)
            for mac in reconfigure_entry.data.get(CONF_TRACKER_MAC_ADDRESSES, [])
        ]
        # Previously tracked MACs stay selectable even if currently offline,
        # so reconfiguring never silently un-tracks a device that's simply
        # not on the network right now.
        device_options = self._device_options(extra_macs=existing_mac_addresses)

        if user_input is not None:
            selected_macs = user_input.get(CONF_TRACKER_MAC_ADDRESSES, [])
            errors = self._validate_macs(selected_macs, device_options)
            if not errors:
                url = self._user_input[CONF_URL]
                old_url = reconfigure_entry.data.get(CONF_URL, "")
                # Only refresh the title if the user never renamed the entry.
                title_is_default = reconfigure_entry.title in (
                    f"OPNsense {old_url}",
                    entry_title(old_url),
                )
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    unique_id=url,
                    title=entry_title(url) if title_is_default else UNDEFINED,
                    data_updates=self._entry_data(selected_macs),
                )

        return self._show_devices_form(
            "reconfigure_devices", device_options, existing_mac_addresses, errors
        )


class OPNsenseOptionsFlowHandler(OptionsFlow):
    """Handle OPNsense options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])},
            )

        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=current_scan_interval
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=5,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="s",
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
