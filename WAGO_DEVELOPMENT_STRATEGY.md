# WAGO Integrationen - Entwicklungsstrategie

**Stand: 12. November 2025**
**Repository: github.com/Arndt-Barop/core (Fork)**
**Strategie: Shared Development mit späterem Split-Option**

---

## Executive Summary

Entwicklung von **zwei unabhängigen WAGO-Integrationen** im **selben Core-Fork**:
- `wago_energymeter` (existiert, Core-Vorbereitung läuft)
- `wago_io_system` (neu, wird jetzt entwickelt)

**Strategie:** Start im gemeinsamen Fork für maximale Effizienz, **späteres Splitting jederzeit möglich** via Git Subtree/Filter-Repo.

---

## 1. Repository-Struktur (Aktuell & Ziel)

### **Aktueller Stand:**
```
github.com/Arndt-Barop/core/
├── homeassistant/components/
│   ├── wago_energymeter/          ✅ Existiert (Gold Quality Scale)
│   │   ├── manifest.json          # 55% Test Coverage → 95% Ziel
│   │   ├── __init__.py
│   │   ├── config_flow.py
│   │   ├── meter.py
│   │   ├── sensor.py
│   │   └── tests/
│   └── ~3000+ andere Core-Integrationen
└── Git-Remotes:
    ├── origin: Arndt-Barop/core
    ├── upstream: home-assistant/core
    └── wago-custom: Privates Custom Repo
```

### **Ziel-Struktur:**
```
github.com/Arndt-Barop/core/
├── homeassistant/components/
│   ├── wago_energymeter/          ✅ Energy Meter (spezialisiert)
│   └── wago_io_system/            🆕 I/O System (universell)
│       ├── manifest.json
│       ├── __init__.py
│       ├── config_flow.py
│       ├── module_registry.py     # 🆕 Modul-Datenbank
│       ├── module_detector.py     # 🆕 Auto-Discovery
│       ├── entity_factory.py      # 🆕 Dynamische Entities
│       ├── coordinator.py
│       ├── modbus_client.py
│       └── platforms/
│           ├── binary_sensor.py
│           ├── switch.py
│           ├── sensor.py
│           └── number.py
└── Dokumentation:
    ├── WAGO_ENERGYMETER_ANALYSIS.md
    ├── WAGO_IO_SYSTEM_CONCEPT.md
    └── WAGO_DEVELOPMENT_STRATEGY.md  ← Diese Datei
```

---

## 2. Begründung: Warum SHARED Development?

### **✅ Vorteile:**

1. **Infrastruktur bereits fertig:**
   - Dev Container konfiguriert (mit host network für Hardware-Zugriff)
   - Testing-Setup funktioniert (pytest, coverage, mypy, ruff)
   - Hardware @ 192.168.2.44 verfügbar
   - Upstream-Sync eingerichtet

2. **Code-Reuse & Lernkurve:**
   - Testing-Patterns von `wago_energymeter` übernehmen
   - Modbus-Client-Logik als Referenz
   - Quality-Scale-Erfahrung anwendbar

3. **Technische Realität:**
   - Home Assistant Core **ist** die richtige Basis
   - Beide Integrationen **völlig unabhängig** (separate Domains)
   - Core-Submission erfordert sowieso Core-Fork

4. **Community Best Practice:**
   - **TP-Link-Pattern**: `tplink`, `tplink_tapo`, `tplink_lte`, `tplink_omada` koexistieren
   - **Xiaomi-Pattern**: `xiaomi`, `xiaomi_aqara`, `xiaomi_ble`, `xiaomi_miio` koexistieren
   - Mehrere verwandte Integrationen im Core sind **Standard**

### **⚠️ Management durch Konventionen:**

1. **Git-Commit-Präfixe:**
   ```bash
   feat(wago_io_system): add module detection
   fix(wago_energymeter): modbus timeout handling
   test(wago_io_system): add config flow tests
   docs(wago_energymeter): update README
   ```

2. **Branch-Strategie:**
   ```bash
   dev (main development)
   ├── feature/wago_io_system_foundation
   ├── feature/wago_energymeter_tests
   ├── fix/wago_io_system_modbus
   └── docs/wago_energymeter_hacs
   ```

3. **GitHub Issue Labels:**
   - `wago_energymeter`
   - `wago_io_system`
   - `modbus`
   - `hardware`
   - `documentation`

---

## 3. Splitting-Strategie (Zukünftige Option)

### **Option A: Git Subtree Extract** ⭐ **EMPFOHLEN**

