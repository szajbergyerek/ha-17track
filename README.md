# 17TRACK for Home Assistant

<img src="logo.png" alt="17TRACK for Home Assistant logo" width="128" height="128">

A Home Assistant custom integration for [17TRACK](https://www.17track.net/), a universal package tracking service. Register your packages on the 17TRACK website or app, and this integration will surface each one as a sensor entity in Home Assistant.

## Features

- One sensor per package registered on your 17TRACK account, created and removed automatically.
- Sensor state is a human-readable sentence: `On <date> package "<name>": <latest event>`.
- Attributes with structured data (tracking number, carrier, package status, last event time) for use in automations and dashboards.
- Polls the 17TRACK API every 15 minutes. This only reads existing data (`gettracklist`), so it never consumes your registration quota, however often it runs.
- A `track17.register_package` service (and matching `input_text` + automation pattern, see below) to register a new tracking number from Home Assistant, optionally with a custom tag/name.
- A `track17.delete_package` service to delete one specific package by tag or tracking number (handy for voice assistants: "delete the Csapágy package").
- A "Delete delivered packages" button and matching `track17.delete_delivered_packages` service to clear out every delivered package from 17TRACK in one go. Packages are never deleted automatically - delivered packages stay tracked (and visible) until you delete them yourself.

You can also register tracking numbers directly via the 17TRACK website or app; this integration will pick them up automatically either way.

## Registering a package

Call the `track17.register_package` service with a `tracking_number` and an optional `tag` (a custom label shown instead of the raw tracking number, both on the sensor and to voice assistants):

```yaml
action: track17.register_package
data:
  tracking_number: "YT2534627690112345"
  tag: "Csapágy"
```

Tracking numbers containing spaces (common - many carriers print them that way) have the whitespace stripped automatically before being sent to 17TRACK.

If 17TRACK can't auto-detect the carrier for a tracking number, it's automatically retried once forcing Zasilkovna/Packeta (17TRACK carrier key `100419`) - this household's actual courier, whose tracking number format 17TRACK's auto-detection doesn't reliably recognize. If you ever add packages from a different carrier that also fails auto-detection, this fallback will need to become configurable instead of hardcoded.

## Installation

### Via HACS

1. In HACS, go to **Integrations** → menu (⋮) → **Custom repositories**.
2. Add this repository URL (`https://github.com/szajbergyerek/ha-17track`) with category **Integration**.
3. Search for **17TRACK** in HACS and install it.
4. Restart Home Assistant.

### Manual

1. Copy the `custom_components/track17` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & services** → **Add integration**.
2. Search for **17TRACK**.
3. Enter your 17TRACK API key (found in your 17TRACK account under **Security Setting**).

## Using with voice assistants

To let Assist (or any exposed conversation agent) answer questions like "where are my packages", expose the `track17` sensors under **Settings** → **Voice assistants** → **Entities**.

Services (`track17.delete_package`, `track17.delete_delivered_packages`, `track17.register_package`) don't need to be exposed the same way - they can be called directly by name from an automation, script, or a conversation agent's own service-calling function, e.g. "delete the Csapágy package" → `track17.delete_package` with `identifier: Csapágy`, or "delete every delivered package" → `track17.delete_delivered_packages`.

## Deleting packages

Packages are never deleted automatically by this integration - once delivered, they stay tracked (and visible) until you delete them:

- Call `track17.delete_package` with a specific package's tag or tracking number to remove just that one.
- Press the **Delete delivered packages** button on your dashboard, or call `track17.delete_delivered_packages`, to remove every currently delivered package in one go.

Both immediately refresh the remaining sensors afterwards.

## License

MIT, see [LICENSE](LICENSE).
