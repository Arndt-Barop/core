---
title: WAGO I/O System
description: Instructions on how to integrate WAGO 750 series I/O systems into Home Assistant.
ha_category:
  - Binary sensor
  - Sensor
  - Switch
ha_release: 2025.2
ha_iot_class: Local Polling
ha_config_flow: true
ha_codeowners:
  - '@Arndt-Barop'
ha_domain: wago_io_system
ha_platforms:
  - binary_sensor
  - sensor
  - switch
ha_quality_scale: bronze
---

The **WAGO I/O System** integration allows you to monitor and control WAGO 750 series I/O modules in Home Assistant via Modbus TCP:
- Digital input modules (binary sensors)
- Digital output modules (switches)
- Analog input modules (sensors)
- Analog output modules (sensors) [read-only currently]

{% include integrations/config_flow.md %}

## Supported Devices

This integration supports the WAGO 750 series I/O system with a Modbus TCP coupler.

### Fieldbus Coupler (Required)
- WAGO 750-362 Modbus TCP Coupler

### Digital Input Modules
- WAGO 750-402 (2-channel, 24V DC)
- WAGO 750-404 (4-channel, 24V DC)
- WAGO 750-430 (8-channel, 24V DC)
- WAGO 750-432 (16-channel, 24V DC)
- Dynamic digital input modules (0x8801-0x88FF) automatically detected

### Digital Output Modules
- WAGO 750-504 (4-channel, 24V DC)
- WAGO 750-508 (8-channel, 24V DC)
- WAGO 750-530 (16-channel, 24V DC)
- Dynamic digital output modules (0x8802-0x88FF) automatically detected

### Analog Input Modules
- WAGO 750-451 (4-channel, 4-20mA)
- WAGO 750-455 (2-channel, ±10V)
- WAGO 750-469 (4-channel, 4-20mA with Highway Addressable Remote Transducer)
- WAGO 750-471 (4-channel, 0-10V)
- WAGO 750-473 (4-channel, 0-20mA)

### Analog Output Modules
- WAGO 750-550 (4-channel, 0-10V) [read-only]
- WAGO 750-552 (4-channel, 4-20mA) [read-only]

## Prerequisites

- A WAGO 750 series I/O system with a Modbus TCP coupler (e.g., 750-362)
- The coupler must be connected to your network
- You need to know the IP address of the coupler
- Modbus TCP must be enabled (default port: 502)
- I/O modules must be installed and powered

## Configuration

The integration is set up via the Home Assistant user interface.

1. Go to **{% my integrations title="Settings > Devices & Services" %}**
2. Click the **{% my config_flow_start domain=page.ha_domain title="Add Integration" %}** button
3. Search for **WAGO I/O System**
4. Enter the following information:
   - **Host**: The IP address of your WAGO coupler (e.g., "192.168.2.44")
   - **Port**: Modbus TCP port (default: 502)
   - **Timeout**: Communication timeout in seconds (1-30, default: 3)

The integration will test the connection, read the controller MAC address, and automatically detect all installed I/O modules.

## Automatic Module Detection

The integration automatically detects all I/O modules installed in your WAGO system:

- Reads configuration registers from the coupler
- Identifies module types based on module codes
- Creates appropriate entities for each module channel
- Groups entities by module in the device registry

**Supported module types:**
- Static modules with known module codes (750-4xx, 750-5xx series)
- Dynamic modules with 0x8xxx codes (automatically parsed for channel count)

## Entities

### Binary Sensors (Digital Inputs)

For each digital input channel, a binary sensor is automatically created:

**Entity naming:**
- Pattern: `binary_sensor.<controller>_<module_type>_input_<channel>`
- Example: `binary_sensor.wago_io_digital_input_8_bit_input_1`

**Properties:**
- Device class: None (generic)
- States: `on` (active) / `off` (inactive)
- Update interval: 1 second

