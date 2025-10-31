# WAGO I/O System 750 - Integration Konzept

**Status**: Konzeptphase
**Ziel-Integration**: `wago_io_system` (neue, separate Integration)
**Bestehende Integration**: `wago_energymeter` (bleibt eigenständig)
**Hardware**: WAGO 750-362 Modbus TCP Koppler @ 192.168.2.44
**Erstellt**: 2025-10-29

---

## 1. Executive Summary

### Vision
Entwicklung einer universellen Home Assistant Integration für das modulare WAGO I/O System 750, die **automatisch** angeschlossene I/O-Module erkennt und entsprechende Entities dynamisch erstellt.

### Kernfunktion
- **Plug & Play**: Module werden automatisch über Modbus-Register erkannt
- **Dynamische Entities**: Sensoren, Schalter, Lights, etc. basierend auf erkannten Modulen
- **Flexibel**: Unterstützt beliebige WAGO 750-Konfigurationen
- **Skalierbar**: Bis zu 255 I/O-Module pro Koppler

### Abgrenzung zu `wago_energymeter`
| Aspekt | wago_energymeter | wago_io_system |
|--------|------------------|----------------|
| **Zweck** | Spezifisch für Energy Meter | Universelles I/O-System |
| **Module** | MID-Meter, 2857-570 (fest) | Beliebige 750-Module (dynamisch) |
| **Komplexität** | Niedrig (3 Gerätetypen) | Hoch (100+ Modultypen) |
| **Auto-Discovery** | Nein | **Ja** (Kern-Feature) |
| **Zielgruppe** | Energie-Monitoring | Industrie-Automatisierung |

---

## 2. Technische Grundlagen

### 2.1 WAGO 750-362 Modbus TCP Koppler

#### Hardware-Spezifikationen
```yaml
Gerät: WAGO 750-362 FC Modbus TCP (4. Generation)
Protokoll: Modbus TCP/IP
Max Module: 255
Erkennung: Automatisch über Modbus-Register
Web Interface: Ja (WBM - Web-Based Management)
Firmware: Update-fähig
```

#### Automatische Modul-Erkennung

**Konfigurationsregister** (Read-Only):
```python
Register 0x2030 (8240): Module 1-64      # Bis zu 64 Worte
Register 0x2031 (8241): Module 65-128    # Bis zu 64 Worte
Register 0x2032 (8242): Module 129-192   # Bis zu 64 Worte
Register 0x2033 (8243): Module 193-255   # Bis zu 63 Worte
```

**Modul-Identifikation**:
- **Analog/Spezial-Module**: Bestellnummer ohne `750-` Prefix
  - Beispiel: `750-530` → Register-Wert `0x0530` (1328 dez)
  - Beispiel: `750-469` → Register-Wert `0x0469` (1129 dez)

- **Digital-Module**: Codiert als 16-Bit Wert
  ```
  Bit 15:     1 = Digital-Modul Kennzeichnung
  Bit 14-8:   I/O-Größe in Bits (0-127)
  Bit 7-2:    Nicht benutzt (0)
  Bit 1:      1 = Ausgangsmodul
  Bit 0:      1 = Eingangsmodul

  Beispiele:
  0x8401 = 4-Kanal Digital-Eingang
  0x8202 = 2-Kanal Digital-Ausgang
  0x8803 = 8-Kanal Digital Ein-/Ausgang
  ```

### 2.2 Prozessdaten-Mapping

#### Input-Register (Function Code 4)
```python
# Digitale Eingänge
0x0000-0x007F: Digital Input Bytes (0-127)
0x0200-0x027F: Digital Input Words (0-127)

# Analoge Eingänge
0x0200-0x05FF: Analog Input Words
```

#### Holding-Register (Function Code 3 & 16)
```python
# Digitale Ausgänge
0x0000-0x007F: Digital Output Bytes (0-127)
0x0200-0x027F: Digital Output Words (0-127)

# Analoge Ausgänge
0x0200-0x05FF: Analog Output Words

# Diagnose & Konfiguration
0x1000-0x11FF: Diagnoseregister
0x2000-0x2FFF: Konfigurationsregister
0x3000-0x3FFF: Konstantenregister
```