**Zeitpunkt:** Nach Phase 1-2 Entwicklung (2-3 Monate), wenn HACS-Separation gewünscht

```bash
# Beispiel: wago_io_system zu separatem Repo extrahieren
# (Behält KOMPLETTE Git-Historie nur für diese Integration)

# 1. Neues Repo erstellen
gh repo create Arndt-Barop/wago-io-system --private

# 2. Subtree Extract (behält Historie)
git subtree split \
  --prefix=homeassistant/components/wago_io_system \
  -b wago_io_system_only

# 3. Push zu neuem Repo
git remote add wago-io-remote https://github.com/Arndt-Barop/wago-io-system
git push wago-io-remote wago_io_system_only:main

# 4. Für HACS: Umstrukturieren
cd ../wago-io-system
mkdir -p custom_components/wago_io_system
mv homeassistant/components/wago_io_system/* custom_components/wago_io_system/
```

**Vorteile:**
- ✅ **Komplette Git-Historie** erhalten
- ✅ **Commits bleiben attributiert** (Author, Dates, Messages)
- ✅ **Jederzeit durchführbar** (auch nach Monaten)
- ✅ **Original-Fork bleibt intakt**

### **Option B: Git Filter-Repo** (Fortgeschritten)

Für maximale Sauberkeit bei HACS-Export:
```bash
git clone Arndt-Barop/core wago-io-system-export
cd wago-io-system-export

git filter-repo \
  --path homeassistant/components/wago_io_system \
  --path-rename homeassistant/components/wago_io_system:custom_components/wago_io_system \
  --force

# Perfekt strukturiertes HACS-Repo mit Historie
```

---

## 4. Entwicklungs-Timeline

### **Phase 1: Foundation (Jetzt - Woche 1-2)**

**wago_io_system:**
- ✅ Integration Scaffold erstellen
- ✅ Config Flow (IP + Port)
- ✅ Modbus Client Wrapper
- ✅ Module Registry (erste 20 Module)
- ✅ Module Detector (Logik)
- ✅ Tests mit Mocks
- ✅ Hassfest validation

**wago_energymeter (parallel):**
- ⏳ Test Coverage verbessern (55% → 75%)
- ⏳ Meter.py Modbus-Mocking

**Aufwand:** ~16-20 Stunden gesamt

### **Phase 2: Core Features (Woche 3-4)**

**wago_io_system:**
- ✅ Live Module Detection mit Hardware @ 192.168.2.44
- ✅ Entity Factory implementieren
- ✅ Binary Sensor Platform (Digital Inputs)
- ✅ Switch Platform (Digital Outputs)
- ✅ Data Update Coordinator
- ✅ Diagnostics

**wago_energymeter (parallel):**
- ⏳ Test Coverage 75% → 90%
- ⏳ Sensor.py Entity-Tests

**Aufwand:** ~20-24 Stunden gesamt

### **Phase 3: Advanced Features (Woche 5-6)**

**wago_io_system:**
- ✅ Sensor Platform (Analog Inputs)
- ✅ Number Platform (Analog Outputs)
- ✅ Module Registry erweitern (50+ Module)
- ✅ Options Flow
- ✅ Test Coverage >95%

**wago_energymeter:**
- ✅ Test Coverage 90% → 95% (Core-ready)
- ✅ Documentation für homeassistant.io
- ✅ HACS-Vorbereitung

**Aufwand:** ~16-20 Stunden gesamt

### **Phase 4: Polish & Deployment (Woche 7-8)**

**Beide Integrationen:**
- ✅ Quality Scale Compliance
- ✅ Code Review & Refactoring
- ✅ Performance Optimization
- ✅ End-User Documentation

**Deployment-Entscheidung:**
- **Option A**: Beide im Core-Fork → Core-Submission
- **Option B**: Extract zu HACS → Git Subtree
- **Option C**: Hybrid (Energy Meter Core, I/O System HACS)

**Aufwand:** ~12-16 Stunden gesamt

---

## 5. Integration-Koexistenz

### **Technisch völlig getrennt:**

```python
# manifest.json für wago_energymeter
{
  "domain": "wago_energymeter",        # ✅ Unique Domain
  "requirements": ["pyModbusTCP==v0.1.10"]
}

# manifest.json für wago_io_system
{
  "domain": "wago_io_system",          # ✅ Unique Domain
  "requirements": ["pyModbusTCP==v0.1.10"]  # Shared dependency OK
}
```

### **Parallel nutzbar in Home Assistant:**

