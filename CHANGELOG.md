# Changelog

## 1.3.0

### ⚠️ Breaking changes
- **Home Assistant 2024.11.0 or later is now required.** The integration already relied on APIs introduced in 2024.11 (reconfigure flow helpers, coordinator `config_entry`), so older versions installed it but then failed at runtime. The HACS manifest now declares the real minimum.
- **No more automatic fallback to plain HTTP.** When the URL has no scheme, `https://` is used. Previously, if HTTPS was unreachable the integration silently retried over `http://`, sending the API key and secret unencrypted. If your router only serves HTTP, type `http://` explicitly. Existing entries keep their stored URL and are not affected.

### Bug fixes
- **Options flow crash**: opening *Configure* to change the scan interval failed on current Home Assistant versions (`config_entry` is now a read-only property of the options flow).
- **Router unreachable handling**: connection errors, timeouts and invalid (non-JSON) responses from `pyopnsense` were not caught:
  - the coordinator logged an "Unexpected error" traceback on every poll while the router was down; it now reports a clean update failure and entities become unavailable;
  - the setup flow showed *Unknown error* instead of *Failed to connect*;
  - the legacy YAML setup crashed instead of failing gracefully.
- **Reconfigure with a new URL**: the config entry's unique ID now follows the new URL, and reconfiguring onto a URL already used by another entry is rejected. The entry title is updated too, unless you renamed it.
- **MAC address normalization**: MAC addresses from the ARP table, from the selected devices and from the entity registry are now all normalized to the same format, so a device can no longer get stuck as *not_home* because of case/format differences. Incomplete ARP entries are ignored.
- **Stale entities**: after changing the interface or device filters, entities that no longer match are removed instead of staying *unavailable* forever.
- **Legacy YAML**: the `tracker_mac_addresses` option was validated but ignored; it is now applied.

### Improvements
- The duplicate check now happens right after the credentials are validated, instead of after going through all setup steps.
- The ARP table is fetched once during setup instead of twice.
- Entry titles no longer include the `/api` suffix (e.g. `OPNsense https://192.168.1.1`).
- Setup and reconfigure flows now share the same validation and form code.

For earlier versions see the [GitHub releases](https://github.com/itsjustdeepred/opnsense-hacs/releases).