---

## 3. Architektur-Design

### 3.1 Komponenten-Übersicht

```
wago_io_system/
├── __init__.py              # Setup & Unload
├── manifest.json            # Integration Metadata
├── const.py                 # Konstanten
├── config_flow.py           # UI Configuration
├── coordinator.py           # Data Update Coordinator
├── modbus_client.py         # Modbus TCP Kommunikation
├── module_registry.py       # 🆕 Modul-Datenbank
├── module_detector.py       # 🆕 Auto-Discovery
├── entity_factory.py        # 🆕 Dynamische Entity-Erstellung
├── models.py                # Data Models
├── diagnostics.py           # Diagnose
├── strings.json             # Translations
├── services.yaml            # Services (optional)
├── platforms/
│   ├── binary_sensor.py     # Digital Inputs
│   ├── switch.py            # Digital Outputs
│   ├── sensor.py            # Analog Inputs
│   ├── number.py            # Analog Outputs
│   └── light.py             # PWM/Dimming Outputs
└── tests/
    ├── conftest.py
    ├── test_config_flow.py
    ├── test_module_detector.py
    └── ...
```

### 3.2 Kern-Komponenten

#### 3.2.1 Module Registry (`module_registry.py`)

**Zweck**: Zentrale Datenbank aller WAGO-Module

