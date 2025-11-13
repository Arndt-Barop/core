# WAGO I/O System Integration

This integration enables the connection of WAGO 750 series I/O systems to Home Assistant via Modbus-TCP, providing seamless control of digital and analog I/O modules.

## Supported Devices

The integration supports the following WAGO devices:

### Fieldbus Couplers
- **[750-362](https://www.wago.com/de/io-systeme-feldbus-couplers/modbus-tcp-coupler/p/750-362)** - Modbus TCP Coupler ✅ **Hardware tested**

### Digital Input Modules
- **[750-402](https://www.wago.com/de/io-systeme-digital/digitale-eingangsklemme/p/750-402)** - 2-Channel Digital Input 24V DC
- **[750-404](https://www.wago.com/de/io-systeme-digital/digitale-eingangsklemme/p/750-404)** - 4-Channel Digital Input 24V DC
- **[750-430](https://www.wago.com/de/io-systeme-digital/digitale-eingangsklemme/p/750-430)** - 8-Channel Digital Input 24V DC
- **[750-432](https://www.wago.com/de/io-systeme-digital/digitale-eingangsklemme/p/750-432)** - 16-Channel Digital Input 24V DC
- **Dynamic Digital Input Modules** - Auto-detected modules (0x8801-0x88FF) ✅ **Hardware tested (8-bit)**

### Digital Output Modules
- **[750-504](https://www.wago.com/de/io-systeme-digital/digitale-ausgangsklemme/p/750-504)** - 4-Channel Digital Output 24V DC
- **[750-508](https://www.wago.com/de/io-systeme-digital/digitale-ausgangsklemme/p/750-508)** - 8-Channel Digital Output 24V DC
- **[750-530](https://www.wago.com/de/io-systeme-digital/digitale-ausgangsklemme/p/750-530)** - 16-Channel Digital Output 24V DC
- **Dynamic Digital Output Modules** - Auto-detected modules (0x8802-0x88FF) ✅ **Hardware tested (8-bit)**

### Analog Input Modules
- **[750-451](https://www.wago.com/de/io-systeme-analog/analog-eingangsklemme/p/750-451)** - 4-Channel Analog Input 4-20mA ✅ **Hardware tested**
- **[750-455](https://www.wago.com/de/io-systeme-analog/analog-eingangsklemme/p/750-455)** - 2-Channel Analog Input ±10V ✅ **Hardware tested**
- **[750-469](https://www.wago.com/de/io-systeme-analog/analog-eingangsklemme/p/750-469)** - 4-Channel Analog Input 4-20mA with Highway Addressable Remote Transducer
- **[750-471](https://www.wago.com/de/io-systeme-analog/analog-eingangsklemme/p/750-471)** - 4-Channel Analog Input 0-10V
- **[750-473](https://www.wago.com/de/io-systeme-analog/analog-eingangsklemme/p/750-473)** - 4-Channel Analog Input 0-20mA

### Analog Output Modules
- **[750-550](https://www.wago.com/de/io-systeme-analog/analog-ausgangsklemme/p/750-550)** - 4-Channel Analog Output 0-10V
- **[750-552](https://www.wago.com/de/io-systeme-analog/analog-ausgangsklemme/p/750-552)** - 4-Channel Analog Output 4-20mA

**⚠️ Important:**
- All modules must be installed in a WAGO 750 I/O system with a Modbus TCP coupler (e.g., 750-362)
- The coupler must be configured with a static IP address or DHCP reservation
- Module detection is automatic based on the I/O system configuration
- Digital modules use Coil addressing (Function Codes 1/2/5)
- Analog modules use Register addressing (Function Codes 3/4)

## Hardware Verification

The following hardware configurations have been **live tested** and verified working:

### Test System 1 (192.168.2.44)
- ✅ 750-362 Modbus TCP Coupler
- ✅ Dynamic Digital Output 8-bit (0x8802)
- ✅ Dynamic Digital Input 8-bit (0x8801)
- ✅ 750-451 4-Channel Analog Input 4-20mA
- ✅ 750-455 2-Channel Analog Input ±10V

### Test System 2 (192.168.2.45)
- ✅ 750-362 Modbus TCP Coupler
- ✅ Additional I/O modules (mixed digital/analog)

**Status:** All digital inputs show stable values (no toggling), analog sensors display correct measurements, and digital outputs respond correctly to switch commands.

## Installation

### Via UI (recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for "WAGO I/O System"
4. Follow the setup wizard:
   - **Host**: The IPv4 address of the WAGO coupler (e.g., "192.168.2.44")
   - **Port**: The Modbus-TCP port (default: 502)
   - **Timeout**: Communication timeout in seconds (1-30, default: 3)

The integration will:
- Test the connection to the WAGO coupler
- Read the MAC address for unique device identification
- Automatically detect all installed I/O modules
- Create entities for all inputs and outputs

### Via configuration.yaml (deprecated)

Manual configuration via `configuration.yaml` is no longer supported. Please use the UI-based setup wizard.

## Available Entities

The integration automatically creates entities based on the detected I/O modules:

### Binary Sensors (Digital Inputs)

For each digital input channel, a binary sensor is created:

- **Entity ID**: `binary_sensor.<device>_<module_name>_input_<channel>`
- **Example**: `binary_sensor.wago_io_digital_input_8_bit_input_1`
- **Device Class**: None (generic binary sensor)
- **States**: `on` (input active) / `off` (input inactive)

### Sensors (Analog Inputs)

For each analog input channel, a sensor is created:

- **Entity ID**: `sensor.<device>_<module_name>_input_<channel>`
- **Example**: `sensor.wago_io_4_channel_analog_input_4_20ma_input_1`
- **Device Class**: Voltage or Current (based on module type)
- **Units**: Volt (V) or Milliampere (mA) based on module specification
- **State Class**: Measurement (for historical tracking)

### Switches (Digital Outputs)

For each digital output channel, a switch entity is created:

- **Entity ID**: `switch.<device>_<module_name>_output_<channel>`
- **Example**: `switch.wago_io_digital_output_8_bit_output_1`
- **Device Class**: Outlet (generic controllable output)
- **Actions**: Turn On / Turn Off

### Devices

Each detected I/O module is represented as a device in Home Assistant:

- **Device Name**: Based on module type (e.g., "750-451 4-Channel Analog Input 4-20mA")
- **Identifiers**: Unique per module based on position in I/O system
- **Manufacturer**: WAGO
- **Model**: Module part number (e.g., "750-451")

The coupler itself is also represented as a device with:
- **MAC Address**: Used for unique identification
- **Connections**: Network MAC address
- **Firmware Version**: If available from coupler

## Multiple Controllers

You can add multiple WAGO I/O systems to Home Assistant. Simply repeat the setup process for each additional controller with a different IP address. Each system will be independently managed with its own set of entities.

**Example scenario:**
- System 1 (192.168.2.44): Main building automation
- System 2 (192.168.2.45): Garage control
- System 3 (192.168.2.40): Workshop I/O

All systems can coexist and are updated independently.

## Features

- ✅ UI-based setup (no YAML required)
- ✅ Automatic module detection (digital and analog I/O)
- ✅ Multiple WAGO controllers supported
- ✅ Dynamic digital module support (0x8xxx modules)
- ✅ Separate handling of digital (Coils) and analog (Registers) I/O
- ✅ Automatic reconnection on connection issues
- ✅ Reauthentication flow for credential changes
- ✅ Reconfiguration flow (change IP/port without removing integration)
- ✅ Entity unavailability detection (marks entities as "unavailable" when controller is offline)
- ✅ Intelligent logging (single warning on connection issues, recovery notifications)
- ✅ Diagnostics support for troubleshooting
- ✅ Device registry integration (all modules grouped by controller)
- ✅ Unique entity IDs based on controller MAC address

## Polling & Performance

- **Polling Interval**: 1 second (optimized for industrial control)
  - Digital inputs updated via Coils (Function Code 2)
  - Digital outputs read via Coils (Function Code 1)
  - Analog inputs updated via Input Registers (Function Code 4)
  - Analog outputs read via Holding Registers (Function Code 3)
- **Parallel Updates**: Unlimited (0) - coordinator-based updates prevent overwhelming the controller
- **Write Operations**: Switch entities use write_single_coil (Function Code 5) for immediate response

**Performance Notes:**
- Initial register read optimized to 32 registers (fast startup)
- Separate data structures for digital and analog I/O minimize Modbus traffic
- Bit-level addressing for digital I/O ensures accurate state representation
- No unnecessary read-modify-write cycles

## Troubleshooting

### Connection fails

1. **Check network:**
   - Verify the WAGO coupler is reachable at the specified IP address
   - Ping test: `ping <IP-address>`
   - Ensure the Modbus-TCP port is correct (default: 502)

2. **Coupler configuration:**
   - Is the 750-362 (or compatible) coupler correctly installed?
   - Is the status LED on the coupler lit green?
   - Has the coupler been assigned an IP address?
   - Is Modbus TCP enabled on the coupler?

3. **Firewall:**
   - Check firewall settings (TCP port 502)
   - Home Assistant must be able to access the device

4. **Modbus timeout:**
   - Try adjusting the timeout (3-10 seconds) in the reconfiguration flow
   - Longer timeouts help with slower or heavily loaded systems

5. **Module detection:**
   - The integration reads configuration registers from the coupler
   - If module detection fails, verify the I/O system is powered and modules are seated correctly

### Entities show no values

- Wait 1-2 seconds after setup (polling interval)
- Check logs for error messages: **Settings** → **System** → **Logs**
- Entities will be marked as "unavailable" if the controller is unreachable

### Digital inputs toggling rapidly

**This should NOT happen anymore!** This was a known issue in early development where digital inputs were incorrectly read from Holding Registers.

**If you still see this:**
1. Check that you're using the latest version of the integration
2. Verify the coordinator is using Coils (FC2) for digital inputs
3. Check logs for any Modbus communication errors
4. Report the issue with diagnostics data

### Entities marked as "unavailable"

This is normal behavior when:
- The WAGO controller is not powered on or not reachable on the network
- There is a temporary communication issue
- The network connection is lost

**Solutions:**
- Check the network connection to the controller
- Verify the controller is powered on
- Check that all I/O modules are seated correctly and powered
- When the controller is reachable again, entities will automatically become available
- You will receive an info message in the log when the controller comes back online

### IP address has changed

1. Go to **Settings** → **Devices & Services**
2. Click the three dots next to "WAGO I/O System"
3. Select "Reconfigure"
4. Enter the new IP address

### Modules not detected

**Possible causes:**
- Modules not properly seated in the I/O rack
- Modules not powered (check bus power supply)
- Configuration registers not readable

**Solutions:**
- Power cycle the entire I/O system
- Verify modules are fully inserted and locked
- Check for error LEDs on modules or coupler
- Ensure the coupler is the correct type (750-362 or compatible)
- Use WAGO configuration software to verify I/O system status

### Analog values incorrect

**Possible causes:**
- Incorrect scaling or unit conversion
- Sensor wiring issues (4-20mA loop, voltage reference)
- Module configuration issues

**Solutions:**
- Verify sensor wiring matches module specifications
- Check that 4-20mA sensors have proper loop power
- Verify voltage inputs are within ±10V or 0-10V range
- Use WAGO configuration tools to test module directly

## Technical Details

### Modbus Communication

**Digital I/O (Coils):**
- **Read Digital Inputs**: Function Code 2 (Read Discrete Inputs)
- **Read Digital Outputs**: Function Code 1 (Read Coils)
- **Write Single Output**: Function Code 5 (Write Single Coil)
- **Addressing**: Bit-based (0-based index per module channel count)

**Analog I/O (Registers):**
- **Read Analog Inputs**: Function Code 4 (Read Input Registers)
- **Read Analog Outputs**: Function Code 3 (Read Holding Registers)
- **Write Analog Output**: Function Code 16 (Write Multiple Registers) [future implementation]
- **Addressing**: Register-based (0-based index per module register count)
- **Data Format**: 16-bit signed integer

### Module Detection

**Module Registry:**
- Reads configuration registers from coupler (starting at register 0)
- Each module identified by 16-bit module code
- Bit 15 indicates dynamic digital modules (0x8xxx range)
- process_image_offset field indicates:
  - Bit offset for digital modules (relative to I/O start)
  - Register offset for analog modules (relative to I/O start)

**Supported Detection:**
- Static modules: Exact match in MODULE_REGISTRY
- Dynamic modules: Bit 15 detection (0x8xxx)
  - 0x8801: Digital Input modules
  - 0x8802: Digital Output modules
  - Channel count extracted from lower byte

### Data Update Coordinator

**Four Separate Data Structures:**
1. `digital_inputs` (bit array) - Read via FC2
2. `digital_outputs` (bit array) - Read via FC1
3. `analog_inputs` (register array) - Read via FC4
4. `analog_outputs` (register array) - Read via FC3

**Update Strategy:**
- Coordinator updates all four structures every second
- Entities read from appropriate structure based on module type
- Failed updates raise UpdateFailed exception, marking entities unavailable
- Automatic recovery when communication restored

### Integration Quality
- **Quality scale**: Bronze (16/19 rules met)
- **Standards**: Home Assistant integration best practices
- **Testing**: 88% test coverage (target: 95%)
- **Live verified**: Multiple WAGO controllers (192.168.2.44, .45, .40)

## Module Type Comparison

| Feature | Digital Modules | Analog Modules |
|---------|----------------|----------------|
| **Addressing** | Coils (bit-based) | Registers (word-based) |
| **Read Function** | FC1 (out), FC2 (in) | FC3 (out), FC4 (in) |
| **Write Function** | FC5 (single coil) | FC16 (multiple registers) |
| **Data Type** | Boolean (on/off) | 16-bit integer |
| **Entity Type** | Binary Sensor, Switch | Sensor |
| **Update Rate** | 1 second | 1 second |
| **Detection** | 0x8xxx dynamic support | Static registry |

## Use Cases

**Digital I/O:**
- Building automation (lights, pumps, valves)
- Industrial control (conveyor belts, motors, alarms)
- Safety systems (emergency stop, door contacts)
- Status monitoring (machine running, fault signals)

**Analog I/O:**
- Temperature monitoring (PT100, thermocouple converters)
- Pressure sensing (4-20mA transducers)
- Flow measurement (0-10V signals)
- Level detection (ultrasonic, hydrostatic)
- Energy monitoring (current transformers)

**Mixed Applications:**
- HVAC systems (analog temperatures, digital dampers)
- Water treatment (analog sensors, digital pumps)
- Manufacturing (analog process values, digital machine control)

## Future Enhancements

Planned features for future releases:

- 🔄 Analog output control (write to 750-550, 750-552 modules)
- 📊 Additional analog module types (temperature, RTD, thermocouple)
- 🔧 Advanced module configuration (calibration, scaling)
- 📈 Increased test coverage to 95%+ (Gold tier)
- 📝 Comprehensive entity platform tests
- 🌐 Translation support for entity names
- 🎯 Device class optimization for specific module types

## Removal

To remove the integration:

1. Go to **Settings** → **Devices & Services**
2. Find your WAGO I/O System integration
3. Click the three dots (⋮) menu and select **Delete**
4. Confirm the deletion

All associated entities and devices will be removed.

**Note:** This will not affect the physical WAGO hardware or its configuration.