```yaml
# configuration.yaml (User kann beide nutzen)
# Beide via UI konfigurierbar, keine YAML-Config

# Entities:
sensor.wago_energymeter_voltage_l1
sensor.wago_energymeter_current_l1
binary_sensor.wago_io_0_0      # I/O System Position 0 Channel 0
switch.wago_io_1_3             # I/O System Position 1 Channel 3
```

### **Keine Konflikte:**
- ✅ Unterschiedliche Domains
- ✅ Unterschiedliche Config Entries
- ✅ Unterschiedliche Entity IDs
- ✅ Shared Modbus-Library ist OK (beide nutzen pyModbusTCP)

---

## 6. Core-Submission-Strategie

### **Separate Pull Requests:**

```bash
# wago_energymeter Core-PR (später)
git checkout -b pr/wago_energymeter_core
# Nur wago_energymeter-relevante Changes
# PR zu home-assistant/core

# wago_io_system Core-PR (später)
git checkout -b pr/wago_io_system_core
# Nur wago_io_system-relevante Changes
# PR zu home-assistant/core
```

### **Unabhängige Review-Prozesse:**
- Jede Integration hat eigene Reviewer
- Unterschiedliche Merge-Timelines OK
- Kein Dependency zwischen den PRs

---

## 7. HACS-Strategie

### **Wenn HACS gewünscht (vor Core-Submission):**

```bash
# Extract wago_energymeter
git subtree split --prefix=homeassistant/components/wago_energymeter -b wago_energymeter_hacs
# → github.com/Arndt-Barop/hacs-wago-energymeter

# Extract wago_io_system
git subtree split --prefix=homeassistant/components/wago_io_system -b wago_io_system_hacs
# → github.com/Arndt-Barop/hacs-wago-io-system

# Beide als HACS-Repos mit custom_components/ Struktur
```

### **HACS-Repository-Struktur:**
```
hacs-wago-energymeter/
├── custom_components/
│   └── wago_energymeter/
│       ├── manifest.json
│       └── ... (alle Files)
├── hacs.json
├── info.md
└── README.md

hacs-wago-io-system/
├── custom_components/
│   └── wago_io_system/
│       ├── manifest.json
│       └── ... (alle Files)
├── hacs.json
├── info.md
└── README.md
```

---

## 8. Best Practices & Learnings

### **Aus Community-Analyse:**

1. **TP-Link-Pattern:**
   - 4 separate Integrationen im Core: `tplink`, `tplink_tapo`, `tplink_lte`, `tplink_omada`
   - Zeigt: Koexistenz ist Standard und akzeptiert

2. **Xiaomi-Pattern:**
   - 5 separate Integrationen: `xiaomi`, `xiaomi_aqara`, `xiaomi_ble`, `xiaomi_miio`, `xiaomi_tv`
   - Zeigt: Schrittweise Aufteilung bei wachsender Komplexität

3. **Commit-Historie:**
   - Git-Log zeigt viele "split", "separate", "extract" Operations
   - Refactoring und Separation sind normale Wartungs-Operations

### **Unsere Konventionen:**

#### **1. Commit Messages (Conventional Commits Format):**

**Format:** `type(scope): description`

**Wichtig:** Viele **kleine, atomare Commits** statt große Änderungen!

```bash
# Standard-Format (Klammern, nicht eckige Klammern!)
feat(wago_io_system): add config flow
feat(wago_io_system): add module registry with 20 base modules
feat(wago_io_system): implement module detector
fix(wago_energymeter): timeout handling in meter.py
fix(wago_io_system): correct register offset calculation
test(wago_io_system): add config flow tests
test(wago_io_system): add module detector unit tests
docs(wago_io_system): add README
docs(wago_energymeter): update installation guide
refactor(wago_io_system): extract modbus client to separate module
chore(wago_io_system): add quality_scale.yaml
style(wago_io_system): apply ruff formatting
```

**Commit-Typen:**
- `feat`: Neue Features
- `fix`: Bugfixes
- `test`: Test-Ergänzungen/-Verbesserungen
- `docs`: Dokumentations-Änderungen
- `refactor`: Code-Umstrukturierung (kein Feature/Fix)
- `chore`: Maintenance (Dependencies, Config-Files)
- `style`: Code-Formatierung (Ruff, MyPy-Fixes)
- `perf`: Performance-Verbesserungen
- `ci`: CI/CD-Änderungen

**Scope (Integration-Name):**
- `wago_io_system` - Für neue I/O System Integration
- `wago_energymeter` - Für bestehende Energy Meter Integration
- `both` - Nur wenn beide betroffen (sehr selten)

