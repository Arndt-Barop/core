"""WAGO Energy Meter device communication."""

import logging
import re
import struct
import threading
import time

from pyModbusTCP.client import ModbusClient

_LOGGER = logging.getLogger(__name__)


class WagoMeter:
    """Base class for WAGO meters with Modbus RTU communication."""

    def __init__(
        self,
        ip: str,
        port: int,
        interval: int,
        timeout: int = 5,
        device_type: str = "mid_meter",
    ) -> None:
        """Initialize the WAGO meter.

        Args:
            ip: IP address of the WAGO Modbus TCP gateway
            port: Modbus TCP port
            interval: Polling interval in seconds
            timeout: Modbus timeout in seconds
            device_type: Type of WAGO device (mid_meter, 2857_570)

        """
        self._running = True
        self._interval = int(interval)
        self._timeout = int(timeout)
        self._device_type = device_type

        _LOGGER.debug("INIT Process - Device Type: %s", device_type)
        self._ip = ip
        _LOGGER.debug("MOD IP: %s", self._ip)
        if not self._valid_ip(self._ip):
            raise ValueError("Invalid IP address given")

        self._port = int(port)
        _LOGGER.debug("MOD PORT: %s", self._port)

        # Initialize values based on device type
        self._initialize_values()
        self._last_read_successful = False

        try:
            self._client = ModbusClient(
                host=self._ip,
                port=self._port,
                unit_id=1,
                auto_open=True,
                auto_close=True,
                timeout=self._timeout,
            )
        except ValueError as err:
            _LOGGER.error("Error with host or port params: %s", err)

        # Thread will be started by calling start() method
        self._modthread: threading.Thread | None = None

    def start(self) -> None:
        """Start the background Modbus reading thread.

        This method must be called after initialization to begin
        polling the WAGO device for measurements.
        """
        if self._modthread is None:
            _LOGGER.debug("Starting Modbus read thread for %s", self._device_type)
            self._modthread = threading.Thread(target=self._read_values, daemon=True)
            self._modthread.start()
        else:
            _LOGGER.warning("Modbus read thread already running")

    def _initialize_values(self) -> None:
        """Initialize measurement values based on device type."""
        # Common values for all device types
        self._U_L1 = 0.0
        self._U_L2 = 0.0
        self._U_L3 = 0.0
        self._I_L1 = 0.0
        self._I_L2 = 0.0
        self._I_L3 = 0.0
        self._Freq = 0.0
        self._P_L1 = 0.0
        self._P_L2 = 0.0
        self._P_L3 = 0.0
        self._P_Tot = 0.0

        # Device-specific values
        if self._device_type == "mid_meter":
            self._P_Imp = 0.0  # Active energy import (Wirkenergie Bezug)
            self._P_Exp = 0.0  # Active energy export (Wirkenergie Lieferung)
            self._Q_Imp = 0.0  # Reactive energy import (Blindenergie Bezug)
            self._Q_Exp = 0.0  # Reactive energy export (Blindenergie Lieferung)
            # Phase-specific energy values
            self._P_Imp_L1 = 0.0  # Active energy consumed L1
            self._P_Imp_L2 = 0.0  # Active energy consumed L2
            self._P_Imp_L3 = 0.0  # Active energy consumed L3
            self._P_Exp_L1 = 0.0  # Active energy delivered L1
            self._P_Exp_L2 = 0.0  # Active energy delivered L2
            self._P_Exp_L3 = 0.0  # Active energy delivered L3
            self._Q_Imp_L1 = 0.0  # Reactive energy consumed L1
            self._Q_Imp_L2 = 0.0  # Reactive energy consumed L2
            self._Q_Imp_L3 = 0.0  # Reactive energy consumed L3
            self._Q_Exp_L1 = 0.0  # Reactive energy delivered L1
            self._Q_Exp_L2 = 0.0  # Reactive energy delivered L2
            self._Q_Exp_L3 = 0.0  # Reactive energy delivered L3
            # Tariff-based energy values
            self._P_Imp_T1 = 0.0  # Active energy consumed tariff 1
            self._P_Imp_T2 = 0.0  # Active energy consumed tariff 2
            self._P_Exp_T1 = 0.0  # Active energy delivered tariff 1
            self._P_Exp_T2 = 0.0  # Active energy delivered tariff 2
            self._Q_Imp_T1 = 0.0  # Reactive energy consumed tariff 1
            self._Q_Imp_T2 = 0.0  # Reactive energy consumed tariff 2
            self._Q_Exp_T1 = 0.0  # Reactive energy delivered tariff 1
            self._Q_Exp_T2 = 0.0  # Reactive energy delivered tariff 2
            # Total reactive energy
            self._Q_Tot = 0.0  # Total reactive energy
        elif self._device_type == "2857_570":
            # 2857-570 has additional measurements
            self._Q_L1 = 0.0  # Reactive power L1
            self._Q_L2 = 0.0  # Reactive power L2
            self._Q_L3 = 0.0  # Reactive power L3
            self._Q_Tot = 0.0  # Total reactive power
            self._S_L1 = 0.0  # Apparent power L1
            self._S_L2 = 0.0  # Apparent power L2
            self._S_L3 = 0.0  # Apparent power L3
            self._S_Tot = 0.0  # Total apparent power
            self._PF_L1 = 0.0  # Power factor L1
            self._PF_L2 = 0.0  # Power factor L2
            self._PF_L3 = 0.0  # Power factor L3
            self._PF_Tot = 0.0  # Total power factor

    def _read_values(self) -> None:
        """Read values from Modbus in background thread."""
        while self._running:
            if self._device_type == "mid_meter":
                self._read_mid_meter()
            elif self._device_type == "2857_570":
                self._read_2857_570()

            _LOGGER.debug("Messung completed")
            time.sleep(self._interval)
        _LOGGER.debug("Thread stopped")

    def _read_mid_meter(self) -> None:
        """Read values from MID meter (879-3000 series)."""
        result = self._client.read_holding_registers(20480, 26)

        if result:
            # Spannung (Voltage)
            self._U_L1 = self._bytes_to_float(result[2], result[3])
            self._U_L2 = self._bytes_to_float(result[4], result[5])
            self._U_L3 = self._bytes_to_float(result[6], result[7])
            # Strom (Current)
            self._I_L1 = self._bytes_to_float(result[12], result[13])
            self._I_L2 = self._bytes_to_float(result[14], result[15])
            self._I_L3 = self._bytes_to_float(result[16], result[17])
            # Frequenz (Frequency)
            self._Freq = self._bytes_to_float(result[8], result[9])
            # Wirkleistung (Active power)
            self._P_L1 = self._bytes_to_float(result[20], result[21])
            self._P_L2 = self._bytes_to_float(result[22], result[23])
            self._P_L3 = self._bytes_to_float(result[24], result[25])
            self._P_Tot = self._bytes_to_float(result[18], result[19])
            self._last_read_successful = True
        else:
            _LOGGER.warning("Unable to read modbus registers (20480)")
            self._last_read_successful = False

        result = self._client.read_holding_registers(24576, 24)

        if result:
            # Wirkenergie Bezug (Active energy import) - Register 0x6006 = 24582
            self._P_Imp = self._bytes_to_float(result[12], result[13])
            # Wirkenergie Lieferung (Active energy export) - Register 0x6010 = 24592
            self._P_Exp = self._bytes_to_float(result[22], result[23])
        else:
            _LOGGER.warning("Unable to read modbus registers (24576)")

        # Read reactive energy values (Blindenergie) - Register 0x6030 = 24624
        result = self._client.read_holding_registers(24624, 14)

        if result:
            # Blindenergie Bezug (Reactive energy import) - Register 0x6030
            self._Q_Imp = self._bytes_to_float(result[0], result[1])
            # Blindenergie Lieferung (Reactive energy export) - Register 0x603C = 24636
            self._Q_Exp = self._bytes_to_float(result[12], result[13])
        else:
            _LOGGER.warning("Unable to read modbus registers (24624)")

        # Read tariff-based and phase-specific energy values
        # Register 0x6002-0x6022 (24578-24610): Tariff and phase energy values
        result = self._client.read_holding_registers(24578, 34)

        if result:
            # Tariff 1 active energy consumed - Register 0x6002 = 24578
            self._P_Imp_T1 = self._bytes_to_float(result[0], result[1])
            # Tariff 2 active energy consumed - Register 0x6004 = 24580
            self._P_Imp_T2 = self._bytes_to_float(result[2], result[3])
            # Tariff 1 active energy delivered - Register 0x600C = 24588
            self._P_Exp_T1 = self._bytes_to_float(result[10], result[11])
            # Tariff 2 active energy delivered - Register 0x600E = 24590
            self._P_Exp_T2 = self._bytes_to_float(result[12], result[13])
            # Phase L1 active energy consumed - Register 0x601E = 24606
            self._P_Imp_L1 = self._bytes_to_float(result[28], result[29])
            # Phase L2 active energy consumed - Register 0x6020 = 24608
            self._P_Imp_L2 = self._bytes_to_float(result[30], result[31])
            # Phase L3 active energy consumed - Register 0x6022 = 24610
            self._P_Imp_L3 = self._bytes_to_float(result[32], result[33])
        else:
            _LOGGER.warning("Unable to read modbus registers (24578)")

        # Read reactive energy tariff and phase-specific values
        # Register 0x6032-0x6046 (24626-24646): Reactive energy by tariff and phase
        result = self._client.read_holding_registers(24626, 22)

        if result:
            # Tariff 1 reactive energy consumed - Register 0x6032 = 24626
            self._Q_Imp_T1 = self._bytes_to_float(result[0], result[1])
            # Tariff 2 reactive energy consumed - Register 0x6034 = 24628
            self._Q_Imp_T2 = self._bytes_to_float(result[2], result[3])
            # Phase L1 reactive energy delivered - Register 0x6036 = 24630
            self._Q_Exp_L1 = self._bytes_to_float(result[4], result[5])
            # Phase L2 reactive energy delivered - Register 0x6038 = 24632
            self._Q_Exp_L2 = self._bytes_to_float(result[6], result[7])
            # Phase L3 reactive energy delivered - Register 0x603A = 24634
            self._Q_Exp_L3 = self._bytes_to_float(result[8], result[9])
            # Tariff 1 reactive energy delivered - Register 0x603E = 24638
            self._Q_Exp_T1 = self._bytes_to_float(result[12], result[13])
            # Tariff 2 reactive energy delivered - Register 0x6040 = 24640
            self._Q_Exp_T2 = self._bytes_to_float(result[14], result[15])
            # Phase L1 active energy delivered - Register 0x6042 = 24642
            self._P_Exp_L1 = self._bytes_to_float(result[16], result[17])
            # Phase L2 active energy delivered - Register 0x6044 = 24644
            self._P_Exp_L2 = self._bytes_to_float(result[18], result[19])
            # Phase L3 active energy delivered - Register 0x6046 = 24646
            self._P_Exp_L3 = self._bytes_to_float(result[20], result[21])
        else:
            _LOGGER.warning("Unable to read modbus registers (24626)")

        # Read phase-specific reactive energy consumed
        # We need to read consumed reactive energy per phase separately
        # These are at registers before the total reactive energy
        # Register 0x602E = 24622: Total consumed reactive energy per phase
        result = self._client.read_holding_registers(24614, 10)

        if result:
            # Phase L1 reactive energy consumed - Register 0x6026 offset calculation
            # Based on pattern, consumed values are before delivered
            self._Q_Imp_L1 = self._bytes_to_float(result[0], result[1])
            self._Q_Imp_L2 = self._bytes_to_float(result[2], result[3])
            self._Q_Imp_L3 = self._bytes_to_float(result[4], result[5])
            # Total reactive energy - Register 0x602E = 24622
            self._Q_Tot = self._bytes_to_float(result[8], result[9])
        else:
            _LOGGER.warning("Unable to read modbus registers (24614)")

    def _read_2857_570(self) -> None:
        """Read values from 2857-570 power measurement module."""
        # Based on datasheet: Messwerte ab Register 0x000A (10)
        # Using Input Registers (FC04)
        result = self._client.read_input_registers(10, 50)

        if result:
            # Extract voltage, current, frequency, power values
            # Note: Exact register mapping needs to be verified from datasheet
            # This is a placeholder implementation
            self._U_L1 = self._bytes_to_float(result[0], result[1])
            self._U_L2 = self._bytes_to_float(result[2], result[3])
            self._U_L3 = self._bytes_to_float(result[4], result[5])

            self._I_L1 = self._bytes_to_float(result[10], result[11])
            self._I_L2 = self._bytes_to_float(result[12], result[13])
            self._I_L3 = self._bytes_to_float(result[14], result[15])

            self._Freq = self._bytes_to_float(result[20], result[21])

            # Active power
            self._P_L1 = self._bytes_to_float(result[30], result[31])
            self._P_L2 = self._bytes_to_float(result[32], result[33])
            self._P_L3 = self._bytes_to_float(result[34], result[35])
            self._P_Tot = self._bytes_to_float(result[36], result[37])

            # Reactive power
            self._Q_L1 = self._bytes_to_float(result[38], result[39])
            self._Q_L2 = self._bytes_to_float(result[40], result[41])
            self._Q_L3 = self._bytes_to_float(result[42], result[43])
            self._Q_Tot = self._bytes_to_float(result[44], result[45])

            # Apparent power (Scheinleistung)
            self._S_L1 = self._bytes_to_float(result[46], result[47])
            self._S_L2 = self._bytes_to_float(result[48], result[49])
            # Note: We only read 50 registers, need more for S_L3, S_Tot, PF values

            self._last_read_successful = True
        else:
            _LOGGER.warning("Unable to read modbus registers from 2857-570")
            self._last_read_successful = False

        # Read additional registers for S_L3, S_Tot, and power factors
        result = self._client.read_input_registers(60, 10)

        if result:
            self._S_L3 = self._bytes_to_float(result[0], result[1])
            self._S_Tot = self._bytes_to_float(result[2], result[3])

            # Power factors (Leistungsfaktor cos φ)
            self._PF_L1 = self._bytes_to_float(result[4], result[5])
            self._PF_L2 = self._bytes_to_float(result[6], result[7])
            self._PF_L3 = self._bytes_to_float(result[8], result[9])
            # Total power factor might be at next register
            # self._PF_Tot = self._bytes_to_float(result[10], result[11])
        else:
            _LOGGER.warning("Unable to read additional registers from 2857-570")

    @staticmethod
    def _bytes_to_float(high_word: int, low_word: int) -> float:
        """Convert two 16-bit words to a float."""
        value = (high_word << 16) + low_word
        return struct.unpack("!f", struct.pack("!I", value))[0]

    def print_values(self) -> None:
        """Print current values for debugging."""
        _LOGGER.debug("UL1: %s", self._U_L1)
        _LOGGER.debug("UL2: %s", self._U_L2)
        _LOGGER.debug("UL3: %s", self._U_L3)
        _LOGGER.debug("IL1: %s", self._I_L1)
        _LOGGER.debug("IL2: %s", self._I_L2)
        _LOGGER.debug("IL3: %s", self._I_L3)
        _LOGGER.debug("PL1: %s", self._P_L1)
        _LOGGER.debug("PL2: %s", self._P_L2)
        _LOGGER.debug("PL3: %s", self._P_L3)
        _LOGGER.debug("PTot: %s", self._P_Tot)

        if self._device_type == "mid_meter":
            _LOGGER.debug("PImp: %s", self._P_Imp)
            _LOGGER.debug("PExp: %s", self._P_Exp)
        elif self._device_type == "2857_570":
            _LOGGER.debug("QL1: %s", self._Q_L1)
            _LOGGER.debug("QL2: %s", self._Q_L2)
            _LOGGER.debug("QL3: %s", self._Q_L3)
            _LOGGER.debug("QTot: %s", self._Q_Tot)

        _LOGGER.debug("Freq: %s", self._Freq)
        _LOGGER.debug("***************")

    def stop(self) -> None:
        """Stop the background reading thread."""
        self._running = False
        _LOGGER.debug("Stopping meter thread")
        if self._modthread is not None:
            self._modthread.join()
            _LOGGER.debug("Meter thread stopped")
        else:
            _LOGGER.debug("Meter thread was never started")

    @staticmethod
    def _valid_ip(ip: str) -> bool:
        """Validate IP address format."""
        if re.match(
            r"^((\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])$",
            ip,
        ):
            return True
        return False

    # Voltage getters
    def get_voltage_l1(self) -> float:
        """Get voltage L1."""
        return round(self._U_L1, 4)

    def get_voltage_l2(self) -> float:
        """Get voltage L2."""
        return round(self._U_L2, 4)

    def get_voltage_l3(self) -> float:
        """Get voltage L3."""
        return round(self._U_L3, 4)

    # Current getters
    def get_current_l1(self) -> float:
        """Get current L1."""
        return round(self._I_L1, 4)

    def get_current_l2(self) -> float:
        """Get current L2."""
        return round(self._I_L2, 4)

    def get_current_l3(self) -> float:
        """Get current L3."""
        return round(self._I_L3, 4)

    # Active power getters
    def get_power_l1(self) -> float:
        """Get active power L1."""
        return round(self._P_L1, 4)

    def get_power_l2(self) -> float:
        """Get active power L2."""
        return round(self._P_L2, 4)

    def get_power_l3(self) -> float:
        """Get active power L3."""
        return round(self._P_L3, 4)

    def get_power_total(self) -> float:
        """Get total active power."""
        return round(self._P_Tot, 4)

    # MID meter specific getters
    def get_energy_import(self) -> float:
        """Get imported energy (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Imp, 4)
        return 0.0

    def get_energy_export(self) -> float:
        """Get exported energy (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Exp, 4)
        return 0.0

    def get_energy_consumed(self) -> float:
        """Get consumed (imported) active energy in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Imp, 4)
        return 0.0

    def get_energy_delivered(self) -> float:
        """Get delivered (exported) active energy in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Exp, 4)
        return 0.0

    def get_reactive_energy_consumed(self) -> float:
        """Get consumed (imported) reactive energy in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Imp, 4)
        return 0.0

    def get_reactive_energy_delivered(self) -> float:
        """Get delivered (exported) reactive energy in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Exp, 4)
        return 0.0

    # Phase-specific energy getters (MID meter only)
    def get_energy_consumed_l1(self) -> float:
        """Get consumed active energy L1 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Imp_L1, 4)
        return 0.0

    def get_energy_consumed_l2(self) -> float:
        """Get consumed active energy L2 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Imp_L2, 4)
        return 0.0

    def get_energy_consumed_l3(self) -> float:
        """Get consumed active energy L3 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Imp_L3, 4)
        return 0.0

    def get_energy_delivered_l1(self) -> float:
        """Get delivered active energy L1 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Exp_L1, 4)
        return 0.0

    def get_energy_delivered_l2(self) -> float:
        """Get delivered active energy L2 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Exp_L2, 4)
        return 0.0

    def get_energy_delivered_l3(self) -> float:
        """Get delivered active energy L3 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Exp_L3, 4)
        return 0.0

    def get_reactive_energy_consumed_l1(self) -> float:
        """Get consumed reactive energy L1 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Imp_L1, 4)
        return 0.0

    def get_reactive_energy_consumed_l2(self) -> float:
        """Get consumed reactive energy L2 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Imp_L2, 4)
        return 0.0

    def get_reactive_energy_consumed_l3(self) -> float:
        """Get consumed reactive energy L3 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Imp_L3, 4)
        return 0.0

    def get_reactive_energy_delivered_l1(self) -> float:
        """Get delivered reactive energy L1 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Exp_L1, 4)
        return 0.0

    def get_reactive_energy_delivered_l2(self) -> float:
        """Get delivered reactive energy L2 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Exp_L2, 4)
        return 0.0

    def get_reactive_energy_delivered_l3(self) -> float:
        """Get delivered reactive energy L3 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Exp_L3, 4)
        return 0.0

    # Tariff-based energy getters (MID meter only)
    def get_energy_consumed_t1(self) -> float:
        """Get consumed active energy tariff 1 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Imp_T1, 4)
        return 0.0

    def get_energy_consumed_t2(self) -> float:
        """Get consumed active energy tariff 2 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Imp_T2, 4)
        return 0.0

    def get_energy_delivered_t1(self) -> float:
        """Get delivered active energy tariff 1 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Exp_T1, 4)
        return 0.0

    def get_energy_delivered_t2(self) -> float:
        """Get delivered active energy tariff 2 in kWh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._P_Exp_T2, 4)
        return 0.0

    def get_reactive_energy_consumed_t1(self) -> float:
        """Get consumed reactive energy tariff 1 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Imp_T1, 4)
        return 0.0

    def get_reactive_energy_consumed_t2(self) -> float:
        """Get consumed reactive energy tariff 2 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Imp_T2, 4)
        return 0.0

    def get_reactive_energy_delivered_t1(self) -> float:
        """Get delivered reactive energy tariff 1 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Exp_T1, 4)
        return 0.0

    def get_reactive_energy_delivered_t2(self) -> float:
        """Get delivered reactive energy tariff 2 in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Exp_T2, 4)
        return 0.0

    def get_reactive_energy_total(self) -> float:
        """Get total reactive energy in kvarh (MID meter only)."""
        if self._device_type == "mid_meter":
            return round(self._Q_Tot, 4)
        return 0.0

    # 2857-570 specific getters
    def get_reactive_power_l1(self) -> float:
        """Get reactive power L1 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._Q_L1, 4)
        return 0.0

    def get_reactive_power_l2(self) -> float:
        """Get reactive power L2 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._Q_L2, 4)
        return 0.0

    def get_reactive_power_l3(self) -> float:
        """Get reactive power L3 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._Q_L3, 4)
        return 0.0

    def get_reactive_power_total(self) -> float:
        """Get total reactive power (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._Q_Tot, 4)
        return 0.0

    def get_apparent_power_l1(self) -> float:
        """Get apparent power L1 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._S_L1, 4)
        return 0.0

    def get_apparent_power_l2(self) -> float:
        """Get apparent power L2 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._S_L2, 4)
        return 0.0

    def get_apparent_power_l3(self) -> float:
        """Get apparent power L3 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._S_L3, 4)
        return 0.0

    def get_apparent_power_total(self) -> float:
        """Get total apparent power (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._S_Tot, 4)
        return 0.0

    def get_power_factor_l1(self) -> float:
        """Get power factor L1 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._PF_L1, 4)
        return 0.0

    def get_power_factor_l2(self) -> float:
        """Get power factor L2 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._PF_L2, 4)
        return 0.0

    def get_power_factor_l3(self) -> float:
        """Get power factor L3 (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._PF_L3, 4)
        return 0.0

    def get_power_factor_total(self) -> float:
        """Get total power factor (2857-570 only)."""
        if self._device_type == "2857_570":
            return round(self._PF_Tot, 4)
        return 0.0

    # Common getters
    def get_frequency(self) -> float:
        """Get frequency."""
        return round(self._Freq, 4)

    def is_available(self) -> bool:
        """Return whether the last Modbus read was successful."""
        return self._last_read_successful


# Legacy class name for backwards compatibility
class meter(WagoMeter):
    """Legacy meter class for backwards compatibility."""

    def __init__(self, modbus, interval) -> None:
        """Initialize legacy meter class."""
        super().__init__(
            ip=modbus["ip"],
            port=int(modbus["port"]),
            interval=interval,
            timeout=5,
            device_type="mid_meter",
        )

    # Legacy method names
    def getUL1(self) -> float:
        """Get voltage L1 (legacy method)."""
        return self.get_voltage_l1()

    def getUL2(self) -> float:
        """Get voltage L2 (legacy method)."""
        return self.get_voltage_l2()

    def getUL3(self) -> float:
        """Get voltage L3 (legacy method)."""
        return self.get_voltage_l3()

    def getIL1(self) -> float:
        """Get current L1 (legacy method)."""
        return self.get_current_l1()

    def getIL2(self) -> float:
        """Get current L2 (legacy method)."""
        return self.get_current_l2()

    def getIL3(self) -> float:
        """Get current L3 (legacy method)."""
        return self.get_current_l3()

    def getPL1(self) -> float:
        """Get power L1 (legacy method)."""
        return self.get_power_l1()

    def getPL2(self) -> float:
        """Get power L2 (legacy method)."""
        return self.get_power_l2()

    def getPL3(self) -> float:
        """Get power L3 (legacy method)."""
        return self.get_power_l3()

    def getPTotal(self) -> float:
        """Get total power (legacy method)."""
        return self.get_power_total()

    def getPImport(self) -> float:
        """Get import energy (legacy method)."""
        return self.get_energy_import()

    def getPExport(self) -> float:
        """Get export energy (legacy method)."""
        return self.get_energy_export()

    def getFreq(self) -> float:
        """Get frequency (legacy method)."""
        return self.get_frequency()

    def printValues(self) -> None:
        """Print values (legacy method)."""
        return self.print_values()
