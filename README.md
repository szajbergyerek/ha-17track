# 17TRACK for Home Assistant

<img src="logo.png" alt="17TRACK for Home Assistant logo" width="128" height="128">

A Home Assistant custom integration for [17TRACK](https://www.17track.net/), a universal package tracking service. Register your packages on the 17TRACK website or app, and this integration will surface each one as a sensor entity in Home Assistant.

## Features

- One sensor per package registered on your 17TRACK account, created and removed automatically.
- Sensor state is a human-readable sentence: `On <date> package "<name>": <latest event>`.
- Attributes with structured data (tracking number, carrier, package status, last event time) for use in automations and dashboards.
- Polls the 17TRACK API every 30 minutes.

Package registration itself is not handled by this integration; register tracking numbers via the 17TRACK website or app, and this integration will pick them up automatically.

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

## License

MIT, see [LICENSE](LICENSE).