```python
from dataclasses import dataclass
from enum import Enum
from typing import Callable

class ModuleType(Enum):
    """Modul-Kategorien"""
    DIGITAL_INPUT = "digital_input"
    DIGITAL_OUTPUT = "digital_output"
    DIGITAL_MIXED = "digital_mixed"
    ANALOG_INPUT = "analog_input"
    ANALOG_OUTPUT = "analog_output"
    SPECIAL_FUNCTION = "special_function"
    POWER_SUPPLY = "power_supply"

@dataclass
class WAGOModuleSpec:
    """Spezifikation eines WAGO-Moduls"""
    order_code: str                    # z.B. "750-530"
    name: str                          # "8-Channel Digital Input 24V DC"
    module_type: ModuleType
    channels: int                      # Anzahl Kanäle
    data_width_bits: int               # Bits im Prozessabbild
    platform: str                      # "binary_sensor", "switch", etc.
    device_class: str | None = None    # "voltage", "current", etc.
    unit: str | None = None            # "V", "A", "°C", etc.
    parser: Callable | None = None     # Funktion zum Parsen der Modbus-Daten

    # Register-Offsets (relativ zur Modulposition)
    input_offset: int | None = None
    output_offset: int | None = None
    config_registers: list[int] | None = None

# Modul-Registry
MODULE_REGISTRY: dict[int, WAGOModuleSpec] = {
    # Digital Input Modules
    0x8101: WAGOModuleSpec(
        order_code="750-400",
        name="1-Channel Digital Input 24V DC",
        module_type=ModuleType.DIGITAL_INPUT,
        channels=1,
        data_width_bits=1,
        platform="binary_sensor",
    ),
    0x8201: WAGOModuleSpec(
        order_code="750-402",
        name="2-Channel Digital Input 24V DC",
        module_type=ModuleType.DIGITAL_INPUT,
        channels=2,
        data_width_bits=2,
        platform="binary_sensor",
    ),
    0x8401: WAGOModuleSpec(
        order_code="750-404",
        name="4-Channel Digital Input 24V DC",
        module_type=ModuleType.DIGITAL_INPUT,
        channels=4,
        data_width_bits=4,
        platform="binary_sensor",
    ),
    0x8801: WAGOModuleSpec(
        order_code="750-408",
        name="8-Channel Digital Input 24V DC",
        module_type=ModuleType.DIGITAL_INPUT,
        channels=8,
        data_width_bits=8,
        platform="binary_sensor",
    ),

    # Digital Output Modules
    0x8102: WAGOModuleSpec(
        order_code="750-501",
        name="1-Channel Digital Output 24V DC 0.5A",
        module_type=ModuleType.DIGITAL_OUTPUT,
        channels=1,
        data_width_bits=1,
        platform="switch",
    ),
    0x8202: WAGOModuleSpec(
        order_code="750-502",
        name="2-Channel Digital Output 24V DC 0.5A",
        module_type=ModuleType.DIGITAL_OUTPUT,
        channels=2,
        data_width_bits=2,
        platform="switch",
    ),

    # Analog Input Modules
    0x0530: WAGOModuleSpec(
        order_code="750-530",
        name="8-Channel Analog Input 0-10V",
        module_type=ModuleType.ANALOG_INPUT,
        channels=8,
        data_width_bits=128,  # 8 channels × 16 bits
        platform="sensor",
        device_class="voltage",
        unit="V",
        parser=lambda raw: raw / 3276.7,  # 0-32767 → 0-10V
    ),
    0x0469: WAGOModuleSpec(
        order_code="750-469",
        name="4-Channel Analog Input 4-20mA",
        module_type=ModuleType.ANALOG_INPUT,
        channels=4,
        data_width_bits=64,  # 4 channels × 16 bits
        platform="sensor",
        device_class="current",
        unit="mA",
        parser=lambda raw: 4 + (raw / 32767 * 16),  # 0-32767 → 4-20mA
    ),

    # TODO: Weitere ~50-100 gängige Module hinzufügen
}

def get_module_spec(module_code: int) -> WAGOModuleSpec | None:
    """Hole Modul-Spezifikation basierend auf Modbus-Code"""
    return MODULE_REGISTRY.get(module_code)

def decode_digital_module(code: int) -> WAGOModuleSpec | None:
    """Dekodiere Digital-Modul aus codiertem Wert"""
    if not (code & 0x8000):  # Bit 15 muss gesetzt sein
        return None

    is_input = bool(code & 0x0001)
    is_output = bool(code & 0x0002)
    channels = (code >> 8) & 0x7F  # Bits 8-14

    # Bestimme Modul-Typ
    if is_input and is_output:
        module_type = ModuleType.DIGITAL_MIXED
        platform = "binary_sensor"  # Input als primär
    elif is_output:
        module_type = ModuleType.DIGITAL_OUTPUT
        platform = "switch"
    else:
        module_type = ModuleType.DIGITAL_INPUT
        platform = "binary_sensor"

    return WAGOModuleSpec(
        order_code=f"750-unknown-{code:04X}",
        name=f"{channels}-Channel Digital {'I/O' if is_input and is_output else 'Output' if is_output else 'Input'}",
        module_type=module_type,
        channels=channels,
        data_width_bits=channels,
        platform=platform,
    )
```

#### 3.2.2 Module Detector (`module_detector.py`)

**Zweck**: Automatische Erkennung angeschlossener Module

