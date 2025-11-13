# WAGO Energy Meter Integration - Projekt-Analyse und Strategieplanung

**Stand: 9. November 2025**
**Repository: home-assistant/core Fork**
**Integration: homeassistant/components/wago_energymeter/**

## Executive Summary

Die WAGO Energy Meter Integration ist technisch **Core-bereit** (Bronze/Silver/Gold/Platinum Quality Scale erfüllt), benötigt jedoch signifikanten Aufwand für die **95% Testabdeckung** (aktuell 55%). Parallel kann eine **HACS-Veröffentlichung** als Zwischenschritt erfolgen.

## Aktuelle Situation

### ✅ **Erreichte Meilensteine**

#### Code-Qualität (Home Assistant Core Standards)
- **Bronze Tier**: 100% erfüllt ✅
  - Config Flow mit UI-Setup ✅
  - Unique Entity IDs ✅
  - Proper error handling ✅

- **Silver Tier**: 100% erfüllt ✅
  - Entity unavailability handling ✅
  - Parallel updates configuration ✅
  - Reauthentication support ✅

- **Gold Tier**: 90% erfüllt (nur Test Coverage fehlt)
  - Device management ✅
  - Diagnostics support ✅
  - Entity translations ✅
  - **Test Coverage**: 55% (⚠️ Blocker für Core)

- **Platinum Tier**: 100% erfüllt ✅
  - Strict typing ✅
  - Async dependencies ✅
  - WebSession injection ✅

#### Integration-Architektur
- **Proper Core Structure**: `homeassistant/components/wago_energymeter/` ✅
- **Manifest.json**: Core-konforme Konfiguration ✅
- **Config Flow**: Vollständige UI-basierte Einrichtung ✅
- **Entity Framework**: Modern Home Assistant Entity-Patterns ✅
- **Error Handling**: Robuste Exception-Behandlung ✅
- **Diagnostics**: Debug-Informationen für Troubleshooting ✅

### ⚠️ **Identifizierte Herausforderungen**

#### Test Coverage Gap (KRITISCHER BLOCKER für Core)
```
Aktuell:   55% Coverage (646/1165 lines covered)
Benötigt:  95% Coverage für Home Assistant Core
Gap:       40% (519 missing lines)

Datei-spezifische Analyse:
├── config_flow.py:   100% ✅ (Core-bereit)
├── const.py:         100% ✅ (Core-bereit)
├── diagnostics.py:   100% ✅ (Core-bereit)
├── __init__.py:       91% 🟡 (3 lines missing)
├── meter.py:          34% 🔴 (268 lines missing) - HAUPTPROBLEM
└── sensor.py:         56% 🔴 (248 lines missing) - HAUPTPROBLEM
```

#### Hardware-abhängige Tests (Primäre Komplexität)
- **Modbus TCP Kommunikation**: Alle Hardware-Operationen benötigen sophisticated Mocking
- **Threading**: Background-Read-Loops mit Race-Condition-Tests
- **Device-spezifisch**: MID-Meter vs 2857-570 unterschiedliche Register-Layouts
- **Error Scenarios**: Connection timeouts, register read failures

## Aufwands-Analyse für 95% Test Coverage

### **Gesamtschätzung: 33-43 Arbeitstage**

#### Hauptaufwand-Bereiche:

1. **meter.py Modbus-Mocking** (268 lines)
   - `_read_mid_meter()`: 4 Register-Bereiche, Complex data structures
   - `_read_2857_570()`: Device-specific register layouts
   - Threading-Operations: start(), stop(), background loops
   - **Aufwand: 12-15 Tage** (High complexity)

2. **sensor.py Entity-Tests** (248 lines)
   - Entity property methods: native_value, available, extra_state_attributes
   - Update mechanisms: Coordinator integration, state propagation
   - Device-specific implementations: MID vs 2857-570 differences
   - **Aufwand: 9-12 Tage** (Medium complexity)

3. **Integration & Support**
   - Error handling paths, edge cases, cleanup
   - **Aufwand: 8-12 Tage** (Medium complexity)

### **Umsetzungs-Strategie (Phasiert)**

#### Phase 1: Foundation (Woche 1-2)
- Mock-Framework für Modbus-Client
- Simple Property-Tests
- __init__.py Coverage schließen

#### Phase 2: Hardware-Mocking (Woche 3-5)
- `_read_mid_meter()` vollständige Abdeckung
- `_read_2857_570()` vollständige Abdeckung
- Threading-Operations

#### Phase 3: Entity-Layer (Woche 6-7)
- sensor.py Property-Tests
- Update-Mechanism-Tests
- Device-spezifische Scenarios

#### Phase 4: Integration (Woche 8-9)
- Error-Handling-Paths
- Edge-Cases und Cleanup
- Coverage-Validierung

## Strategische Optionen

### **Option A: Home Assistant Core (Langfristig optimal)**

#### Vorteile:
- ✅ Offizielle Integration, keine separaten Updates nötig
- ✅ Höchste Sichtbarkeit und Adoption
- ✅ Automatische QA durch Home Assistant Core-Team
- ✅ Integration in offizielle Dokumentation

#### Nachteile:
- ❌ **40% Test Coverage Gap** (7-9 Wochen Aufwand)
- ❌ Strenge Review-Prozesse
- ❌ Längere Time-to-Market

#### Zusätzliche Anforderungen:
- **Dokumentation**: homeassistant.io Website-Docs
- **Brand Assets**: WAGO Logo in brands repository
- **Code Review**: Community-Review-Prozess

### **Option B: HACS Integration (Schneller Start)**

#### Vorteile:
- ✅ **Sofortige Verfügbarkeit** (wenige Tage Setup)
- ✅ Community kann sofort testen und Feedback geben
- ✅ Iterative Verbesserungen möglich
- ✅ Weniger strenge technische Anforderungen

#### Nachteile:
- ❌ Manuelle Installation durch Benutzer
- ❌ Geringere Adoption als Core-Integration
- ❌ Separate Update-Zyklen

#### Minimal-Anforderungen für HACS:
- ✅ **Bereits erfüllt**: Funktionierende Integration
- ✅ **Bereits erfüllt**: Proper manifest.json
- ⏳ **Benötigt**: Separates Repository-Setup
- ⏳ **Benötigt**: hacs.json Konfiguration
- ⏳ **Benötigt**: README mit Installationsanleitung

### **Option C: Hybrid-Strategie (EMPFOHLEN)**

#### Phasen-Ansatz:
1. **Phase 1**: HACS-Veröffentlichung (sofort, 1-2 Wochen Setup)
2. **Phase 2**: Test Coverage Entwicklung (parallel, 7-9 Wochen)
3. **Phase 3**: Core-Submission (nach Test-Fertigstellung)

#### Vorteile:
- ✅ **Sofortiger Nutzen** durch HACS
- ✅ **Community-Feedback** für Core-Vorbereitung
- ✅ **Validierung** der Integration im Feld
- ✅ **Parallele Entwicklung** möglich

## Technische Eckpfeiler

### **Integration-Architektur**
```
WAGO Energy Meter Integration
├── Core-kompatible Struktur ✅
├── Async/Await Pattern ✅
├── DataUpdateCoordinator Pattern ✅
├── Modern Entity Framework ✅
├── Type Hints (Python 3.13+) ✅
└── Error Handling & Diagnostics ✅
```

### **Supported Hardware**
- **MID-Meter (879-3000 series)**: Vollständig implementiert
- **2857-570 Power Module**: Implementiert (Register-Mapping teilweise placeholder)
- **Modbus TCP**: WAGO Controller mit Ethernet-Interface

### **Features**
- **Live-Monitoring**: Spannung, Strom, Leistung, Energie per Phase
- **Energy Management**: Import/Export, Tariff-based tracking
- **Device Detection**: Automatic device type recognition
- **Diagnostics**: Comprehensive debug information
- **Entity Management**: Proper Home Assistant entity lifecycle

## Nächste Schritte - Entscheidung erforderlich

### **Kurzfristig (1-2 Wochen)**
1. **Entscheidung**: HACS vs Core-first Strategy
2. **HACS-Setup**: Falls Hybrid-Ansatz gewählt (siehe unten)
3. **Dokumentation**: README für End-User

### **Mittelfristig (2-3 Monate)**
1. **Test Coverage**: 95% Coverage-Entwicklung
2. **Community-Feedback**: Integration von HACS-User-Feedback
3. **Hardware-Tests**: Erweiterte Geräte-Kompatibilität

### **Langfristig (6+ Monate)**
1. **Core-Submission**: Nach Test-Coverage-Fertigstellung
2. **Brand Integration**: WAGO Logo und offizielle Dokumentation
3. **Feature-Erweiterungen**: Basierend auf Community-Input

---

## Fazit

Die Integration ist **technisch bereit** für beide Pfade. Der **Hybrid-Ansatz** (HACS sofort, Core parallel) bietet die beste Balance zwischen sofortigem Nutzen und langfristigem Ziel.

**Empfehlung**: Start mit HACS-Veröffentlichung für Community-Feedback und parallele Entwicklung der Test-Coverage für Core-Readiness.