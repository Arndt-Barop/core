# WAGO Energy Meter - Custom Integration Sync

Dieses Script synchronisiert die WAGO Energy Meter Integration aus dem Home Assistant Core Development Repository in dieses Custom Integration Repository.

## 🚀 Quick Start

### Einmalige Verwendung
```bash
./script/sync_wago_custom.sh
```

### Mit Custom Commit Message
```bash
./script/sync_wago_custom.sh "Add Platinum tier strict typing support"
```

## 📋 Was macht das Script?

1. ✅ Prüft auf uncommitted Änderungen
2. 📥 Cloned das Custom-Repo in ein temporäres Verzeichnis
3. 📋 Kopiert alle relevanten Dateien (ohne Entwicklungs-Artefakte)
4. 💾 Erstellt einen Commit
5. ⬆️ Pushed zum Remote-Repository
6. 🧹 Räumt temporäre Dateien auf

## 🚫 Automatisch ausgeschlossene Dateien

Das Script ignoriert automatisch:
- `__pycache__/` - Python Cache
- `*.pyc` - Compiled Python
- `.pytest_cache/` - Test Cache
- `Datasheets/` - PDF Datasheets
- `*.code-workspace` - VS Code Workspace
- `DOCUMENTATION.md` - Interne Dev-Doku
- `translations/` - Auto-generiert

## 🔄 Workflow-Integration

### In GitHub Actions (automatisch bei Push)
```yaml
name: Sync to Custom Repo

on:
  push:
    paths:
      - 'homeassistant/components/wago_energymeter/**'

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Sync to custom repo
        env:
          CUSTOM_REPO_TOKEN: ${{ secrets.CUSTOM_REPO_TOKEN }}
        run: |
          git config --global user.email "action@github.com"
          git config --global user.name "GitHub Action"
          ./script/sync_wago_custom.sh "Auto-sync from core: ${{ github.sha }}"
```

### Als Git Hook (automatisch bei lokalem Commit)
```bash
# .git/hooks/post-commit
#!/bin/bash
if git diff HEAD~1 HEAD --name-only | grep -q "homeassistant/components/wago_energymeter"; then
    echo "🔄 WAGO integration changed, syncing to custom repo..."
    ./script/sync_wago_custom.sh "Auto-sync: $(git log -1 --pretty=%B)"
fi
```

## 🔧 Manuelle Sync-Methoden

### Methode 1: Git Subtree (mit History)
```bash
# Einmalig: Exportiere nur den Integration-Ordner mit vollständiger Git-History
git subtree split --prefix=homeassistant/components/wago_energymeter -b wago-export

# Push zum Custom-Repo
git push wago-custom wago-export:main --force

# Cleanup
git branch -D wago-export
```

### Methode 2: Manueller Copy (ohne History)
```bash
# 1. Clone Custom-Repo
cd /tmp
git clone https://git.uncletombbg.duckdns.org/ wago-custom
cd wago-custom

# 2. Kopiere aktuellen Stand
rm -rf custom_components/wago_energymeter/*
cp -r /workspaces/core/homeassistant/components/wago_energymeter/* \
      custom_components/wago_energymeter/

# 3. Commit & Push
git add .
git commit -m "Manual sync from core"
git push origin main
```

## 🎯 Best Practices

### Vor dem Sync
1. ✅ Alle Änderungen im Core-Repo committen
2. ✅ Tests laufen lassen: `pytest ./tests/components/wago_energymeter/`
3. ✅ Linting prüfen: `pre-commit run --all-files`
4. ✅ Quality scale validieren: `python -m script.hassfest --integration-path homeassistant/components/wago_energymeter`

### Nach dem Sync
1. 🔍 Custom-Repo überprüfen auf GitHub/GitLab
2. 🧪 Installation in HACS testen
3. 📝 Release Notes aktualisieren (falls nötig)

## 🐛 Troubleshooting

### "Error: Could not clone repository"
- Prüfe Netzwerkverbindung zu `git.uncletombbg.duckdns.org`
- Prüfe Git-Credentials: `git credential fill`
- Teste manuellen Clone: `git clone https://git.uncletombbg.duckdns.org/`

### "Warning: Uncommitted changes"
Entweder:
- Commit die Änderungen: `git add . && git commit -m "..."`
- Oder bestätige mit 'y' um trotzdem zu syncen (nicht empfohlen)

### "No changes detected"
- Repository ist bereits up-to-date
- Oder `.gitignore` filtert alle Änderungen (prüfe Exclude-Liste)

## 📚 Repository-Struktur

### Im Custom-Repo erwartet:
```
wago-custom-repo/
├── custom_components/
│   └── wago_energymeter/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── const.py
│       ├── diagnostics.py
│       ├── manifest.json
│       ├── meter.py
│       ├── py.typed
│       ├── quality_scale.yaml
│       ├── sensor.py
│       └── strings.json
├── README.md
└── hacs.json  # Optional für HACS
```

### HACS Integration (Optional)
Erstelle `hacs.json` im Custom-Repo:
```json
{
  "name": "WAGO Energy Meter",
  "render_readme": true,
  "domains": ["wago_energymeter"]
}
```

## 🔐 Authentifizierung

### SSH (Empfohlen)
```bash
# Ändere Remote-URL auf SSH
cd /workspaces/core
git remote set-url wago-custom git@uncletombbg.duckdns.org:repo.git
```

### HTTPS mit Token
```bash
# Speichere Token in Git-Credentials
git config --global credential.helper store
# Beim nächsten Push/Clone nach Token fragen lassen
```

## 📞 Support

Bei Fragen oder Problemen:
1. 📖 Lies diese README komplett
2. 🐛 Prüfe die Troubleshooting-Sektion
3. 💬 Kontaktiere den Maintainer

---

**Last Updated:** 2025-10-30
**Maintainer:** Arndt-Barop & uncletombbg
