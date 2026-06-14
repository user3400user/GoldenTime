# MaStR-Gesamtdatenexport als Basis für ein wöchentliches Lead-Produkt (neue gewerbliche PV ohne Speicher)
_Run: 2026-06-14 · Mode: deep-research · Slug: mastr-pv-leads_

## TL;DR
Der **Gesamtdatenexport** der Bundesnetzagentur ist ein einzelnes, täglich gegen 05:00 Uhr neu erzeugtes
**ZIP mit XML-Dateien** (~2,96 GB komprimiert, Stand 14.06.2026), frei und ohne Login unter
`download.marktstammdatenregister.de` abrufbar; er enthält **alle** öffentlichen Felder und Objekte mit
einer dokumentierten, versionierten XSD [1][2][3]. Für eine wöchentliche, regional gefilterte
Lead-Pipeline ist der **Gesamtexport klar überlegen** gegenüber der Web-JSON-Einzelabfrage — und zwar aus
vier der fünf Prüfpunkte heraus: (3) historische **Inbetriebnahmedaten** (Feld `Inbetriebnahmedatum`,
zusätzlich `EegInbetriebnahmedatum`) liegen vollständig vor, der Post‑EEG‑Jahrgang 2006/2007 ist sauber
filterbar [3][19]; (4) die **Speicher‑Verknüpfung** zum Betreiber gelingt zuverlässig über die
`AnlagenbetreiberMastrNummer` (ABR…, Feld zu ~95–100 % befüllt) — damit lässt sich prüfen, ob ein Betreiber
*irgendwo* einen Speicher hat, nicht nur an der PV — und co‑lokal zusätzlich über `LokationMaStRNummer`
(SEL…) bzw. die expliziten Felder `GemeinsamRegistrierteSolareinheitMastrNummer` / `SpeicherAmGleichenOrt`
[3][14]; (5) das **Registrierungsdatum** ist als Erstregistrierungsdatum konzipiert und soll bei
Korrekturen stabil bleiben (Korrekturen schlagen auf `DatumLetzteAktualisierung`) [3][15][16]. Das
etablierte Tool dafür ist **open‑mastr** (Python, aktiv: PyPI 0.17.1 vom 13.04.2026, Commit 09.06.2026)
[4][5]; `marktstammdatenregister.dev` (Go→SQLite) ist inhaltlich brauchbar, aber **seit 11/2023 ruhend**
[6], und `bundesAPI/deutschland` hat **gar kein MaStR‑Modul** [8]. **Größte Fallstricke**: (a) ein jüngeres
`Registrierungsdatum` heißt *nicht* „neu gebaut" — wegen der Nachregistrierungspflicht für Bestandsanlagen
(Frist 31.01.2021) tragen viele Altanlagen junge Registrierungsdaten; deshalb das `Registrierungsdatum`
**immer mit dem `Inbetriebnahmedatum` kombinieren** [15][18]; (b) „ohne Speicher" heißt nur „kein Speicher
*gemeldet*" — ca. 9 % der Heimspeicher werden gar nicht oder verspätet registriert [13].

## Empfehlung (Kurzfassung — Details s. „Empfehlung" unten)
**Pipeline auf den Gesamtdatenexport bauen** (wöchentlicher Pull des täglichen ZIP → lokale SQLite/Postgres
via open‑mastr → SQL‑Filter), **nicht** auf die Web‑JSON‑Abfrage. Begründung verdichtet: nur der Export
liefert den Betreibergraph für den Speicher‑Anywhere‑Check (P4), beide Datumsfelder für die
Frische‑Logik (P3+P5) und eine versionierte, diff‑bare Grundlage; die Web‑JSON ist eine inoffizielle
Frontend‑Schnittstelle mit eingeschränktem Feldumfang, deren Referenz‑Tooling seit 2022 eingefroren ist.

## Key findings

