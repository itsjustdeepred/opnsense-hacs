# Release v1.0.0 - Initial Release

## 🎉 Initial Release

This is the initial release of the enhanced OPNsense integration for Home Assistant, providing a complete GUI-based configuration experience with advanced device tracking capabilities.

## ✨ Features

### Configuration
- **GUI-based Configuration Flow**: Set up the integration entirely through the Home Assistant UI - no YAML editing required
- **URL Normalization**: Automatically handles URL formatting (adds `/api` if missing, tries HTTPS then HTTP)
- **Reconfiguration Support**: Update interface and device selections without removing and re-adding the integration

### Device Tracking
- **Interface Selection**: Choose which network interfaces to monitor for device tracking
- **Device Selection**: Select specific devices by MAC address to track, or track all devices
- **Automatic Entity Management**: Entities are automatically added or removed based on your selections
- **Real-time Updates**: Uses a data update coordinator for efficient polling and updates

### Entity Management
- **Smart Entity Restoration**: Entities are preserved during integration reload, preventing "no longer provided" messages
- **Dynamic Updates**: Entities automatically update when devices connect or disconnect
- **State Tracking**: Accurate `home`/`not_home` state based on device connectivity

## 📋 Requirements

- Home Assistant 2024.1.0 or later
- OPNsense router with API access enabled
- API user with required privileges:
  - Diagnostics: ARP Table
  - Diagnostics: Network Insight
  - All Pages (required for OPNsense 25.7 and later)

## 🚀 Installation

### Via HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots → "Custom repositories"
4. Add: `https://github.com/itsjustdeepred/opnsense-hacs`
5. Select category: "Integration"
6. Click "Download" and restart Home Assistant

### Manual Installation
1. Download or clone this repository
2. Copy `custom_components/opnsense` to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## 📖 Documentation

For detailed setup instructions, API credential configuration, and troubleshooting, see the [README](https://github.com/itsjustdeepred/opnsense-hacs/blob/main/README.md).

## 🔗 Links

- **Repository**: https://github.com/itsjustdeepred/opnsense-hacs
- **Issues**: https://github.com/itsjustdeepred/opnsense-hacs/issues
- **OPNsense Documentation**: https://docs.opnsense.org/development/api.html

## 📝 Note

A Pull Request is currently in progress to integrate this into Home Assistant core. This HACS version includes all the latest features and improvements.

---

**Enjoy your enhanced OPNsense integration!** 🎊

