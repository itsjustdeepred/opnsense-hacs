# OPNsense Integration for Home Assistant

Enhanced OPNsense integration for Home Assistant with GUI-based configuration flow, interface selection, and device tracking capabilities.

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]][license]
[![hacs][hacsbadge]][hacs]
[![Maintainer][maintainer-shield]][maintainer]

<p align="center">
  <img width="360" src="https://raw.githubusercontent.com/opnsense/core/stable/25.1/src/opnsense/www/themes/opnsense/build/images/default-logo.svg">
</p>

> **Note**: A Pull Request is currently in progress to integrate this into Home Assistant core. In the meantime, you can use this HACS version which includes all the latest features.

This integration adds support for device tracking and network monitoring through your OPNsense router. It provides a GUI-based configuration flow that allows you to select which network interfaces and devices to monitor.

For this integration you **must have an OPNsense router** with API access enabled. You need to create an API user with specific privileges (see Configuration section below).

## Features

- **GUI Configuration**: Set up the integration through the Home Assistant UI without editing YAML files
- **Interface Selection**: Choose which network interfaces to monitor for device tracking
- **Device Selection**: Select specific devices by MAC address to track, or track all devices
- **Reconfiguration**: Update interface and device selections without removing and re-adding the integration
- **Automatic Entity Management**: Entities are automatically added or removed based on your selections
- **Real-time Updates**: Uses a data coordinator for efficient polling and updates
- **URL Normalization**: Automatically handles URL formatting (adds `/api` if missing, tries HTTPS then HTTP)

## Configuration

To add OPNsense to your installation, do the following:

- Go to Settings → Devices & Services
- Click the + ADD INTEGRATION button in the lower right corner
- Search for **OPNsense** and click the integration
- When loaded, there will be a configuration box, where you must enter:

  | Parameter | Required | Default Value | Description |
  | --------- | -------- | ------------- | ----------- |
  | `OPNsense URL` | Yes | None | URL of your OPNsense instance (e.g., `https://192.168.1.1` or just `192.168.1.1`). The integration will automatically try HTTPS first, then HTTP if needed, and add `/api` if missing. |
  | `API Key` | Yes | None | API key from your OPNsense router. Create it in System → Access → Users → [Your User] → API tab. |
  | `API Secret` | Yes | None | API secret from your OPNsense router. Generated together with the API key. |
  | `Verify SSL` | No | False | Enable to verify SSL certificates. Disable if using self-signed certificates. |

- Click on SUBMIT to save your data
- Select which network interfaces to monitor (leave empty to track all interfaces)
- Select specific devices to track by MAC address (leave empty to track all devices)

**Important**: The API user account requires specific privileges:

- **GUI Name**: Diagnostics: ARP Table
- **GUI Name**: Diagnostics: Network Insight
- **All Pages** (required for OPNsense 25.7 and later)

For more information on creating API credentials, refer to the [OPNsense documentation](https://docs.opnsense.org/development/api.html).

Minimum required version of Home Assistant is **2024.1.0**.

***

[releases-shield]: https://img.shields.io/github/release/itsjustdeepred/opnsense-hacs.svg?style=flat-square
[releases]: https://github.com/itsjustdeepred/opnsense-hacs/releases
[license-shield]: https://img.shields.io/github/license/itsjustdeepred/opnsense-hacs.svg?style=flat-square
[license]: https://github.com/itsjustdeepred/opnsense-hacs/blob/main/LICENSE
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square
[maintainer-shield]: https://img.shields.io/badge/maintainer-@itsjustdeepred-blue.svg?style=flat-square
[maintainer]: https://github.com/itsjustdeepred
