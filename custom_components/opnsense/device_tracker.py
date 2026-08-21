"""Device tracker support for OPNsense routers."""

from __future__ import annotations

import logging
from typing import Any, TypeAlias

from pyopnsense import diagnostics

from homeassistant.components.device_tracker import (
    DeviceScanner,
    ScannerEntity,
    SourceType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_INTERFACE_CLIENT,
    CONF_TRACKER_INTERFACES,
    CONF_TRACKER_MAC_ADDRESSES,
    DOMAIN,
    OPNSENSE_DATA,
    OPNSENSE_LEGACY_ENTRY,
)
from .coordinator import OPNsenseDataUpdateCoordinator

DeviceDetails: TypeAlias = dict[str, Any]
DeviceDetailsByMAC: TypeAlias = dict[str, DeviceDetails]


async def async_get_scanner(
    hass: HomeAssistant, config: ConfigType
) -> DeviceScanner | None:
    """Configure the OPNsense device_tracker (legacy YAML)."""
    legacy_data = hass.data.get(OPNSENSE_DATA, {}).get(OPNSENSE_LEGACY_ENTRY)
    if not legacy_data:
        return None
    return OPNsenseDeviceScanner(
        legacy_data[CONF_INTERFACE_CLIENT],
        legacy_data[CONF_TRACKER_INTERFACES],
        legacy_data.get(CONF_TRACKER_MAC_ADDRESSES, []),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for OPNsense component."""
    data = hass.data[OPNSENSE_DATA][entry.entry_id]
    coordinator: OPNsenseDataUpdateCoordinator = data["coordinator"]
    tracker_interfaces = data[CONF_TRACKER_INTERFACES]
    tracker_mac_addresses = data[CONF_TRACKER_MAC_ADDRESSES]

    entity_registry = er.async_get(hass)

    entities = []
    devices_in_data: dict[str, DeviceDetails] = {}
    for mac, device in coordinator.data.items():
        if (
            tracker_interfaces
            and device.get("intf_description") not in tracker_interfaces
        ):
            continue
        if tracker_mac_addresses and mac not in tracker_mac_addresses:
            continue
        unique_id = format_mac(mac)
        devices_in_data[unique_id] = device
        if deleted_entity_id := entity_registry.async_get_entity_id(
            "device_tracker", DOMAIN, unique_id
        ):
            entity_entry = entity_registry.async_get(deleted_entity_id)
            if entity_entry and entity_entry.config_entry_id != entry.entry_id:
                _LOGGER.debug(
                    "Removing orphaned entity %s before recreating",
                    deleted_entity_id,
                )
                entity_registry.async_remove(deleted_entity_id)

        entities.append(
            OPNsenseTrackerEntity(
                coordinator, device, tracker_interfaces, tracker_mac_addresses
            )
        )

    existing_entities_list = [
        entity
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        if entity.platform == DOMAIN
    ]
    for entity_entry in existing_entities_list:
        if entity_entry.unique_id not in devices_in_data:
            # unique_id is already in format_mac format (lowercase colon-separated)
            mac_formatted = entity_entry.unique_id
            if tracker_mac_addresses and mac_formatted not in tracker_mac_addresses:
                continue
            device_data: DeviceDetails = {
                "mac": mac_formatted,
                "hostname": entity_entry.original_name or None,
                "ip": None,
                "intf_description": None,
                "manufacturer": None,
            }
            entities.append(
                OPNsenseTrackerEntity(
                    coordinator, device_data, tracker_interfaces, tracker_mac_addresses
                )
            )

    if entities:
        async_add_entities(entities)

    @callback
    def _async_check_devices() -> None:
        """Check for new devices and add tracker entities."""
        valid_macs = {
            format_mac(mac)
            for mac, device in coordinator.data.items()
            if (
                not tracker_interfaces
                or device.get("intf_description") in tracker_interfaces
            )
            and (not tracker_mac_addresses or mac in tracker_mac_addresses)
        }

        current_entity_registry = er.async_get(hass)
        existing_unique_ids = {
            entity.unique_id
            for entity in er.async_entries_for_config_entry(
                current_entity_registry, entry.entry_id
            )
            if entity.platform == DOMAIN
        }

        new_macs = valid_macs - existing_unique_ids
        new_entities = []
        for mac, device in coordinator.data.items():
            unique_id = format_mac(mac)
            if unique_id in new_macs:
                if deleted_entity_id := current_entity_registry.async_get_entity_id(
                    "device_tracker", DOMAIN, unique_id
                ):
                    entity_entry = current_entity_registry.async_get(deleted_entity_id)
                    if entity_entry and entity_entry.config_entry_id != entry.entry_id:
                        _LOGGER.debug(
                            "Removing orphaned entity %s before recreating",
                            deleted_entity_id,
                        )
                        current_entity_registry.async_remove(deleted_entity_id)

                new_entities.append(
                    OPNsenseTrackerEntity(
                        coordinator, device, tracker_interfaces, tracker_mac_addresses
                    )
                )

        if new_entities:
            _LOGGER.debug("Adding %d new device tracker entities", len(new_entities))
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_async_check_devices))


class OPNsenseDeviceScanner(DeviceScanner):
    """This class queries a router running OPNsense (legacy)."""

    def __init__(
        self,
        client: diagnostics.InterfaceClient,
        interfaces: list[str],
        mac_addresses: list[str] | None = None,
    ) -> None:
        """Initialize the scanner."""
        self.last_results: DeviceDetailsByMAC = {}
        self.client = client
        self.interfaces = interfaces
        self.mac_addresses = mac_addresses or []

    def _get_mac_addrs(self, devices: list[DeviceDetails]) -> DeviceDetailsByMAC:
        """Create dict with mac address keys from list of devices."""
        out_devices: DeviceDetailsByMAC = {}
        for device in devices:
            mac = device["mac"]
            if (
                self.interfaces
                and device.get("intf_description") not in self.interfaces
            ):
                continue
            if self.mac_addresses and mac not in self.mac_addresses:
                continue
            out_devices[mac] = device
        return out_devices

    def scan_devices(self) -> list[str]:
        """Scan for new devices and return a list with found device IDs."""
        self.update_info()
        return list(self.last_results)

    def get_device_name(self, device: str) -> str | None:
        """Return the name of the given device or None if we don't know."""
        if device not in self.last_results:
            return None
        return self.last_results[device].get("hostname") or None

    def update_info(self) -> bool:
        """Ensure the information from the OPNsense router is up to date.

        Return boolean if scanning successful.
        """
        try:
            devices = self.client.get_arp()
            self.last_results = self._get_mac_addrs(devices)
            return True
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Failed to update OPNsense device list")
            return False

    def get_extra_attributes(self, device: str) -> dict[Any, Any]:
        """Return the extra attrs of the given device."""
        if device not in self.last_results:
            return {}
        mfg = self.last_results[device].get("manufacturer")
        if not mfg:
            return {}
        return {"manufacturer": mfg}


class OPNsenseTrackerEntity(
    CoordinatorEntity[OPNsenseDataUpdateCoordinator], ScannerEntity
):
    """Represent a tracked device."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: OPNsenseDataUpdateCoordinator,
        device: DeviceDetails,
        tracker_interfaces: list[str],
        tracker_mac_addresses: list[str],
    ) -> None:
        """Initialize the tracker entity."""
        super().__init__(coordinator)
        self._device = device
        self._mac = device["mac"]
        self._tracker_interfaces = tracker_interfaces
        self._tracker_mac_addresses = tracker_mac_addresses
        self._attr_unique_id = format_mac(self._mac)
        hostname = device.get("hostname")
        if hostname and hostname.strip():
            self._attr_name = hostname.strip()
        else:
            self._attr_name = format_mac(self._mac)
        self._attr_hostname = (
            hostname.strip() if hostname and hostname.strip() else None
        )
        self._attr_ip_address = device.get("ip")
        self._attr_mac_address = self._mac

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._should_track()

    def _should_track(self) -> bool:
        """Check if device should be tracked based on filters."""
        if self._tracker_interfaces:
            intf = self._device.get("intf_description")
            # When intf is None the device is offline and its last interface is
            # unknown; don't filter it out so it keeps showing as "not_home".
            if intf is not None and intf not in self._tracker_interfaces:
                return False
        if self._tracker_mac_addresses:
            if self._mac not in self._tracker_mac_addresses:
                return False
        return True

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        return self._mac in self.coordinator.data

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.ROUTER

    @callback
    def find_device_entry(self) -> None:
        """Prevent automatic linking to existing device registry entries."""
        return

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if entity is enabled by default."""
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs: dict[str, Any] = {}
        if self._device.get("manufacturer"):
            attrs["manufacturer"] = self._device["manufacturer"]
        if self._device.get("ip"):
            attrs["ip"] = self._device["ip"]
        if self._device.get("intf_description"):
            attrs["interface"] = self._device["intf_description"]
        return attrs

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device = self.coordinator.data.get(self._mac)
        if device is not None:
            self._device = device
            hostname = device.get("hostname")
            if hostname and hostname.strip():
                self._attr_name = hostname.strip()
                self._attr_hostname = hostname.strip()
            else:
                self._attr_hostname = None
            if device.get("ip"):
                self._attr_ip_address = device["ip"]
        self.async_write_ha_state()
