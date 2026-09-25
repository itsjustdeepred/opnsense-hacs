"""Data update coordinator for OPNsense."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from pyopnsense import diagnostics
from pyopnsense.exceptions import APIException
import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class OPNsenseDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Class to manage fetching OPNsense data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: diagnostics.InterfaceClient,
        update_interval: timedelta = SCAN_INTERVAL,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
            config_entry=config_entry,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Update data via library."""
        try:
            data = await self.hass.async_add_executor_job(self.client.get_arp)
        except (APIException, requests.RequestException, ValueError) as err:
            # pyopnsense doesn't wrap connection errors (requests) or invalid
            # JSON bodies (ValueError), so all three mean "router unreachable".
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        return devices_by_mac(data)


def devices_by_mac(devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index ARP entries by normalized MAC, skipping incomplete entries."""
    out: dict[str, dict[str, Any]] = {}
    for device in devices:
        mac = device.get("mac")
        if not mac or "incomplete" in mac:
            continue
        mac = format_mac(mac)
        out[mac] = {**device, "mac": mac}
    return out