**SQ1 — Bezugsweg & Format**
- **Ein ZIP, XML, kein Login.** „Unter dem Menüpunkt ‚Datendownload' steht ein Gesamt‑Datenauszug zur
  Verfügung … die gesamten öffentlichen Daten" und „Die Daten werden im XML Format bereitgestellt";
  Download‑Link `https://download.marktstammdatenregister.de/Gesamtdatenexport_20260614_26.1.zip` [1][2].
  (answers SQ1, confidence: high)
- **Größe ~2,96 GB komprimiert, wachsend.** „Die Zip Datei ist mehr als 1GB groß und enthält mehrere
  XML‑Objekte" [1]; konkret „ZIP / 2.960.073 KB" am 14.06.2026 [2]. **Unkomprimierte Größe und exakte
  Einheitenzahl** stehen auf den Download‑Seiten *nicht* — „not found" (nur „mehrere XML‑Objekte") [1][2].
  (answers SQ1, confidence: high)
- **Täglich ~05:00 Uhr aktualisiert** (Datenstand „vom Vortag"): „Der Gesamtdatenauszug wird in der Regel
  täglich um 5:00 Uhr auf den zu diesem Zeitpunkt gültigen Datenstand aktualisiert" [1]. Für eine
  *wöchentliche* Kadenz mehr als ausreichend. (answers SQ1, confidence: high)
- **Struktur:** „Der gesamte Datenexport besteht aus einzelnen XML‑Dateien … dem dazugehörenden Schema als
  XSD‑Datei und dieser Dokumentation"; ~30 Objekt‑/Tabellentypen (u. a. `EinheitenSolar`,
  `EinheitenStromSpeicher`, `AnlagenEegSolar`, `Marktakteure`, `Lokationen`), je Objekt eine XML‑Datei;
  Dateiname kodiert Datum + Schemaversion (`YYYYMMDD_<major.minor>`) [3]. (answers SQ1, confidence: high)
- **Keine REST‑API für den Gesamtbestand.** Den vollständigen Bestand gibt es nur als Bulk‑ZIP; die
  SOAP‑API liefert Einzeleinheiten gegen Token, die Web‑JSON nur paginierte Einzelabfragen [4][9]. Dazu:
  **Vertrauliche Felder fehlen** im Export („als vertraulich gekennzeichneten Datenfelder … nicht in den
  Exporten enthalten") [1]; **begrenzte Zahl paralleler Downloads** [1]; **dated Stichtag‑Exporte**
  (1.1./1.4./1.7./1.10.) zusätzlich verfügbar, zurück bis 01.04.2023 [2][3]; **neues Exportformat seit
  01.10.2025** [2]. (answers SQ1, confidence: high)

**SQ2 — Tooling**
- **open‑mastr (Python) — beste Wahl, aktiv gepflegt.** Lädt standardmäßig den Bulk‑Export und schreibt ihn
  in eine **SQLite‑ (oder via SQLAlchemy‑Engine Postgres‑) DB**; „`method` = 'bulk': … download the whole
  dataset (few Gigabite)"; Technologie‑Filter über `db.download(data=["solar", ...])` (selektierte Tabellen
  werden neu befüllt) und Export per `db.to_csv()` [4]. **Recency:** PyPI **0.17.1 (13.04.2026)**, letzter
  Commit **09.06.2026**, 134★ [5]. Wichtige Einschränkung: **kein inkrementelles Update** — pro Lauf der
  ganze Tagesstand; `download(method="API")` ist >v0.16.0 entfernt (Default fällt auf bulk) [4].
  (answers SQ2, confidence: high)
