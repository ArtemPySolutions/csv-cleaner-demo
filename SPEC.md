# SPEC / Pflichtenheft: csv-cleaner-demo

Zielsetzung
Bereitstellung eines kleinen, mit GitHub teilbaren Demo-Projekts „CSV Cleaner“, das eine CSV-Datei über die Kommandozeile einliest, bereinigt und eine bereinigte CSV sowie einen Textbericht ausgibt.

Funktionale Anforderungen
1. CLI-Parameter
   - --input: Pfad zur Eingabe-CSV (z. B. data/messy.csv)
   - --output: Pfad zur bereinigten CSV (z. B. data/clean.csv)
   - --dedupe-on: "all" (Duplikate über komplette Zeilen) ODER Liste von Spalten (z. B. id,email)
   - --empty-policy: "delete-row" ODER "mark" (markiert leere Zellen mit "__EMPTY__")
   - --sep: Trennzeichen, Standard ","
   - --report: Pfad zur Report-Datei (z. B. reports/run_YYYYMMDD_HHMM.txt)

2. Verarbeitungsschritte
   - CSV robust einlesen (auch leere Dateien bzw. nur Header verarbeiten)
   - Führende und nachgestellte Leerzeichen in allen Zellen entfernen
   - Leere Zellen gemäß Policy behandeln
   - Duplikate je nach --dedupe-on entfernen
   - Bereinigte CSV mit gleichem Separator schreiben
   - Text-Report generieren mit:
     - total input rows
     - total output rows
     - number of duplicates removed
     - number of empty cells/rows affected
     - runtime
     - parameters used

3. Output
   - Bereinigte CSV an --output
   - Report-Datei an --report (i. d. R. im Ordner reports/)
   - Programm soll bei leeren Dateien oder inkonsistenten Angaben (z. B. fehlende Spalten in --dedupe-on) nicht abstürzen

Nicht-funktionale Anforderungen
- Python 3.10+
- Nutzung von pandas für CSV-Verarbeitung
- Sauberer, modularer, dokumentierter Code
- Fehlerbehandlung für fehlende Dateien, falsche Argumente etc.

Projektstruktur (Soll)
```
csv-cleaner-demo/
├── data/
│   ├── messy.csv (Beispielinput)
│   └── clean_expected.csv (manuell erzeugte Referenzausgabe)
├── reports/
├── screenshots/
├── main.py
├── requirements.txt  (pandas, openpyxl)
├── README.md
└── SPEC.md
```

Annahmen
- Alle Spalten werden als String gelesen (dtype=str), um ungewollte Typkonvertierung zu vermeiden.
- Beim Löschen von Zeilen mit "delete-row" genügt eine leere Zelle in einer Zeile, damit die Zeile entfernt wird.
- Bei "mark" werden leere Zellen mit "__EMPTY__" ersetzt.
- "Leere Zellen" umfassen nach dem Trimmen sowohl leere Strings als auch NA/NaN-Werte.
- Bei --dedupe-on mit Spaltenliste werden unbekannte Spalten ignoriert (im Report vermerkt). Wenn keine der gewünschten Spalten existiert, erfolgt keine Deduplikation.

Akzeptanzkriterien
- Das Tool lässt sich mit den geforderten CLI-Parametern starten und liefert Exit-Code 0 bei Erfolg.
- Für data/messy.csv erzeugt der Befehl
  ```
  python main.py --input data\messy.csv --output data\clean.csv --dedupe-on id,email --empty-policy mark --sep "," --report reports\run_sample.txt
  ```
  eine Ausgabe, die mit data/clean_expected.csv übereinstimmt.
- Leere Datei: Keine Exceptions; Report und (ggf.) leere Ausgabedatei werden erzeugt.
- Falsche Datei-Pfade oder unlesbare Datei: Verständliche Fehlermeldung und Exit-Code != 0; ggf. Report mit Fehlerhinweis.
- Fehlende Spalten in --dedupe-on verursachen keinen Absturz; die Information wird im Report vermerkt.
