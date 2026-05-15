# Lumagen Radiance Pro Home Assistant Integration

![GitHub release](https://img.shields.io/github/v/release/johncarey70/lumagen-ha?style=flat-square)
[![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/johncarey70/lumagen-ha?style=flat-square)](https://github.com/johncarey70/lumagen-ha/issues)

A Home Assistant custom integration for Lumagen Radiance Pro video processors.

This integration communicates with a Lumagen Radiance Pro over either a direct serial connection or a TCP serial connection. It exposes the processor as a media player, remote, buttons, sensors, and Home Assistant actions.

## Features

- Setup from the Home Assistant UI
- Supports:
  - TCP serial connection
  - USB to Serial RS-232 Adapter
- Media player entity:
  - Power on
  - Standby
  - Input/source selection
  - Custom input labels
- Remote entity:
  - Menu navigation
  - Aspect controls
  - Input memory selection
  - NLS toggle
  - Auto-aspect controls
- Button entities:
  - Toggle NLS
  - Show Aspect
  - HDMI Input Restart
  - HDMI Output Restart
  - Refresh Info
- Sensors:
  - Current input/source
  - Input/output format, rate, and mode
  - Aspect information
  - Dynamic range
  - Output status
  - CMS/style information
  - Diagnostic Lumagen status fields
- Home Assistant actions:
  - Set one input label
  - Set multiple input labels
  - Display an on-screen message
  - Clear an on-screen message

## Installation

### HACS custom repository

1. Open Home Assistant.
2. Go to HACS.
3. Open the menu in the top right.
4. Choose Custom repositories.
5. Add this repository URL.

```text
   https://github.com/johncarey70/lumagen-ha
```
6. Select category Integration.
7. Install the integration.
8. Restart Home Assistant.

### Manual installation

Copy the integration folder into Home Assistant:

```text
custom_components/lumagen
```

The final layout should look like:

```text
custom_components/
`-- lumagen/
    |-- __init__.py
    |-- button.py
    |-- config_flow.py
    |-- const.py
    |-- coordinator.py
    |-- entity.py
    |-- manifest.json
    |-- media_player.py
    |-- remote.py
    |-- sensor.py
    |-- services.yaml
    |-- strings.json
    |-- switch.py
`-- translations/
    `-- en.json
```

Then restart Home Assistant.

## Setup

After installation:

1. Go to Settings -> Devices & services.
2. Click Add Integration.
3. Search for Lumagen.
4. Choose the connection type.

### Lumagen Setup

The following must be configured in the Lumagen Radiance Pro:

```text
MENU -> Other -> I/O Setup -> RS-232 Setup -> Echo -> On
MENU -> Other -> I/O Setup -> RS-232 Setup -> Delimiters -> Off
MENU -> Other -> I/O Setup -> RS-232 Setup -> Report mode changes -> Fullv5
Save
```

These settings are required so Home Assistant can correctly parse Lumagen responses and receive full status updates.

### TCP serial connection

Use this when the Lumagen Radiance Pro RS-232 port is connected through a TCP serial adapter.

You will need:

- Host/IP address
- TCP port

### USB to Serial RS-232 Adapter

Use this when the Lumagen Radiance Pro is connected directly to the Home Assistant host with a USB-to-RS-232 adapter.

You will need:

- Serial device path, for example:

```text
/dev/ttyS0
/dev/ttyUSB0
/dev/serial/by-id/...
```

- Baud rate, usually:

```text
9600
```

## Entities

### Media Player

The media player entity exposes the Lumagen Radiance Pro as a controllable device.

Supported features:

- Turn on
- Turn off / standby
- Select source

The source list is built from Lumagen input labels. The integration queries labels for inputs 1 through 8 because the Lumagen label command uses label indexes 0 through 7.

Inputs 9 through 10 are still selectable, but they use generic names:

```text
Input 9
Input 10
```

### Remote

The remote entity supports Home Assistant's remote.send_command action.

Supported command names include:

```text
alt
auto_aspect_disable
auto_aspect_enable
clear
down
exit
help
left
mema
memb
memc
memd
menu
nls
ok
right
show_aspect
source_aspect_16x9
source_aspect_1_85
source_aspect_1_90
source_aspect_2_00
source_aspect_2_20
source_aspect_2_35
source_aspect_2_40
source_aspect_4x3
source_aspect_lbox
up
```

Example:

```yaml
action: remote.send_command
target:
  entity_id: remote.lumagen_remote
data:
  command:
    - menu
    - down
    - ok
```

### Buttons

The integration creates buttons for common commands:

- Toggle NLS
- Show Aspect
- Refresh Info

Refresh Info reloads runtime information from the Lumagen without relying on a power cycle or input change.

### Sensors

The integration exposes Lumagen status sensors.

Common sensors include:

- Current Input
- Current Source
- Input Status
- Input Format
- Input Mode
- Input Rate
- Output Format
- Output Mode
- Output Rate
- Output Aspect
- Input Dynamic Range
- Input Memory
- Output On

Diagnostic sensors include:

- Detected Source Aspect
- Detected Source Raster Aspect
- Input Virtual Selected
- Physical Input Selected
- Output Color Space
- NLS Active
- Active Output CMS
- Active Output Style
- Current Source Content Aspect
- Input Config Number
- Output Mode 3D
- Input 3D Mode
- Input Raster Aspect
- Input Horizontal Resolution
- Output Horizontal Resolution

## Actions

### Set input label

Sets the custom name for one Lumagen input label.

Lumagen supports custom input label setting for inputs 1 through 8.

```yaml
action: lumagen.set_input_label
data:
  memory: A
  input_number: 2
  label: Roku 2A
```

This sends the Lumagen label command and then saves the configuration.

Valid memory values:

```text
A
B
C
D
```

The label is limited to 10 characters by the Lumagen.

### Set multiple input labels

Sets multiple labels in one action and saves the configuration once at the end.

```yaml
action: lumagen.set_input_labels
data:
  memory: A
  labels:
    - input_number: 1
      label: TiVo
    - input_number: 2
      label: Roku 2A
    - input_number: 3
      label: Apple TV
```

### Display message

Displays a message on the Lumagen on-screen display.

If only one Lumagen device is configured, `entity_id` can be omitted. If multiple Lumagen devices are configured, provide any Lumagen entity, such as the media player or remote entity, so the action can target the correct device.

The display message action supports two modes:

- `message` mode for a normal message that can auto-wrap or be forced onto one line.
- `line1` / `line2` mode for exact control of both Lumagen OSD lines.

Do not mix `message` with `line1` / `line2`. If `line1` or `line2` is supplied, explicit two-line mode is used.

#### Message mode

Use `message` for a normal message. By default, the integration word-wraps the message across the two Lumagen OSD lines.

```yaml
action: lumagen.display_message
data:
  message: Movie starting
  duration: 5
```

Use `message_placement` to force the message onto a specific OSD line.

```yaml
action: lumagen.display_message
data:
  message: Movie starting
  message_placement: line1
  duration: 5
```

Valid `message_placement` values are:

```text
auto
line1
line2
```

#### Explicit two-line mode

Use `line1` and/or `line2` when you want exact control over each OSD line.

```yaml
action: lumagen.display_message
data:
  line1: Volume
  line2: "==============="
  duration: 5
```

#### Centering

Use `center` to center line 1, line 2, or both lines.

```yaml
action: lumagen.display_message
data:
  line1: Volume
  line2: "==============="
  center: both
  duration: 5
```

Valid `center` values are:

```text
line1
line2
both
```

Omit `center` when no centering is needed.

#### Block character / volume bar

Use `block_char` to replace a chosen character with the Lumagen solid-block OSD character. This is useful for volume bars or progress bars.

```yaml
action: lumagen.display_message
data:
  line1: "Volume -35.0"
  line2: "==============="
  center: line1
  block_char: "="
  duration: 5
```

#### Persistent messages

`duration` is a Lumagen display duration value from 0 through 9. A value of 9 leaves the message on screen until cleared.

```yaml
action: lumagen.display_message
data:
  message: Intermission
  duration: 9
```

Messages are cleaned before being sent:

- Unsupported characters are removed.
- Lumagen supports 2 lines of up to 30 characters per line.
- Explicit line text is truncated to 30 characters per line.
- Auto-wrapped message text is split into up to two 30-character lines.

### Clear message

Clears a persistent Lumagen OSD message.

```yaml
action: lumagen.clear_message
```

## Runtime behavior

The integration is mostly event-driven.

At startup, it queries the Lumagen Radiance Pro for:

- Power state
- Current input
- Full status
- Input/output horizontal information

Input labels are loaded in the background after the integration starts so Home Assistant startup is not delayed.

At runtime, the integration listens for unsolicited Lumagen status events and updates entities when the Lumagen reports changes.

When a full input/status event is received, the integration also refreshes horizontal input/output information in the background.

## Notes about input labels

Lumagen's input label command supports inputs 1 through 8 using label indexes 0 through 7.

Because of that, this integration only reads and writes custom labels for inputs 1 through 8.

Inputs 9 through 18 remain selectable from the media player source list, but they use generic names.

## Troubleshooting

### Integration does not connect

Check the connection type.

For TCP serial connections:

- Confirm the IP address.
- Confirm the port.
- Confirm the TCP serial adapter is reachable.
- Confirm the adapter is configured for the Lumagen serial settings.

For USB to Serial RS-232 Adapter connections:

- Confirm the serial device path.
- Confirm Home Assistant has permission to access the serial device.
- Try a stable /dev/serial/by-id/... path if available.
- Confirm the baud rate is correct.

### Sources show generic Input names

Input labels are loaded in the background after startup. Wait a few seconds after Home Assistant starts.

Only inputs 1 through 8 support custom label queries through the Lumagen command used by this integration.

### Sensors are unknown

Some sensors depend on Lumagen full-status responses.

Use the Refresh Info button to force a refresh.

If values remain unknown, check Home Assistant logs for Lumagen communication errors.

### OSD message does not display

Check that the Lumagen Radiance Pro is powered on and accepting serial commands.

For persistent messages, use duration 9. Clear them with:

```yaml
action: lumagen.clear_message
```

## License

This project is licensed under the [MPL-2.0 License](LICENSE).