```python
import logging
from typing import TYPE_CHECKING

from .modbus_client import WAGOModbusClient
from .module_registry import MODULE_REGISTRY, decode_digital_module, WAGOModuleSpec

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class ModuleDetector:
    """Automatische Erkennung von WAGO I/O-Modulen"""

    # Konfigurationsregister
    CONFIG_REG_1_64 = 0x2030      # Module 1-64
    CONFIG_REG_65_128 = 0x2031    # Module 65-128
    CONFIG_REG_129_192 = 0x2032   # Module 129-192
    CONFIG_REG_193_255 = 0x2033   # Module 193-255

    def __init__(self, modbus_client: WAGOModbusClient):
        """Initialize module detector"""
        self.client = modbus_client
        self._detected_modules: list[tuple[int, WAGOModuleSpec]] = []

    async def async_detect_modules(self, hass: "HomeAssistant") -> list[tuple[int, WAGOModuleSpec]]:
        """
        Erkenne alle angeschlossenen I/O-Module

        Returns:
            Liste von (position, module_spec) Tupeln
        """
        detected = []

        # Lese alle Konfigurationsregister
        register_blocks = [
            (self.CONFIG_REG_1_64, 64, 0),      # Start position 0
            (self.CONFIG_REG_65_128, 64, 64),   # Start position 64
            (self.CONFIG_REG_129_192, 64, 128), # Start position 128
            (self.CONFIG_REG_193_255, 63, 192), # Start position 192
        ]

        for reg_addr, count, base_position in register_blocks:
            try:
                # Lese Modbus-Register im Executor
                def read_registers():
                    return self.client.read_holding_registers(reg_addr, count)

                registers = await hass.async_add_executor_job(read_registers)

                if not registers:
                    continue

                # Verarbeite erkannte Module
                for i, code in enumerate(registers):
                    if code == 0:  # Kein Modul an dieser Position
                        continue

                    position = base_position + i
                    module_spec = self._identify_module(code)

                    if module_spec:
                        detected.append((position, module_spec))
                        _LOGGER.info(
                            "Detected module at position %d: %s (%s)",
                            position,
                            module_spec.name,
                            module_spec.order_code,
                        )
                    else:
                        _LOGGER.warning(
                            "Unknown module at position %d: code 0x%04X",
                            position,
                            code,
                        )

            except Exception as err:
                _LOGGER.error("Failed to read config registers 0x%04X: %s", reg_addr, err)

        self._detected_modules = detected
        return detected

    def _identify_module(self, code: int) -> WAGOModuleSpec | None:
        """Identifiziere Modul anhand des Codes"""
        # Prüfe zuerst, ob es ein bekanntes Analog/Spezial-Modul ist
        if code in MODULE_REGISTRY:
            return MODULE_REGISTRY[code]

        # Falls nicht, versuche Digital-Modul zu dekodieren
        if code & 0x8000:  # Bit 15 gesetzt = Digital-Modul
            return decode_digital_module(code)

        return None

    def calculate_process_image_offsets(self) -> dict[int, dict[str, int]]:
        """
        Berechne Prozessabbild-Offsets für jedes Modul

        Returns:
            Dict: {position: {"input_offset": x, "output_offset": y}}
        """
        offsets = {}
        input_offset = 0
        output_offset = 0

        for position, module_spec in self._detected_modules:
            module_offsets = {}

            # Input-Offset
            if module_spec.module_type in [
                ModuleType.DIGITAL_INPUT,
                ModuleType.DIGITAL_MIXED,
                ModuleType.ANALOG_INPUT,
            ]:
                module_offsets["input_offset"] = input_offset
                # Berechne Bytes basierend auf Datengröße
                input_offset += (module_spec.data_width_bits + 7) // 8

            # Output-Offset
            if module_spec.module_type in [
                ModuleType.DIGITAL_OUTPUT,
                ModuleType.DIGITAL_MIXED,
                ModuleType.ANALOG_OUTPUT,
            ]:
                module_offsets["output_offset"] = output_offset
                output_offset += (module_spec.data_width_bits + 7) // 8

            offsets[position] = module_offsets

        return offsets
```

#### 3.2.3 Entity Factory (`entity_factory.py`)

**Zweck**: Dynamische Erstellung von Entities basierend auf erkannten Modulen