- **marktstammdatenregister.dev (Go‑CLI) — inhaltlich gut, aber ruhend.** „kann den Gesamtdatenexport
  auslesen, validieren und in eine SQLite‑Datenbank umwandeln"; publiziert eine **Datasette‑Instanz**
  (`ds.marktstammdatenregister.dev`) + Zenodo‑CSV; volle **SQL‑Filterung** (z. B. Solar nach `Bundesland`
  + `Inbetriebnahmedatum`/`Registrierungsdatum`, Speicher als separate Tabelle ausschließbar) [6][7]. Aber:
  **letzter Code‑Commit 23.11.2023**, mitgelieferte Spec auf Export‑„Version 23.1"; die gehostete
  Instanz/Zenodo ist ein 2023er Snapshot [6]. Gut als **Schema-/SQL‑Referenz**; für frische Daten müsste man
  das Tool selbst gegen aktuelle Exporte laufen lassen — und die Spec dürfte wegen des neuen Formats
  (01.10.2025) Anpassung brauchen. (answers SQ2, confidence: high; Spec‑Inkompatibilität: med, Inferenz)
- **bundesAPI/deutschland — kein MaStR‑Modul.** Im README‑Inventar *und* im Quellbaum `src/deutschland`
  (nur `bundesanzeiger`, `bundesnetzagentur`, `bundeswahlleiter`, `lebensmittelwarnung`, `verena`, `smard`,
  `ladestationen` …) ist **kein** MaStR‑Client enthalten [8]. Die MaStR‑Abdeckung der bundesAPI liegt im
  separaten Repo **`bundesAPI/marktstammdaten-api`** — einer OpenAPI‑Beschreibung der **Web‑JSON‑Endpunkte**
  (`GetErweiterteOeffentlicheEinheitStromerzeugung`, paginiert `page`/`pageSize`, `filter=`‑Prädikate), also
  des Einzelabfrage‑Wegs, **eingefroren seit 17.07.2022** [9]. (answers SQ2, confidence: high)