**Beispiele für atomare Commits:**
```bash
# ✅ RICHTIG: Kleine, fokussierte Commits
git commit -m "feat(wago_io_system): add manifest.json"
git commit -m "feat(wago_io_system): add const.py with register definitions"
git commit -m "feat(wago_io_system): add __init__.py with basic setup"
git commit -m "feat(wago_io_system): add config_flow.py skeleton"

# ❌ FALSCH: Zu große Commits
git commit -m "feat(wago_io_system): add complete integration"
git commit -m "Add files"
```

#### **2. Branch Naming:**

```bash
# Feature-Branches
feature/wago_io_system_foundation
feature/wago_io_system_config_flow
feature/wago_io_system_module_detection
feature/wago_energymeter_test_coverage

# Fix-Branches
fix/wago_io_system_modbus_timeout
fix/wago_energymeter_sensor_state

# Documentation-Branches
docs/wago_io_system_readme
docs/wago_energymeter_hacs_guide
```

#### **3. PR Titles (für spätere Core-Submission):**

```
[wago_io_system] Add module detection
[wago_io_system] Implement config flow
[wago_energymeter] Improve test coverage to 75%
[wago_energymeter] Add support for 2857-570 variant
```

---

## 9. Risiko-Minimierung

### **Was kann schiefgehen?**

1. **Vermischte Git-Historie** → Gelöst durch Commit-Präfixe
2. **Issue-Tracking-Chaos** → Gelöst durch GitHub Labels
3. **Merge-Konflikte** → Minimiert durch separate Verzeichnisse
4. **Review-Overhead** → Gelöst durch separate PRs

### **Exit-Strategien:**

1. **Jederzeit Splitting möglich:**
   - Git Subtree Extract (behält Historie)
   - Git Filter-Repo (maximale Sauberkeit)
   - Kein Code-Verlust, Commit-Attribution bleibt

2. **Flexibles Deployment:**
   - Core → Beide Integrationen
   - HACS → Extract nach Bedarf
   - Hybrid → Energy Meter Core, I/O System HACS

---

## 10. Entscheidungs-Matrix

### **Wann Splitting durchführen?**

| Szenario | Aktion | Zeitpunkt |
|----------|--------|-----------|
| **Beide Ready für Core** | Separate PRs aus Fork | Nach Phase 3-4 |
| **HACS vor Core gewünscht** | Git Subtree Extract | Nach Phase 2 |
| **Unterschiedliche Timelines** | Partial Extract | Flexibel |
| **Issue-Tracking-Overhead** | Labels genügen | Kein Split nötig |
| **Community-Beiträge** | Separate Repos hilfreich | Nach Public Release |

### **Evaluation-Checkpoints:**

**Nach 2 Monaten:**
- Ist Issue-Tracking handhabbar? → JA: Weiter, NEIN: Extract
- Wird HACS vor Core benötigt? → JA: Extract, NEIN: Weiter
- Gibt es Merge-Konflikte? → JA: Extract, NEIN: Weiter

**Nach 4 Monaten:**
- Core-Submission-Termin klar? → Separate PRs vorbereiten
- Community-Beiträge erwartet? → Separate Repos erwägen
- Maintenance-Overhead hoch? → Extract evaluieren

---

## 11. Konkrete Nächste Schritte

### **Sofort (Heute):**

```bash
cd /workspaces/core
git checkout -b feature/wago_io_system

# Scaffold erstellen
python -m script.scaffold integration
# Inputs:
#   Domain: wago_io_system
#   Name: WAGO I/O System
#   Codeowners: @Thomas-Brandt, @Arndt-Barop
```

### **Diese Woche:**
1. ✅ Config Flow implementieren
2. ✅ Modbus Client Wrapper
3. ✅ Module Registry (Basis 20 Module)
4. ✅ Tests schreiben

### **Nächste Woche:**
1. ✅ Module Detection mit Hardware @ 192.168.2.44
2. ✅ Entity Factory
3. ✅ Binary Sensor Platform

---

## 12. Fazit

**Strategie:** ✅ **Shared Development im Core-Fork**

**Begründung:**
1. **Maximale Effizienz** - Setup fertig, sofortiger Start
2. **Flexible Zukunft** - Splitting jederzeit möglich
3. **Community-konform** - TP-Link/Xiaomi-Pattern ist Standard
4. **Risiko minimiert** - Git-Historie bleibt, keine Lock-in

**Commitment:** Diese Strategie für **Phase 1-2** (2-3 Monate), dann Re-Evaluation

---

**Ende der Entwicklungsstrategie**

Dieses Dokument wird aktualisiert, wenn sich Strategie-relevante Änderungen ergeben.