**Modbus details:**
- Function code: 2 (Read Discrete Inputs)
- Addressing: Bit-based (per channel)

### Sensors (Analog Inputs)

For each analog input channel, a sensor is automatically created:

**Entity naming:**
- Pattern: `sensor.<controller>_<module_type>_input_<channel>`
- Example: `sensor.wago_io_4_channel_analog_input_4_20ma_input_1`

**Properties:**
- Device class: Voltage or Current (based on module specification)
- Units: Volt (V) or Milliampere (mA)
- State class: Measurement
- Update interval: 1 second

**Modbus details:**
- Function code: 4 (Read Input Registers)
- Addressing: Register-based (16-bit values)

### Switches (Digital Outputs)

For each digital output channel, a switch entity is automatically created:

**Entity naming:**
- Pattern: `switch.<controller>_<module_type>_output_<channel>`
- Example: `switch.wago_io_digital_output_8_bit_output_1`

**Properties:**
- Device class: Outlet
- Actions: Turn On / Turn Off
- Update interval: 1 second (state read-back)

**Modbus details:**
- Read: Function code 1 (Read Coils)
- Write: Function code 5 (Write Single Coil)
- Addressing: Bit-based (per channel)

### Devices

Each I/O module is represented as a separate device in Home Assistant:

**Device properties:**
- Name: Based on module type (e.g., "750-451 4-Channel Analog Input 4-20mA")
- Manufacturer: WAGO
- Model: Module part number (e.g., "750-451")
- Identifiers: Unique based on controller and module position

**Coupler device:**
- MAC address as unique identifier
- Network connection information
- Groups all child module devices

## Multiple Controllers

You can add multiple WAGO I/O systems:

1. Each controller must have a unique IP address
2. Repeat the setup process for each controller
3. Each system is managed independently
4. Entities are uniquely identified by controller MAC address

**Example setup:**
- Controller 1 (192.168.2.44): Main building
- Controller 2 (192.168.2.45): Garage
- Controller 3 (192.168.2.40): Workshop

All systems update independently with their own polling cycles.

## Reconfiguration

You can change the IP address or port of your WAGO controller without removing the integration:

1. Go to **{% my integrations title="Settings > Devices & Services" %}**
2. Find your WAGO I/O System integration
3. Click the three dots (⋮) menu and select **Reconfigure**
4. Enter the new IP address or port
5. The integration will reload automatically

{% note %}
The MAC address is used as the unique identifier. Changing the controller hardware will create a new integration instance.
{% endnote %}

## Diagnostics

The integration supports downloading diagnostic information for troubleshooting:

1. Go to **{% my integrations title="Settings > Devices & Services" %}**
2. Find your WAGO I/O System integration
3. Click the three dots (⋮) menu and select **Download diagnostics**
4. A JSON file will be downloaded with:
   - Configuration data
   - Detected modules
   - Current I/O states
   - Connection information

Sensitive information (IP addresses) is automatically redacted from the diagnostics file.

## Troubleshooting

### Cannot connect during setup

**Possible causes:**
- The coupler is not powered on or not connected to the network
- The IP address is incorrect
- A firewall is blocking Modbus TCP traffic on port 502
- The 750-362 coupler is not installed or not configured

**Solutions:**
- Verify the coupler is reachable by pinging the IP address
- Check the coupler's status LED (should be green)
- Ensure Modbus TCP is enabled on the coupler
- Check your network firewall settings (allow TCP port 502)
- Try increasing the timeout setting (5-10 seconds)

### Controller shows as unavailable

**Possible causes:**
- Network connectivity issues
- The coupler has been powered off
- The IP address has changed
- Modbus timeout is too short

**Solutions:**
- Check network connectivity (ping test)
- Use a static IP or DHCP reservation for the coupler
- Use the reconfiguration flow to update the IP address
- Increase the Modbus timeout in the reconfiguration

### Entities show "unavailable"