```python
from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.sensor import SensorEntity

from .module_registry import WAGOModuleSpec, ModuleType

class EntityFactory:
    """Factory für dynamische Entity-Erstellung"""

    @staticmethod
    def create_entities(
        position: int,
        module_spec: WAGOModuleSpec,
        coordinator: DataUpdateCoordinator,
        device_info: DeviceInfo,
        offsets: dict[str, int],
    ) -> list[Entity]:
        """
        Erstelle Entities für ein Modul

        Args:
            position: Modulposition (0-254)
            module_spec: Modul-Spezifikation
            coordinator: Data Update Coordinator
            device_info: Device Info
            offsets: Input/Output Offsets

        Returns:
            Liste von Entity-Instanzen
        """
        entities = []

        if module_spec.module_type == ModuleType.DIGITAL_INPUT:
            entities = EntityFactory._create_digital_inputs(
                position, module_spec, coordinator, device_info, offsets
            )
        elif module_spec.module_type == ModuleType.DIGITAL_OUTPUT:
            entities = EntityFactory._create_digital_outputs(
                position, module_spec, coordinator, device_info, offsets
            )
        elif module_spec.module_type == ModuleType.ANALOG_INPUT:
            entities = EntityFactory._create_analog_inputs(
                position, module_spec, coordinator, device_info, offsets
            )
        # TODO: Weitere Typen

        return entities

    @staticmethod
    def _create_digital_inputs(
        position: int,
        module_spec: WAGOModuleSpec,
        coordinator,
        device_info,
        offsets,
    ) -> list[BinarySensorEntity]:
        """Erstelle Binary Sensor Entities für Digital Inputs"""
        entities = []

        for channel in range(module_spec.channels):
            entity = WAGODigitalInput(
                coordinator=coordinator,
                module_position=position,
                channel=channel,
                module_spec=module_spec,
                device_info=device_info,
                offset=offsets.get("input_offset", 0),
            )
            entities.append(entity)

        return entities

    # TODO: Weitere Factory-Methoden
```

### 3.3 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Config Flow (User Input)                                 │
│    - IP-Adresse: 192.168.2.44                               │
│    - Port: 502                                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Setup Entry (async_setup_entry)                          │
│    - Erstelle Modbus Client                                 │
│    - Initialisiere Module Detector                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Module Detection (async_detect_modules)                  │
│    - Lese Register 0x2030-0x2033                            │
│    - Identifiziere Module via Registry                      │
│    - Berechne Process Image Offsets                         │
│    Result: [(0, DI-8ch), (1, DO-4ch), (2, AI-8ch-10V)]     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Entity Creation (Entity Factory)                         │
│    - Pro Modul: Erstelle Entities für alle Kanäle          │
│    - Pos 0, DI-8ch → 8× Binary Sensors                     │
│    - Pos 1, DO-4ch → 4× Switches                           │
│    - Pos 2, AI-8ch → 8× Voltage Sensors                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Coordinator Setup (DataUpdateCoordinator)                │
│    - Poll Interval: 1 second                                 │
│    - Read Input Registers (Digital + Analog)                │
│    - Entities update via coordinator.data                    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Runtime Operations                                        │
│    - Switches: Write to Output Registers                    │
│    - Numbers: Write to Analog Output Registers              │
│    - Sensors: Read from coordinator.data                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Implementierungs-Phasen

### Phase 1: Foundation (Woche 1-2)
**Ziel**: Basis-Infrastruktur ohne Hardware

- [x] Projekt-Setup & Struktur
- [ ] Config Flow (IP + Port)
- [ ] Modbus Client Wrapper
- [ ] Module Registry (erste 20 Module)
- [ ] Module Detector (Logik)
- [ ] Tests mit Mocks
- [ ] Hassfest validation

**Geschätzter Aufwand**: 12-16 Stunden

### Phase 2: Core Features (Woche 3-4)
**Ziel**: Grundfunktionen mit Hardware @ 192.168.2.44

- [ ] Live Module Detection testen
- [ ] Entity Factory implementieren
- [ ] Digital Input (Binary Sensor) Platform
- [ ] Digital Output (Switch) Platform
- [ ] Data Update Coordinator
- [ ] Diagnostics
- [ ] Integration Tests mit Hardware

**Geschätzter Aufwand**: 16-20 Stunden

### Phase 3: Advanced Features (Woche 5-6)
**Ziel**: Erweiterte Funktionen

- [ ] Analog Input (Sensor) Platform
- [ ] Analog Output (Number) Platform
- [ ] Module Registry erweitern (50+ Module)
- [ ] Options Flow (Update Interval, etc.)
- [ ] Services (Manual Refresh, etc.)
- [ ] Reconfigure Flow

**Geschätzter Aufwand**: 12-16 Stunden

### Phase 4: Polish & Quality (Woche 7-8)
**Ziel**: Production-Ready