**SQ3 — Historie & Post‑EEG**
- **Historische Inbetriebnahmedaten liegen vor.** `EinheitenSolar` führt `Inbetriebnahmedatum` („Datum der
  Inbetriebnahme", Typ date; Doc‑Beispiel `1998-01-02`); open‑mastr zeigt real `"Inbetriebnahmedatum":
  datetime.date(2007, 7, 20)` [3][4]. Damit ist der **Jahrgang 2006/2007 als Kohorte filterbar** (Filter
  auf das Inbetriebnahmejahr). (answers SQ3, confidence: high)
- **Zusätzliches EEG‑Datum.** Die EEG‑Anlage (`AnlagenEegSolar`) trägt `EegInbetriebnahmedatum`
  („Inbetriebnahmedatum der EEG‑Anlage", date) und `EegMaStRNummer`; `EinheitenSolar` verweist per
  `EegMaStRNummer` auf die EEG‑Anlage [3]. Für die **Förderende‑Logik** ist das EEG‑Inbetriebnahmedatum das
  maßgebliche Feld. (answers SQ3, confidence: high)
- **Post‑EEG‑Timing.** Die EEG‑Vergütung endet im **21. Betriebsjahr = Inbetriebnahmejahr + 20
  Kalenderjahre**; „Wenn Sie Ihre Photovoltaik‑Anlage 2006 in Betrieb genommen haben, endet die Förderung …
  am 31. Dezember 2026" [19]. ⇒ Jahrgang **2006 → Ende 2026**, **2007 → Ende 2027** (Begriffe „Ü20‑Anlage",
  „ausgeförderte Anlage" bestätigt; „Post‑EEG" als wörtl. Term auf der Seite nicht belegt; Kohortengröße
  „not found"). (answers SQ3, confidence: high)

**SQ4 — Speicher‑Verknüpfung (kritisch)**
- **Speicher = eigene Einheit, meist co‑registriert.** „Regelmäßig werden Stromspeicher gemeinsam mit einer
  anderen Stromerzeugungsanlage betrieben"; der Speicher wird als separate Einheit (`EinheitenStromSpeicher`)
  mit eigenem Inbetriebnahmedatum registriert und per Schaltfläche mit der PV verknüpft [11][3].
  ⇒ „ohne Speicher" ist **kein Einzelfeld**, sondern ein Join‑Ergebnis. (answers SQ4, confidence: high)
- **Betreiber‑Weg ist der robuste „Anywhere"-Check.** Sowohl `EinheitenSolar` als auch
  `EinheitenStromSpeicher` tragen `AnlagenbetreiberMastrNummer` (Beispiel `ABR9123456789`); Grundsatz: „Jede
  Einheit und jede Anlage wird von genau einem Anlagenbetreiber betrieben" [3][12]. Das Verknüpfungs‑Feld ist
  **zu ~95–100 % befüllt** (Solar 100 %) [14]. ⇒ **Group‑by `AnlagenbetreiberMastrNummer` über alle Einheiten
  findet jeden Speicher eines Betreibers — auch fernab der PV.** Genau das gesuchte Ziel. (answers SQ4,
  confidence: high)
- **Lokations‑Weg für die *co‑lokale* Zuordnung.** Beide Einheiten tragen `LokationMaStRNummer` (Beispiel
  `SEL9123456789`); das `Lokationen`‑Objekt listet Mitglieder via `VerknuepfteEinheitenMaStRNummern` +
  `NetzanschlusspunkteMaStRNummern`. Zusätzlich explizit: am Speicher
  `GemeinsamRegistrierteSolareinheitMastrNummer` („Zum Speicher registrierte Solareinheit", `SEE…`), an der
  PV das Bool‑Feld `SpeicherAmGleichenOrt` [3]. ⇒ Co‑lokale PV+Speicher sind über die SEL‑Lokation **und**
  über direkte Felder verbindbar. (answers SQ4, confidence: high)
- **Antwort auf „… oder gar nicht zuverlässig?":** **Beides existiert und ist nutzbar** — der
  Betreiber‑Nummer‑Weg ist der zuverlässigste für „hat der Betreiber irgendwo einen Speicher"; der
  Lokations-/Direktfeld‑Weg ist die korrekte co‑lokale Zuordnung, aber **nicht lückenlos**. Grenzen:
  (i) Speicher und PV werden manuell erfasst → „manual entries by private persons … regularly confusions …
  incorrect information" [13]; (ii) **~9 % der Heimspeicher sind gar nicht/erst verspätet registriert** [13];
  (iii) Koordinaten sind bei PV zu ~95 % leer und zu 0,5–2 % falsch [14] (betrifft Geocoding, *nicht* die
  ID‑Verknüpfung). ⇒ „ohne Speicher" lässt sich nur als **„kein Speicher gemeldet"** behaupten.
  (answers SQ4, confidence: high für Mechanik; Vollständigkeit der co‑lokalen Zuordnung: med — nicht exakt
  quantifiziert)

**SQ5 — Registrierungsdatum‑Stabilität**
- **Zwei verschiedene Felder.** `Registrierungsdatum` = „Registrierungsdatum der Einheit" (Pflicht);
  `DatumLetzteAktualisierung` = „Datum der letzten Aktualisierung an diesem Objekt" (dateTime) — *dieses*
  Feld bewegt sich bei Korrekturen [3]. (answers SQ5, confidence: high)
- **Soll‑Verhalten: Registrierungsdatum bleibt fix.** BNetzA 2019 zu einem Fehler, bei dem das (EEG‑)Melde-/
  Registrierungsdatum bei *jeder* Änderung — „auch im Rahmen der Datenkorrektur" — neu gesetzt wurde: „Diese
  Aktualisierung ist ein Fehler, das Meldedatum soll das erstmalige Registrierungsdatum darstellen und soll
  sich danach nicht mehr ändern"; Fehler werde behoben und das Datum „wieder auf das erstmalige
  Registrierungsdatum zurückgesetzt" [15]. Korrekturen sind zudem als Korrektur modelliert (Leistungshistorie
  bleibt erhalten; „Fehlerhafte Daten korrigieren" ≠ „Leistungsänderung registrieren") [16]. (answers SQ5,
  confidence: high für Soll‑Konzept; ob der Fix restlos wirkte: low — nicht separat belegt)
- **Betreiberwechsel erzeugt KEINE Neuregistrierung.** „Die Einheit darf nicht neu im MaStR registriert
  werden, stattdessen muss die Datenverantwortung … übertragen werden" — die SEE‑Einheit bleibt bestehen, nur
  der neue Betreiber registriert sich als Marktakteur (neue ABR‑Nr.) [17]. ⇒ Ein Eigentümerwechsel lässt eine
  Altanlage *nicht* als neu erscheinen. (answers SQ5, confidence: high für „keine Neuregistrierung"; dass der
  Datumswert literal unverändert bleibt: med, Inferenz)
- **Der eigentliche Frische‑Fallstrick ist die Nachregistrierung.** Bestandsanlagen mussten bis **31.01.2021**
  (24‑Monats‑Frist nach Portalstart 31.01.2019) nachgemeldet werden [18]. ⇒ Viele **vor Jahren in Betrieb
  genommene** Anlagen tragen ein **junges Registrierungsdatum** — ein aktuelles `Registrierungsdatum` belegt
  also **keine Neuinstallation**. Konsequenz fürs Produkt: `Registrierungsdatum` **nur zusammen mit
  `Inbetriebnahmedatum`** als „frisch" werten (Skalenzahl der Nachzügler „not found", Mechanismus aber
  belegt). (answers SQ5, confidence: high für Mechanismus; Skala: low/not found)

## Verknüpfungs- und Datumsfelder (Schnellreferenz, Quelle [3])
| Zweck | Feld (XML‑Objekt) | Beispiel/Typ | Hinweis |
| :-- | :-- | :-- | :-- |
| Erstregistrierung der Einheit | `Registrierungsdatum` (EinheitenSolar) | date, Pflicht | soll bei Korrektur stabil sein [15] |
| Letzte Änderung | `DatumLetzteAktualisierung` | dateTime | ändert sich bei Korrekturen |
| Inbetriebnahme (Einheit) | `Inbetriebnahmedatum` (EinheitenSolar) | date | historisch, z. B. 1998/2007 |
| Inbetriebnahme (EEG) | `EegInbetriebnahmedatum` (AnlagenEegSolar) | date | maßgeblich fürs Förderende |
| Betreiber (Anywhere‑Speicher‑Check) | `AnlagenbetreiberMastrNummer` | `ABR…` | ~95–100 % befüllt [14] |
| Lokation (co‑lokal) | `LokationMaStRNummer` | `SEL…` | gruppiert Einheiten hinter Netzanschluss |
| PV↔Speicher direkt | `GemeinsamRegistrierteSolareinheitMastrNummer` / `SpeicherAmGleichenOrt` | `SEE…` / Bool | explizite Co‑Lokation |

## Tooling-Vergleich
| Tool | Sprache | Quelle | Aktualität | Eignung wöchentlich/gefiltert |
| :-- | :-- | :-- | :-- | :-- |
| **open‑mastr** | Python | Bulk‑Export → SQLite/Postgres, `data=`, `to_csv` | **aktiv** (0.17.1 13.04.2026; Commit 09.06.2026) | **beste Wahl**; kein Inkrement, voller Tagesstand je Lauf [4][5] |
| marktstammdatenregister.dev | Go | Bulk‑Export → SQLite + Datasette/Zenodo | **ruhend** (Commit 23.11.2023, Spec v23.1) | gute SQL‑/Schema‑Referenz; selbst betreiben, Spec‑Anpassung nötig [6][7] |
| bundesAPI/deutschland | Python | — | aktiv, aber **kein MaStR‑Modul** | n/a für MaStR [8] |
| bundesAPI/marktstammdaten‑api | (OpenAPI) | Web‑JSON‑Endpunkte | **eingefroren** (17.07.2022) | nur Einzelabfrage‑Weg; nicht Bulk [9] |

## Empfehlung — Gesamtexport-Pipeline (nicht Web‑JSON)
**Entscheidung: Gesamtdatenexport als Backbone, Web‑JSON nur als punktuelle Echtzeit‑Anreicherung.**
Begründung direkt aus SQ1–SQ5:

1. **Speicher‑Anywhere‑Check (SQ4) verlangt den vollen Betreibergraph.** Um zu prüfen, ob ein PV‑Betreiber
   *irgendwo* einen Speicher hat, muss man alle Einheiten je `AnlagenbetreiberMastrNummer` zusammenführen —
   das leistet nur der vollständige Datensatz; eine paginierte Einzelabfrage müsste de facto den Gesamtbestand
   rekonstruieren (und verlöre damit ihren einzigen Vorteil) [3][14].
2. **Frische‑Logik (SQ3+SQ5) braucht beide Datumsfelder.** „Neu" = junges `Registrierungsdatum` **und**
   junges `Inbetriebnahmedatum` (gegen Nachregistrierung). Der Export garantiert beide Felder plus
   `EegInbetriebnahmedatum`; der Web‑JSON‑Feldumfang ist begrenzt und für stabile Dritt‑Nutzung
   undokumentiert [3][15][18].
3. **Stabilität, ToS, Wartung (SQ1+SQ2).** Der Export ist ein offiziell für „versierte IT‑Nutzer"
   bereitgestelltes, **versioniertes, XSD‑schematisiertes** Produkt mit gepflegtem Tool (open‑mastr) [1][3][5];
   die Web‑JSON ist eine inoffizielle Frontend‑Schnittstelle, deren Referenz‑Spec seit 2022 ruht und deren
   Rate‑/Ergebnis‑Limits undokumentiert sind [9].
4. **Reproduzierbarkeit & Dedupe.** Tägliche/Stichtag‑Exporte erlauben **Woche‑gegen‑Woche‑Diffs** auf
   `Registrierungsdatum` (und `DatumLetzteAktualisierung`) gegen einen lokalen Snapshot — sauber auditierbar
   und gegen frühere Läufe deduplizierbar [1][2].

**Konkrete Pipeline (Vorschlag):** wöchentlich das Tages‑ZIP ziehen → mit open‑mastr die Tabellen
`solar` + `storage` + `locations` + `market actors` (nicht nur Solar!) in lokale DB → SQL‑Filter:
PV‑Einheit `In Betrieb`, gewerblicher Betreiber, Ziel‑`Bundesland`/PLZ, `Registrierungsdatum` in letzter
Woche **und** `Inbetriebnahmedatum` jung → **ausschließen**, wenn derselbe `AnlagenbetreiberMastrNummer`
*oder* dieselbe `LokationMaStRNummer` einen Speicher führt bzw. `SpeicherAmGleichenOrt = true`. „ohne
Speicher" stets als „kein Speicher gemeldet" labeln (Unsicherheit ~9 %). **Post‑EEG‑Slice** als zweites
Produkt: Filter `EegInbetriebnahmedatum`‑Jahr ∈ {2006, 2007} ohne gemeldeten Speicher = Retrofit‑/
Optimierungs‑Leads mit Trigger „Förderende 2026/2027".

## Uncertainties & contradictions
- **Exakte Einheitenzahl & unkomprimierte Größe**: auf den offiziellen Download‑Seiten nicht angegeben („not
  found") [1][2]; nur ~2,96 GB komprimiert belegt. Für die Entscheidung irrelevant, aber offen.
- **Vollständigkeit der co‑lokalen PV↔Speicher‑Zuordnung**: kein gelesener Beleg quantifiziert, *wie oft* PV
  und zugehöriger Speicher tatsächlich dieselbe `LokationMaStRNummer`/`GemeinsamRegistrierteSolareinheit`
  tragen. Die Literatur matched bewusst **statistisch** (PV‑seitiges Flag), nicht per Record‑Join [13] —
  Indiz, dass der Record‑Level‑Join nicht als verlässlich gilt. Der **Betreiber‑Nummer‑Weg** ist davon
  unberührt und bleibt der robuste Pfad. (Gegenposition s. u.)
- **Wirksamkeit des 2019er Fixes**: Belegt ist die Fehlerbeschreibung + Korrekturzusage [15]; **nicht** belegt
  ist, dass der Reset restlos erfolgte und kein Altbestand ein „verschobenes" Datum behielt. Für ein
  Lead‑Produkt zweitrangig, weil ohnehin gegen `Inbetriebnahmedatum` geprüft wird.
- **Begriffliche Nuance (SQ5)**: Die 2019er Quelle nennt das „Meldedatum der EEG‑Anlage" und setzt es mit dem
  „erstmaligen Registrierungsdatum" gleich; die Übertragung auf das Export‑Feld `Registrierungsdatum` der
  *Einheit* ist konsistent, aber nicht wörtlich identisch [3][15].
- **Korrigierte Scout‑Annahme**: „~15 % PV fehl‑lokalisiert" ist **nicht** haltbar — die Datenqualitätsstudie
  zeigt 0,5–2 % falsche *vorhandene* Koordinaten + ~95 % *fehlende* PV‑Koordinaten; die 21,3 % betreffen
  Leistungsdichte‑Plausibilität, nicht den Ort [14].

**Stärkste Gegenposition zur Empfehlung:** Wer nur eine *sehr* schmale, kleine regionale Scheibe ohne
Speicher‑Anywhere‑Anspruch braucht, fährt mit der Web‑JSON leichter (serverseitiger `filter=` + Pagination,
kein 3‑GB‑ZIP, kein 30‑Tabellen‑Parsing) [9]. Sobald aber der Betreiber‑weite Speicher‑Check, beide
Datumsfelder und Reproduzierbarkeit gefordert sind — also genau dieses Produkt — kippt die Abwägung
eindeutig zum Export.

## Open questions / next steps (für /deepen)
- Web‑JSON empirisch vermessen: tatsächliche **Rate‑/Ergebnis‑Caps** und **Feldumfang** von
  `GetErweiterteOeffentlicheEinheitStromerzeugung` (enthält die öffentliche Liste die
  `AnlagenbetreiberMastrNummer`? Werden gewerbliche vs. natürliche Betreiber unterschiedlich offengelegt?).
- **Gewerblich** sauber operationalisieren: Welches Feld/Heuristik trennt gewerbliche von privaten Betreibern
  (Marktakteur‑Personenart, Leistungsschwelle, `EinheitMastrNummer`‑Kontext)? Im Export `Marktakteure` prüfen.
- Quantifizieren, wie oft co‑lokale PV+Speicher dieselbe `LokationMaStRNummer` teilen (eigene Auswertung auf
  einem Stichtag‑Export) → echte Zuverlässigkeitszahl statt Literatur‑Proxy.
- Offizielle **„Datendefinitionen/Erläuterungstexte Netze und Lokationen"** beschaffen (vom Gesamtkonzept
  referenziert, hier 404) für die wörtliche Lokations‑Definition + Nummernkonzept (SEL/ABR‑Präfixe).
- Belastbare **Kohortengröße** der Post‑EEG‑Jahrgänge 2026/2027 (offizielle BNetzA‑/Branchenzahl).

## Quellen
1. BNetzA Webhilfe – Datenexport — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/datenexport.html — abgerufen 2026-06-14 — primär (offiziell), hohe Glaubwürdigkeit.
2. MaStR Datendownload (Live‑Seite) — https://www.marktstammdatenregister.de/MaStR/Datendownload — abgerufen 2026-06-14 — primär (offiziell), Werte tagesaktuell.
3. Dokumentation MaStR Gesamtdatenexport (PDF, Rev. 26.1.2, Stand 11.06.2026) — https://www.marktstammdatenregister.de/MaStRHilfe/files/gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport.pdf — abgerufen 2026-06-14 — primär (offizielles Datenwörterbuch), höchste Glaubwürdigkeit.
4. open‑mastr Dokumentation (getting_started / advanced / dataset) — https://open-mastr.readthedocs.io/en/latest/ — abgerufen 2026-06-14 — sekundär (Tool‑Doku), hoch.
5. open‑mastr Repository + PyPI (Recency) — https://github.com/OpenEnergyPlatform/open-MaStR · https://pypi.org/project/open-mastr/ — abgerufen 2026-06-14 — primär (Repo/Index), hoch.
6. marktstammdatenregister‑dev/mastr (GitHub README) — https://github.com/marktstammdatenregister-dev/mastr — abgerufen 2026-06-14 — primär (Repo), hoch.
7. marktstammdatenregister.dev (Datasette‑Instanz) — https://marktstammdatenregister.dev/ — abgerufen 2026-06-14 — sekundär (Projekt‑Site), mittel‑hoch.
8. bundesAPI/deutschland (GitHub) — https://github.com/bundesAPI/deutschland — abgerufen 2026-06-14 — primär (Repo), hoch (Negativbefund: kein MaStR‑Modul).
9. bundesAPI/marktstammdaten‑api (GitHub) — https://github.com/bundesAPI/marktstammdaten-api — abgerufen 2026-06-14 — primär (Repo/OpenAPI), hoch.
10. MaStR‑Gesamtkonzept (PDF, BNetzA, 2018) — https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/MaStR-Gesamtkonzept.pdf — abgerufen 2026-06-14 — primär (offiziell), hoch.
11. Registrierungshilfe für Stromspeicher (PDF, BNetzA, 2021) — https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/Registrierungshilfe%20Stromspeicher.pdf — abgerufen 2026-06-14 — primär (offiziell), hoch.
12. MaStR Hilfe / FAQ — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/faq.html — abgerufen 2026-06-14 — primär (offiziell), hoch.
13. Figgener et al., „The development of battery storage systems in Germany: A market review (status 2023)" — https://arxiv.org/pdf/2203.06762 — abgerufen 2026-06-14 — sekundär (peer‑nah, RWTH), hoch.
14. „Monitoring Germany's Core Energy System Dataset: A Data Quality Analysis of the Marktstammdatenregister" — https://arxiv.org/pdf/2304.10581 — abgerufen 2026-06-14 — sekundär (akademisch), hoch.
15. MaStR‑Newsletter 2019 (Bundesnetzagentur; via Wayback 2024-11-27; Live‑URL 404) — http://web.archive.org/web/20241127233330/https://www.marktstammdatenregister.de/MaStRHilfe/files/newsletter/MaStR-Newsletter%202019_1-7.pdf — abgerufen 2026-06-14 — primär (offiziell, archiviert), hoch.
16. MaStR Hilfe – Daten einer Einheit/Anlage ändern — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/verwaltungEinheitDatenaenderung.html — abgerufen 2026-06-14 — primär (offiziell), hoch.
17. MaStR Hilfe – Betreiberwechsel — https://www.marktstammdatenregister.de/MaStRHilfe/subpages/verwaltungEinheitBetreiberwechsel.html — abgerufen 2026-06-14 — primär (offiziell), hoch.
18. green‑energy‑law – Nachmeldefrist Bestandsanlagen (31.01.2021) — https://www.green-energy-law.com/?p=1016 — abgerufen 2026-06-14 — sekundär (juristischer Blog), mittel.
19. Verbraucherzentrale – „Was tun mit der Ü20‑Anlage, wenn die EEG‑Förderung endet?" — https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/photovoltaik-was-tun-mit-der-ue20anlage-wenn-die-eegfoerderung-endet-50846 — abgerufen 2026-06-14 — sekundär (starke Verbraucherinstitution), hoch.