This is **normal behavior** when:
- The WAGO controller is not powered or not reachable
- There is a temporary communication issue
- An I/O module has been removed or is malfunctioning

**Solutions:**
- Check the network connection to the controller
- Verify the coupler is powered on (green LED)
- Check all I/O modules are properly seated and powered
- Wait for the communication to recover (entities will automatically become available)
- Check logs for specific error messages

### Digital inputs toggling rapidly

**This issue was fixed in the current version!** Early development versions incorrectly read digital inputs from registers instead of coils.

**If you still see this:**
- Ensure you have the latest version installed
- Check logs for Modbus communication errors
- Download diagnostics and report the issue

### Modules not detected

**Possible causes:**
- Modules not properly seated in the I/O rack
- Modules not powered (check bus power supply)
- Configuration registers not readable from the coupler
- Module type not yet supported by the integration

**Solutions:**
- Power cycle the entire I/O system
- Verify all modules are fully inserted and locked
- Check for error LEDs on modules or coupler
- Verify the coupler is a supported type (750-362 or compatible)
- Use WAGO configuration software to verify I/O system configuration
- Check the integration logs for unknown module codes

### Analog values incorrect or out of range

**Possible causes:**
- Incorrect wiring (polarity, loop power)
- Sensor configuration issues
- Wrong module type for the sensor

**Solutions:**
- Verify sensor wiring matches module specifications:
  - 4-20mA modules require loop power
  - Voltage modules require proper ground reference
  - Check polarity for ±10V modules
- Ensure sensors are within the module's input range
- Use WAGO configuration tools to test the module directly
- Check sensor calibration and scaling

### Switches do not control outputs

**Possible causes:**
- Output module not powered
- Load wiring issues
- Module in error state
- Modbus write permissions

**Solutions:**
- Check output module power supply (24V DC)
- Verify load connections (observe LED on module)
- Check for short circuits or overload conditions
- Verify Modbus TCP settings allow writes (Function Code 5)
- Test output manually using WAGO configuration software

## Technical Details

### Communication Protocol

**Modbus TCP:**
- Default port: 502
- Unit ID: 1
- Timeout: 3 seconds (configurable)
- Polling interval: 1 second

**Function codes used:**
- FC1: Read Coils (digital outputs)
- FC2: Read Discrete Inputs (digital inputs)
- FC3: Read Holding Registers (analog outputs)
- FC4: Read Input Registers (analog inputs)
- FC5: Write Single Coil (digital output control)

### Addressing Scheme

**Digital I/O (Coils):**
- Bit-based addressing starting at bit 0
- Offset calculated from module position in I/O rack
- Each module's channels are sequential

**Analog I/O (Registers):**
- Register-based addressing starting at register 0
- Offset calculated from module position
- Each channel occupies one 16-bit register

**Configuration Registers:**
- Starting at register 0
- Each module occupies multiple registers:
  - Module code (16-bit)
  - Channel count
  - Process image offset
  - Additional module-specific data

### Data Update Coordinator

The integration uses a centralized data coordinator with four separate data structures:

1. **Digital Inputs** (bit array)
   - Read via FC2 (Read Discrete Inputs)
   - Updated every second
   - Binary sensors read from this array

2. **Digital Outputs** (bit array)
   - Read via FC1 (Read Coils)
   - Updated every second
   - Switches read from this array for state verification

3. **Analog Inputs** (register array)
   - Read via FC4 (Read Input Registers)
   - Updated every second
   - Sensors read from this array

4. **Analog Outputs** (register array)
   - Read via FC3 (Read Holding Registers)
   - Updated every second
   - Currently read-only (write support planned)

**Error handling:**
- Failed updates raise UpdateFailed exception
- Entities automatically marked as unavailable
- Connection issues logged once (not repeated)
- Recovery automatically detected and logged

### Module Registry

The integration includes a comprehensive module registry with:

- Module type enumeration (DIGITAL_INPUT, DIGITAL_OUTPUT, ANALOG_INPUT, ANALOG_OUTPUT)
- Module specifications (code, name, channel count, I/O type)
- Helper functions (is_digital(), is_analog())
- Support for dynamic module detection (0x8xxx codes)

**Dynamic module support:**
- Bit 15 in module code indicates dynamic module
- Lower byte contains channel count
- 0x8801: Dynamic digital input modules
- 0x8802: Dynamic digital output modules

### Performance Characteristics

**Startup:**
- Initial register read: 32 registers (optimized)
- Module detection: Single Modbus transaction
- Fast integration load time

**Runtime:**
- Update interval: 1 second (all I/O)
- Parallel updates: Unlimited (coordinator prevents conflicts)
- Separate Modbus calls for each I/O type
- Minimal network traffic (only changed values logged)

**Write operations:**
- Single coil writes (FC5) for immediate response
- No read-modify-write cycles for digital outputs
- Atomic operations prevent race conditions

### Integration Quality

**Current status:**
- Quality scale: Bronze (16/19 rules met)
- Test coverage: 88% (target: 95%)
- Live hardware verified: Multiple controllers (192.168.2.44, 192.168.2.45)

**Bronze tier requirements met:**
- ✅ Config flow (UI setup)
- ✅ Entity unique IDs
- ✅ Entity unavailability handling
- ✅ Parallel updates configuration
- ✅ Reauthentication support
- ✅ Reconfiguration support
- ✅ Diagnostics support

**Pending improvements:**
- Increase test coverage to 95%
- Add entity platform tests
- Comprehensive documentation
- Translation support (planned for Silver tier)

## Module Type Comparison

| Feature | Digital Modules | Analog Modules |
|---------|----------------|----------------|
| Addressing | Coils (bit-based) | Registers (word-based) |
| Read Function | FC1 (out), FC2 (in) | FC3 (out), FC4 (in) |
| Write Function | FC5 (single) | FC16 (multiple)* |
| Data Type | Boolean | 16-bit integer |
| Entity Type | Binary Sensor / Switch | Sensor |
| Device Class | Outlet | Voltage / Current |
| Update Rate | 1 second | 1 second |

*Analog output write support planned for future release

## Known Limitations

**Current version limitations:**

1. **Analog outputs read-only**: Writing to analog output modules (750-550, 750-552) is not yet implemented
2. **Basic scaling**: Analog values are raw register values; advanced scaling/calibration not implemented
3. **No special module support**: Temperature modules, RTD converters, and other specialized modules not yet supported
4. **Static polling interval**: Update interval is fixed at 1 second (not user-configurable by design)

**Planned future enhancements:**

- Analog output control (number entities for 750-550, 750-552)
- Additional analog module types (temperature, RTD, thermocouple)
- Advanced scaling and calibration options
- Entity translations for multilingual support
- Device class optimization for specific module types

## Use Cases

**Industrial Control:**
- Machine automation (start/stop buttons, status indicators)
- Process control (valve control, pump control)
- Safety systems (emergency stop monitoring)

**Building Automation:**
- Lighting control (on/off switches)
- HVAC control (damper control, fan control)
- Access control (door sensors, lock control)

**Monitoring:**
- Temperature monitoring (with temperature converters)
- Pressure monitoring (4-20mA transducers)
- Flow measurement (analog sensors)
- Level detection (ultrasonic, hydrostatic sensors)

**Mixed Applications:**
- Water treatment (analog sensors + digital pump control)
- Energy monitoring (current measurement + status signals)
- Greenhouse automation (temperature + valve control)

## Removal

To remove the integration:

1. Go to **{% my integrations title="Settings > Devices & Services" %}**
2. Find your WAGO I/O System integration
3. Click the three dots (⋮) menu and select **Delete**
4. Confirm the deletion

All associated entities and devices will be removed from Home Assistant.

{% note %}
This will not affect the physical WAGO hardware or its configuration. The I/O system will continue to operate normally.
{% endnote %}