- [ ] Test Coverage >95%
- [ ] Quality Scale: Silver Tier minimum
- [ ] Dokumentation (README, Examples)
- [ ] Error Handling & Edge Cases
- [ ] Performance Optimization
- [ ] Code Review

**Geschätzter Aufwand**: 8-12 Stunden

**Gesamt-Aufwand**: ~50-65 Stunden

---

## 5. Test-Hardware Setup

### Verfügbare Hardware
```yaml
IP-Adresse: 192.168.2.44
Port: 502
Gerät: WAGO 750-362 Modbus TCP Koppler
Zugriff: Direkt verfügbar für Entwicklung/Tests
```

### Test-Szenarien
1. **Module Detection**:
   - Aktuelle Konfiguration auslesen
   - Verschiedene Modul-Typen testen
   - Empty slots verifizieren

2. **I/O Operations**:
   - Digital Inputs lesen
   - Digital Outputs schalten
   - Analog Values auslesen
   - Performance messen

3. **Edge Cases**:
   - Modul während Laufzeit entfernen
   - Verbindungsverlust
   - Timeout-Handling
   - Fehlerhafte Daten

---

## 6. API-Referenz

### Config Flow Data Schema
```python
CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=502): cv.port,
    vol.Optional(CONF_NAME, default="WAGO I/O System"): cv.string,
    vol.Optional(CONF_SCAN_INTERVAL, default=1): cv.positive_int,
})
```

### Runtime Data Structure
```python
@dataclass
class WAGOIOSystemData:
    """Runtime data for WAGO I/O System"""
    modbus_client: WAGOModbusClient
    module_detector: ModuleDetector
    detected_modules: list[tuple[int, WAGOModuleSpec]]
    process_image_offsets: dict[int, dict[str, int]]
    coordinator: DataUpdateCoordinator
```

### Entity Naming Convention
```
Format: {device_name} {module_name} Ch{channel}

Examples:
- "WAGO I/O System Digital Input 8ch Ch1"
- "WAGO I/O System Digital Output 4ch Ch2"
- "WAGO I/O System Analog Input 0-10V Ch5"
```

### Entity IDs
```
Format: {platform}.wago_{position}_{channel}

Examples:
- binary_sensor.wago_0_0  # Position 0, Channel 0
- switch.wago_1_3         # Position 1, Channel 3
- sensor.wago_2_7         # Position 2, Channel 7
```

---

## 7. Quality Scale Ziele

### Minimum: Silver Tier
- ✅ Config Flow
- ✅ Config Entry Unloading
- ✅ Entity Unique IDs
- ✅ Entity Unavailable Handling
- ✅ Test Coverage >95%
- ✅ Reauthentication Flow (falls Auth erweitert wird)

### Stretch Goal: Gold Tier
- ✅ Diagnostics
- ✅ Reconfigure Flow
- ✅ Entity Translations
- ✅ Device Registry Integration

---

## 8. Bekannte Herausforderungen

### 8.1 Technisch

**Module Registry Maintenance**:
- ~200+ WAGO-Module existieren
- Priorität: Häufigste Module zuerst
- Commun ity-Beiträge ermöglichen

**Process Image Berechnung**:
- Komplexe Offset-Berechnung
- Byte-Alignment beachten
- Spezialmodule haben eigene Logik

**Performance**:
- 1s Poll-Interval kann bei vielen Modulen CPU-intensiv sein
- Optimierung: Nur geänderte Bereiche lesen

### 8.2 Organisatorisch

**Dokumentation**:
- WAGO-spezifisches Wissen erforderlich
- Handbücher >20.000 Seiten
- Community-Support aufbauen

**Testing**:
- Hardware-abhängig
- Verschiedene Modul-Kombinationen
- Langzeit-Stabilität

---

## 9. Migration & Coexistence

### Parallelbetrieb mit `wago_energymeter`
```yaml
# Beide Integrationen können parallel laufen
wago_energymeter:
  - host: 192.168.1.100  # MID Meter
    device_type: mid_meter

wago_io_system:
  - host: 192.168.2.44   # I/O System
    name: "Factory Floor"
```

