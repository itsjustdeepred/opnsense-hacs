# Release v1.0.1 - Bug Fix

## Bug Fixes

### Device Tracker Entity Persistence
- Fixed: Device tracker entities are no longer removed when devices disconnect
- Changed: Disconnected devices now correctly show as offline instead of being removed from the entity registry
- Benefit: Preserves entity history, configuration, and automations when devices temporarily disconnect

## Technical Details

Previously, when a device disconnected from the network, the integration would remove the entity from Home Assistant's entity registry. When the device reconnected, a new entity would be created, losing all history and configuration.

Now, entities remain in the registry and are simply marked as offline when devices disconnect. The is_connected property correctly reflects the device's connection state, allowing Home Assistant to properly track device presence without losing entity data.

## Upgrade Notes

No action required. This is a bug fix that improves the existing functionality.
