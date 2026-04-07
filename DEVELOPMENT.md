# Aquamonix Flow Meter -- Development Guide

## Repository Structure

```
README.md               <-- User-facing app description
DEVELOPMENT.md          <-- This file
pyproject.toml          <-- Python project config and dependencies
Dockerfile              <-- Production Docker image
doover_config.json      <-- Doover platform metadata (generated)

src/aquamonix_water_meter/
  __init__.py           <-- Entry point (main function)
  application.py        <-- Core application logic and UI handlers
  app_config.py         <-- Configuration schema (Modbus ID, meter name, etc.)
  app_tags.py           <-- Declarative tags (display state, thresholds, pump control)
  app_ui.py             <-- UI definition (flow gauge, event counters, maintenance)
  app_state.py          <-- State machine (sleeping / awake_init / awake_rt)
  record.py             <-- Modbus register parser for the i500 meter

simulators/
  app_config.json       <-- Sample config for local development
  docker-compose.yml    <-- Orchestrates device agent, modbus interface, simulator, and app
  aquamonix_sim/
    main.py             <-- Modbus TCP server emulating an i500 meter
    pyproject.toml      <-- Simulator dependencies
    Dockerfile          <-- Simulator Docker image

tests/
  test_imports.py       <-- Import and basic validation tests
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker and Docker Compose (for simulator and deployment)

## Getting Started

### Install dependencies

```bash
uv sync
```

### Run locally (with simulator)

The simulator provides a Modbus TCP server that emulates an Aquamonix i500 meter, so you can develop and test without real hardware.

```bash
cd simulators
docker compose up --build
```

This starts four services:

| Service | Description |
|---------|-------------|
| `device_agent` | Doover device agent |
| `modbus_iface` | Modbus RTU/TCP bridge |
| `aquamonix_sim` | i500 meter simulator (TCP on port 5020) |
| `application` | This app, reading from the simulator |

### Run tests

```bash
uv run pytest tests/
```

## Architecture

### Data Flow

```
i500 Meter  -->  Modbus (RTU/TCP)  -->  modbus_iface  -->  Application  -->  Doover Platform
                                                              |
                                                              +--> Tags (pump control)
                                                              +--> Channels (alerts)
                                                              +--> UI (dashboard)
```

### State Machine

The application mirrors the i500's own sleep/wake behaviour:

| State | Description | Timeout |
|-------|-------------|---------|
| `initial` | Startup, transitions immediately to `awake_init` | -- |
| `sleeping` | Low-power mode, no Modbus requests. Duration adapts to battery voltage | 10.5 -- 52.5 min |
| `awake_init` | Waiting for the meter to report ready | 30s |
| `awake_rt` | Real-time reading mode, actively polling the meter | 1.5 min |

Sleep duration scales with battery voltage to conserve power:

| Voltage | Sleep Multiplier |
|---------|-----------------|
| > 12.9V | 1x (10.5 min) |
| 12.5 -- 12.9V | 1.5x |
| 12.2 -- 12.5V | 3x |
| <= 12.2V | 5x (52.5 min) |

### Modbus Registers

The app reads 42 input registers (type 4) starting at address 0 from the i500. Key registers:

| Register | Description | Conversion |
|----------|-------------|------------|
| 29 | Current flow (L/sec) | `L/sec * 86400 / 1,000,000` = ML/day |
| 30 | Battery voltage | raw / 10 = Volts |
| 31 | Solar voltage | raw / 10 = Volts |
| 32-33 | On-peak total (high/low words) | Combined 32-bit value in kilolitres |
| 34-35 | Off-peak total (high/low words) | Combined 32-bit value in kilolitres |
| 41 | Ready flag | 0 = ready, 1 = not ready |

Total volume = `(on_peak_kL + off_peak_kL) / 1000` = ML

### Tags

Tags in `app_tags.py` serve two purposes:

1. **Display state** -- bound to UI elements via tag references, updated each loop from Modbus readings (flow, voltage, totals, etc.)
2. **Persisted state** -- event counter baseline, last non-zero flow time, user-set thresholds
3. **Cross-app communication** -- `alert_triggered`, `alert_message_short`, `alert_message_long` are read by pump controller apps

### UI Handlers

User interactions are handled via `@ui.handler` decorators on the application class:

| Handler | Trigger | Action |
|---------|---------|--------|
| `alert_counter` | User sets alert threshold | Stores threshold in `tags.alert_threshold` |
| `shutdown_counter` | User sets shutdown threshold | Stores threshold in `tags.shutdown_threshold` |
| `reset_event` | User clicks "Reset Event" | Resets event counter baseline and clears thresholds |
| `get_now` | User clicks "Get Now" | Wakes the state machine from sleep for an immediate reading |

## Regenerating doover_config.json

After modifying the config schema:

```bash
uv run export-config
```

## Building the Docker Image

```bash
docker build -t aquamonix-flow-meter .
```

The Dockerfile produces a multi-platform image (amd64/arm64) using the `doover_device_base` base image.
