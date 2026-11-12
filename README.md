# MF_Watermark – EU AI Act Image Labelling Tool

Ein leichtgewichtiges Desktop-Tool in Python (`tkinter`), um KI-generierte und KI-modifizierte Bilder vor der Veröffentlichung auf Webseiten stapelweise (Batch-Processing) mit den offiziellen **EU-Kennzeichnungs-Icons** sowie maschinenlesbaren **EXIF- und PNG-Metadaten** gemäß **Artikel 50 der EU-KI-Verordnung (EU AI Act)** zu versehen.

## 🎯 Hintergrund & EU-Kennzeichnungspflicht

Gemäß **Artikel 50 des EU AI Act** (Transparenzpflichten für Anbieter und Betreiber bestimmter KI-Systeme) sowie dem zugehörigen *Code of Practice on Transparency of AI-Generated Content* müssen künstlich erzeugte oder manipulierte Bildinhalte:

1. **Sichtbar gekennzeichnet** werden (z. B. durch die offiziellen EU-Labels `AI GENERATED`, `AI MODIFIED` oder `AI`).
2. **Maschinenlesbar in den Metadaten** markiert werden, damit Browser, Suchmaschinen und Plattformen die KI-Herkunft automatisiert auslesen können.

### 🔗 Offizielle Quellen & Icon-Downloads der Europäischen Kommission

Die Europäische Kommission stellt die offiziellen Wasserzeichen-Sets lizenzfrei und ohne Pflicht zur Namensnennung als **ZIP-Pakete (im PNG- und SVG-Format)** in jeweils vier Ausführungen (*Schwarz*, *Weiß*, *Schwarz mit 50 % Transparenz* und *Weiß mit 50 % Transparenz*) zum Download bereit:

* **Direkt zum offiziellen EU-Icon-Download (PNG & SVG ZIP-Pakete):**
  * 🇬🇧 **Englisch:** [EU Icons for labelling AI-generated content (Abschnitt „The EU icons“)](https://digital-strategy.ec.europa.eu/en/policies/eu-icons-labelling-ai-generated-content)
  * 🇩🇪 **Deutsch:** [EU-Icons für die Kennzeichnung von KI-generierten Inhalten](https://digital-strategy.ec.europa.eu/de/policies/eu-icons-labelling-ai-generated-content)
* **Richtlinien & Code of Practice der EU:**
  * 🇬🇧 [Code of Practice on Marking and Labelling of AI-Generated Content](https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content#1720699867912-1)

### Übersicht der offiziellen EU-Wasserzeichen

| EU-Label / Variante | Dateinamen im offiziellen EU-ZIP-Paket (PNG) | Anwendungsfall gemäß EU AI Office |
| :--- | :--- | :--- |
| **Basic Icon (`AI`)** | `LABEL_AI_black.png`<br>`LABEL_AI_black transparent.png`<br>`LABEL_AI_white.png`<br>`LABEL_AI_white transparent.png` | Allgemeiner Hinweis, dass KI bei der Erstellung beteiligt war, oder in Kombination mit einem eigenen Textzusatz / einer interaktiven Ebene. |
| **Fully AI-Generated (`AI GENERATED`)** | `LABEL_AI GENERATED_black.png`<br>`LABEL_AI GENERATED_black transparent.png`<br>`LABEL_AI GENERATED_white.png`<br>`LABEL_AI GENERATED_white transparent.png` | Vollständig durch KI generierte Inhalte ohne menschlich geschaffene Bildelemente (abgesehen vom Prompting). |
| **Partially AI-Modified (`AI MODIFIED`)** | `LABEL_AI MODIFIED_black.png`<br>`LABEL_AI MODIFIED_black transparent.png`<br>`LABEL_AI MODIFIED_white.png`<br>`LABEL_AI MODIFIED_white transparent.png` | Bestehende, von Menschen erstellte Aufnahmen oder Grafiken, die nachträglich durch generative KI verändert oder erweitert wurden. |

## ✨ Features

* **Stapelverarbeitung (Batch Processing):** Gleichzeitiges Verarbeiten einzelner Bilder oder kompletter Ordner.
* **Drag & Drop Unterstützung:** Bilder und Ordner können direkt aus dem Windows Explorer in die Dateiliste oder das Vorschaufenster gezogen werden (`tkinterdnd2`).
* **Echtzeit-Live-Vorschau:** Jede Änderung an Position, Abstand, Skalierung, Transparenz oder dem gewählten EU-Label wird sofort live am ausgewählten Bild dargestellt.
* **3×3 Anker-System & Padding:** Punktgenaue Platzierung des Wasserzeichens (Ecken, Kantenmitten oder Zentrum) mit frei definierbarem horizontalen und vertikalen Randabstand in Pixeln.
* **Automatische PNG-Konvertierung & EXIF-Drehung:** Quellbilder (`.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`, `.png`) werden automatisch anhand ihres EXIF-Orientation-Tags korrekt ausgerichtet und verlustfrei als `.png` gespeichert.
* **Vollständiger Metadaten-Erhalt & KI-Tagging:**
  * Bestehende Kameradaten (EXIF), GPS-Koordinaten, Farbprofile (`icc_profile`), `dpi` und PNG-Text-Chunks bleiben vollständig erhalten.
  * Zusätzliche Injektion des KI-Vermerks in **EXIF `UserComment`**, **EXIF `ImageDescription`**, **PNG `iTXt` (`AI-Label`, `AI-Watermark-File`)** sowie des IPTC-Standards **`DigitalSourceType`** (`trainedAlgorithmicMedia`).
* **Flexible Dateinamen & Speicherorte (`⚙ Options`):**
  * Speichern im Quellordner oder in einem frei wählbaren Zielordner.
  * Frei definierbares Dateinamen-Suffix (Standard: `<Originalname>_mf.png`).
  * Optionaler Überschreiben-Modus (`Overwrite original files`) inkl. automatischem Entfernen der alten Nicht-PNG-Quelldatei nach erfolgreicher Konvertierung.
* **Persistente Einstellungen:** Alle zuletzt gewählten Parameter werden beim Beenden automatisch in einer lokalen `config.json` gespeichert.

## 📁 Projektstruktur

```text
MF_Watermark/
├── watermarks/                                  # Ordner für die offiziellen EU-Label-PNGs
│   ├── LABEL_AI GENERATED_white transparent.png
│   ├── LABEL_AI GENERATED_white.png
│   ├── LABEL_AI MODIFIED_black transparent.png
│   ├── LABEL_AI MODIFIED_black.png
│   ├── LABEL_AI MODIFIED_white transparent.png
│   ├── LABEL_AI MODIFIED_white.png
│   ├── LABEL_AI_black transparent.png
│   └── LABEL_AI_black.png
├── main.py                                      # Hauptanwendung (GUI & Bildverarbeitung)
├── requirements.txt                             # Python-Abhängigkeiten
├── config.json                                  # Automatisch generierte Benutzereinstellungen
└── README.md                                    # Projektdokumentation
```

## 🚀 Installation & Einrichtung

### Voraussetzungen

* **Python 3.10+** (getestet bis Python 3.14)
* Windows, macOS oder Linux mit installiertem `tkinter`

### 1. Repository klonen

```bash
git clone <REPOSITORY_URL>
cd MF_Watermark
```

### 2. Virtuelle Umgebung erstellen und aktivieren

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

Inhalt der `requirements.txt`:

```text
Pillow
piexif
tkinterdnd2
```

*(Hinweis: Falls `tkinterdnd2` nicht installiert ist, startet das Programm automatisch im Fallback-Modus ohne Drag & Drop; das Hinzufügen über die Buttons funktioniert weiterhin uneingeschränkt).*

### 4. Offizielle EU-Wasserzeichen herunterladen & hinterlegen

1. Öffne die offizielle Seite der Europäischen Kommission: [EU Icons for labelling AI-generated content](https://digital-strategy.ec.europa.eu/en/policies/eu-icons-labelling-ai-generated-content) (bzw. die [deutsche Version](https://digital-strategy.ec.europa.eu/de/policies/eu-icons-labelling-ai-generated-content)).
2. Klicke im Abschnitt **„The EU icons“** (bzw. **„Die EU-Icons“**) auf **„Download the EU icons in PNG format (ZIP)“**.
3. Entpacke die heruntergeladene ZIP-Datei und kopiere die gewünschten `.png`-Dateien in den Unterordner `watermarks/` dieses Projekts.
4. Beim Programmstart liest `MF_Watermark` alle dort liegenden `.png`-Dateien automatisch in das Auswahlmenü ein.

## 🖥️ Bedienung

Starte die Anwendung über PyCharm oder das Terminal:

```bash
python main.py
```

1. **Bilder hinzufügen:**
   * Ziehe Bilder oder Ordner per **Drag & Drop** direkt aus dem Dateimanager in das Programmfenster, oder nutze die Buttons **`➕ Add Images`** bzw. **`📁 Add Folder`**.
   * Beim Importieren ganzer Ordner werden bereits gestempelte Dateien (z. B. mit der Endung `_mf.png`) automatisch übersprungen, um doppelte Wasserzeichen zu vermeiden.
2. **Wasserzeichen & Metadaten wählen:**
   * Wähle unter **EU Label (PNG)** das passende Wasserzeichen aus.
   * Das Feld **Meta / EXIF Tag** passt sich automatisch anhand des Dateinamens an (z. B. `AI GENERATED (EU AI Act Art. 50)` oder `AI MODIFIED (EU AI Act Art. 50)`), kann aber auch individuell angepasst werden.
3. **Position & Darstellung anpassen (mit Live-Vorschau):**
   * **Anchor:** Wähle im 3×3-Raster die gewünschte Ecke oder Bildmitte.
   * **Padding:** Lege den horizontalen (`X`) und vertikalen (`Y`) Abstand zum Bildrand in Pixeln fest.
   * **Scale & Opacity:** Steuere über die Schieberegler die relative Breite des Wasserzeichens (in `%` der Bildbreite) sowie die Deckkraft (`Opacity %`).
4. **Optionen (`⚙ Options`):**
   * **Custom filename suffix:** Definiere das Suffix für die erzeugten Dateien (Standard: `_mf` $\rightarrow$ `beispiel_mf.png`).
   * **Overwrite original files:** Überschreibt die Originaldatei ohne Suffix (`beispiel.png`). Ist zusätzlich *Delete original non-PNG file* aktiviert, wird bei einer Formatumwandlung (z. B. `foto.jpg` $\rightarrow$ `foto.png`) die alte `.jpg`-Datei nach erfolgreichem Speichern entfernt.
5. **Stapelverarbeitung starten:**
   * Klicke oben auf **`▶ Start Batch Processing`**, um alle Bilder in der Warteschlange zu verarbeiten.

## 🔍 Eingebettete Metadaten im Detail

Jede exportierte `.png`-Datei erhält neben den erhaltenen Original-EXIF-Daten folgende maschinenlesbare Einträge:

| Standard | Feld / Chunk | Eingetragener Wert (Beispiel) |
| :--- | :--- | :--- |
| **PNG iTXt** | `AI-Label` | `AI GENERATED (EU AI Act Art. 50)` |
| **PNG iTXt** | `AI-Watermark-File` | `LABEL_AI GENERATED_white transparent.png` |
| **PNG iTXt / IPTC** | `DigitalSourceType` | `http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia` |
| **EXIF (0th IFD)** | `ImageDescription` (`0x010E`) | `<Bestehende Beschreibung> \| AI GENERATED (EU AI Act Art. 50)` |
| **EXIF (Exif IFD)** | `UserComment` (`0x9286`) | `AI GENERATED (EU AI Act Art. 50)` |

Die Metadaten lassen sich nach dem Export z. B. mit `exiftool` überprüfen:

```bash
exiftool -AI-Label -DigitalSourceType -UserComment -ImageDescription bild_mf.png
```

## 📄 Lizenz

Dieses Projekt wurde vollständig mit KI erzeugt und steht daher unter der **MIT-Lizenz** – freie Verwendung, Anpassung und Weitergabe ausdrücklich erwünscht zur Verfügung.