### Keine Migration erforderlich
- Beide Integrationen sind vollständig unabhängig
- Unterschiedliche Domains, Config Entries, Entities
- Kein Daten-Sharing zwischen Integrationen

---

## 10. Nächste Schritte

### Sofort machbar (ohne Hardware)
1. ✅ Dieses Konzeptdokument erstellen
2. ⏳ Integration Scaffold mit `script/scaffold`
3. ⏳ Module Registry Basis-Implementierung
4. ⏳ Config Flow Tests schreiben
5. ⏳ Modbus Client Mocks erstellen

### Mit Hardware @ 192.168.2.44
1. ⏳ Aktuelle Modul-Konfiguration auslesen
2. ⏳ Live Module Detection testen
3. ⏳ I/O Read/Write Operations validieren
4. ⏳ Performance benchmarking

### Dokumentation
1. ⏳ README.md für End-User
2. ⏳ Developer Guide
3. ⏳ Module Registry Contribution Guide
4. ⏳ Troubleshooting Guide

---

## 11. Referenzen

### Offizielle Dokumentation
- WAGO 750-362 Handbuch (21.856 Zeilen)
- Modbus TCP/IP Specification
- WAGO I/O System Katalog

### Home Assistant Developer Docs
- [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
- [Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [Data Update Coordinator](https://developers.home-assistant.io/docs/integration_fetching_data/)

### Ähnliche Integrationen (Referenz)
- `modbus` - Basis Modbus-Integration
- `wago_energymeter` - Unsere bestehende Integration
- `shelly` - Dynamic device discovery

---

## 12. Glossar

| Begriff | Bedeutung |
|---------|-----------|
| **Feldbuskoppler** | WAGO 750-362, verbindet I/O-Module mit Netzwerk |
| **I/O-Modul** | Einzelnes Eingangs-/Ausgangsmodul (Digital/Analog) |
| **Prozessabbild** | Aktueller Zustand aller I/O-Werte im RAM |
| **Lokalbus** | Interne Kommunikation zwischen Koppler und Modulen |
| **Register** | Modbus-Speicheradresse (16-bit Wort) |
| **Holding Register** | Schreibbare Modbus-Register |
| **Input Register** | Nur-Lese Modbus-Register |
| **Module Position** | Index 0-254, Position des Moduls am Koppler |

---

## Appendix A: Modul-Beispiele

### Häufigste Digital-Module
```python
0x8401: "750-404" - 4-Channel DI 24V DC
0x8801: "750-408" - 8-Channel DI 24V DC
0x8202: "750-502" - 2-Channel DO 24V DC
0x8402: "750-504" - 4-Channel DO 24V DC
```

### Häufigste Analog-Module
```python
0x0469: "750-469" - 4-Channel AI 4-20mA
0x0530: "750-530" - 8-Channel AI 0-10V
0x0554: "750-554" - 4-Channel AO 0-10V
0x0559: "750-559" - 4-Channel AO 4-20mA
```

### Spezial-Module
```python
0x0650: "750-650" - SSI Encoder Interface
0x0637: "750-637" - Serial RS232/485
0x0652: "750-652" - Incremental Encoder
```

---

## Appendix B: Register-Map Beispiel

```
Position 0: 750-408 (8-Channel DI)
├── Config Register 0x2030[0] = 0x8801
├── Input Bytes: 0x0000 (1 Byte)
└── Channels: 8× Binary Sensors

Position 1: 750-502 (2-Channel DO)
├── Config Register 0x2030[1] = 0x8202
├── Output Bytes: 0x0000 (1 Byte)
└── Channels: 2× Switches

Position 2: 750-530 (8-Channel AI 0-10V)
├── Config Register 0x2030[2] = 0x0530
├── Input Words: 0x0200-0x0207 (16 Bytes)
└── Channels: 8× Voltage Sensors
```

---

**Ende des Konzeptdokuments**

Dieses Dokument kann in einer neuen Session als Grundlage für die Implementierung von `wago_io_system` verwendet werden.
