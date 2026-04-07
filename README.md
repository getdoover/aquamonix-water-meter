
# Aquamonix Flow Meter

<img src="https://doover.com/wp-content/uploads/Doover-Logo-Landscape-Navy-padded-small.png" alt="App Icon" style="max-width: 300px;">

**Doover application for monitoring water flow via the [Aquamonix i500 Transmitter](https://aquamonix.com.au/product/i500-transmitter/)**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/getdoover/aquamonix-flow-meter)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/getdoover/aquamonix-flow-meter/blob/main/LICENSE)

[Getting Started](#-getting-started) • [Configuration](#configuration) • [Developer](https://github.com/getdoover/aquamonix-flow-meter/blob/main/DEVELOPMENT.md) • [Need Help?](#need-help)

<br/>

## Overview

This application connects to [Aquamonix i500 series](https://aquamonix.com.au/product/i500-transmitter/) flow meter transmitters via Modbus to provide real-time water flow monitoring, event-based alerting, and pump shutdown control through the Doover platform.

Key capabilities:

- **Real-time flow monitoring** -- reads current flow rate (ML/day), cumulative meter totals, battery and solar voltages from the i500 via Modbus
- **Event-based alerting** -- tracks water volume per pumping event and sends notifications when configurable thresholds are exceeded
- **Pump shutdown control** -- triggers automatic pump shutdown when an event volume target is reached
- **Adaptive battery management** -- adjusts sleep/wake cycles based on battery voltage to conserve power in remote installations
- **Maintenance tracking** -- records battery change dates, service notes, and telemetry for field teams

<br/>

## Getting Started

This Doover App can be managed via the Doover CLI and installed onto devices through the Doover platform.

### Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| **Modbus ID** | Device ID of the i500 meter on the Modbus network | *required* |
| **Meter Name** | User-friendly display name for the meter | *required* |
| **Max Flow** | Maximum expected flow rate for the meter (ML/day), used for gauge scaling | *required* |
| **Allow Shutdown** | Enable the app to trigger pump shutdown when a volume target is reached | `true` |
| **Modbus Config** | Modbus connection settings (bus type, serial/TCP parameters) | serial defaults |

<br/>

## Integrations

### Tags

This app exposes the following tags for use by other applications (e.g. pump controllers):

| Tag | Type | Description |
|-----|------|-------------|
| **alert_triggered** | boolean | Set to `true` when the pump shutdown volume target is exceeded |
| **alert_message_short** | string | Short description of the shutdown reason |
| **alert_message_long** | string | Detailed shutdown message including the volume reached |

### Channels

| Channel | Description |
|---------|-------------|
| **significantEvent** | Publishes a notification message when the alert volume threshold is exceeded during an event |

### Dependencies

- **Modbus Interface** (`doover_modbus_iface`) -- provides the Modbus RTU/TCP bridge that this app communicates through to reach the i500 transmitter

<br/>

### Need Help?

- Email: support@doover.com
- [Doover Documentation](https://docs.doover.com)
- [Developer Guide](https://github.com/getdoover/aquamonix-flow-meter/blob/main/DEVELOPMENT.md)

<br/>

## Version History

### v1.0.0 (Current)
- Initial release
- Real-time flow monitoring via Modbus
- Event-based alerting and pump shutdown control
- Adaptive battery-aware sleep/wake cycles
- Maintenance and telemetry UI

<br/>

## License

This app is licensed under the [Apache License 2.0](https://github.com/getdoover/aquamonix-flow-meter/blob/main/LICENSE).
