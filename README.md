<div align="center">

![OPNsense Logo](https://raw.githubusercontent.com/opnsense/core/stable/25.1/src/opnsense/www/themes/opnsense/build/images/default-logo.svg)

# OPNsense Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs][hacs-shield]][hacs]
[![Maintainer][maintainer-shield]][maintainer]

[![Open your Home Assistant instance and show the integrations page.][my-ha-badge]][my-ha]
[![Open your Home Assistant instance and show the add integration page.][add-integration-badge]][add-integration]

</div>

Enhanced OPNsense integration for Home Assistant with GUI-based configuration flow, interface selection, and device tracking capabilities.

> **Note**: A Pull Request is currently in progress to integrate this into Home Assistant core. In the meantime, you can use this HACS version which includes all the latest features.

## Features

- **GUI Configuration**: Set up the integration through the Home Assistant UI without editing YAML files
- **Interface Selection**: Choose which network interfaces to monitor for device tracking
- **Device Selection**: Select specific devices by MAC address to track, or track all devices
- **Reconfiguration**: Update interface and device selections without removing and re-adding the integration
- **Automatic Entity Management**: Entities are automatically added or removed based on your selections
- **Real-time Updates**: Uses a data coordinator for efficient polling and updates
- **URL Normalization**: Automatically handles URL formatting (adds `/api` if missing, tries HTTPS then HTTP)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/itsjustdeepred/opnsense-hacs`
6. Select category: "Integration"
7. Click "Add"
8. Find "OPNsense" in the HACS integrations list
9. Click "Download"
10. Restart Home Assistant
11. Go to Settings → Devices & Services → Add Integration
12. Search for "OPNsense" and follow the setup wizard

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/opnsense` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Search for "OPNsense" and follow the setup wizard

## Configuration

### Obtaining API Credentials

The `api_key` and `api_secret` values are acquired from your OPNsense router using the web interface. For more information on this procedure, refer to the [OPNsense documentation](https://docs.opnsense.org/development/api.html).

**Important**: The API user account requires specific privileges:

**User with API Key requires privileges for Type:**

- **GUI Name**: Diagnostics: ARP Table
- **GUI Name**: Diagnostics: Network Insight

**Important**: OPNsense versions 25.7 and later require **All Pages** privilege to be granted to the API user account.

### Setup Steps

1. **Create API User in OPNsense**:
   - Log in to your OPNsense web interface
   - Navigate to System → Access → Users
   - Create a new user or edit an existing one
   - Go to the "API" tab
   - Generate an API key and secret
   - Ensure the user has the required privileges mentioned above

2. **Add Integration in Home Assistant**:
   - Go to Settings → Devices & Services → Add Integration
   - Search for "OPNsense"
   - Enter your OPNsense URL (e.g., `https://192.168.1.1` or just `192.168.1.1`)
   - Enter your API key and secret
   - Optionally enable SSL verification
   - The integration will automatically try HTTPS first, then HTTP if needed
   - The URL will be normalized to include `/api` if missing

3. **Select Interfaces**:
   - Choose which network interfaces to monitor
   - Leave empty to track devices on all interfaces

4. **Select Devices**:
   - Choose specific devices by MAC address to track
   - Leave empty to track all devices found on the selected interfaces

### Reconfiguration

To update your interface or device selections:

1. Go to Settings → Devices & Services
2. Find your OPNsense integration
3. Click on it, then click "Configure"
4. Update your interface and device selections
5. Changes take effect immediately

## Device Tracking

The integration creates device tracker entities for each tracked device. The state reflects whether the device is currently connected to your network:

- **home**: Device is connected and active on the network
- **not_home**: Device is not currently connected

Each entity includes the following attributes:
- `ip`: Current IP address
- `interface`: Network interface the device is connected to
- `manufacturer`: Device manufacturer (if available)

## Troubleshooting

### Connection Issues

- Verify your OPNsense URL is correct and accessible from Home Assistant
- Check that your API key and secret are valid
- Ensure the API user has the required privileges
- For OPNsense 25.7+, verify "All Pages" privilege is granted

### Devices Not Appearing

- Check that the device is connected to a selected interface
- Verify the device's MAC address is in the ARP table
- Ensure the device is selected in the device list (or leave empty to track all)

### SSL Certificate Errors

- If using self-signed certificates, disable SSL verification in the configuration
- For production use, consider installing a valid SSL certificate on your OPNsense router

### Translation Strings Not Showing

If you don't see user-friendly field labels in the config flow:

1. Ensure you have restarted Home Assistant after installation/update
2. Clear your browser cache or use an incognito window
3. Verify that the `translations/en.json` file exists in the integration directory

## Requirements

- Home Assistant 2024.1.0 or later
- OPNsense router with API access enabled
- Python package: `pyopnsense==0.4.0` (installed automatically)

## Credits

This integration is based on the original OPNsense integration code by [mtreinish](https://github.com/mtreinish), which has been revised and updated to support new features including:

- GUI-based configuration flow
- Interface and device selection
- Reconfiguration capabilities
- Automatic entity management
- Data update coordinator pattern

Original code repository: https://github.com/mtreinish

## Support

For issues, feature requests, or contributions, please visit the [GitHub repository](https://github.com/itsjustdeepred/opnsense-hacs).

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**If you find this integration useful, please consider giving it a ⭐ on GitHub!**

Made with ❤️ for the Home Assistant community

</div>

[releases-shield]: https://img.shields.io/github/release/itsjustdeepred/opnsense-hacs.svg
[releases]: https://github.com/itsjustdeepred/opnsense-hacs/releases
[license-shield]: https://img.shields.io/github/license/itsjustdeepred/opnsense-hacs.svg
[license]: https://github.com/itsjustdeepred/opnsense-hacs/blob/main/LICENSE
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs]: https://hacs.xyz
[maintainer-shield]: https://img.shields.io/badge/maintainer-@itsjustdeepred-blue.svg
[maintainer]: https://github.com/itsjustdeepred
[my-ha-badge]: https://my.home-assistant.io/badges/integrations.svg
[my-ha]: https://my.home-assistant.io/redirect/integrations/
[add-integration-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[add-integration]: https://my.home-assistant.io/redirect/config_flow_start/?domain=opnsense
