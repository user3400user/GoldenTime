# MaStR-Gesamtdatenexport als Basis für ein wöchentliches Lead-Produkt (neue gewerbliche PV ohne Speicher)
_Run: 2026-06-14 (N0) · Nachtrag N+1: 2026-06-14 (deepen) · Mode: deep-research · Slug: mastr-pv-leads_

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

**Nachtrag N+1 (deepen, 2026-06-14):** Eigene Live‑Messungen schließen mehrere Lücken — die Web‑JSON ist
**offener als in N0 angenommen** (in Stichprobe kein Deep‑Paging‑Cap, voll serverseitig filterbar, exponiert Betreibernummer
+ Datumsfelder) und damit ein **valider Weg für gezielte Teilabzüge**, nicht nur Einzel‑Lookups; der **2026er
Post‑EEG‑Jahrgang misst 63.807 Solar‑Einheiten** (2027: 76.827), danach wächst die Kohorte steil; aktueller
Bestand **6,20 Mio. Solar / 2,58 Mio. Speicher** [20]. Die Empfehlung (Bulk‑Export als Backbone) bleibt, aber
**neu begründet** — Details unter „Nachtrag N+1 — empirische Validierung".

## Empfehlung (Kurzfassung — Details s. „Empfehlung" unten)
**Pipeline auf den Gesamtdatenexport bauen** (wöchentlicher Pull des täglichen ZIP → lokale SQLite/Postgres
via open‑mastr → SQL‑Filter), **nicht** auf die Web‑JSON‑Abfrage. Begründung verdichtet: nur der Export
liefert den **vollständigen Betreibergraph** für den Speicher‑Anywhere‑Check (SQ4) als einen joinbaren,
versionierten und Woche‑für‑Woche diff‑baren Gesamtbestand. Die Web‑JSON ist *nicht* feldarm (ihr
Listen‑Endpunkt exponiert laut OpenAPI‑Schema Betreibernummer und alle Datumsfelder [9]), aber sie ist eine
inoffizielle Frontend‑Schnittstelle ohne historische Stichtage, mit undokumentierten Limits und einem seit
2022 eingefrorenen Referenz‑Tooling — für eine globale Betreiber‑Aggregation der falsche Hebel.

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
  des Einzelabfrage‑Wegs, **eingefroren seit 17.07.2022** [9]. Wichtig zur Einordnung: dieses `Entry`‑Schema
  ist **nicht feldarm** — es exponiert u. a. `AnlagenbetreiberMaStRNummer`, `AnlagenbetreiberPersonenArt`
  (natürliche vs. juristische Person — nützlich für „gewerblich"), `EinheitRegistrierungsdatum`,
  `InbetriebnahmeDatum`, `EegInbetriebnahmeDatum`, `DatumLetzteAktualisierung` [9]. (answers SQ2,
  confidence: high)

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
| Erstregistrierung der Einheit | `Registrierungsdatum` (EinheitenSolar) | date, Pflicht | soll bei Korrektur stabil bleiben (Soll‑Konzept, per EEG‑Meldedatum‑Analogie [15]) |
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
**Entscheidung (in N+1 bestätigt, aber neu begründet): Gesamtdatenexport als Backbone.** Die Web‑JSON ist
nach empirischer Prüfung (s. Nachtrag N+1) **kein bloßer Einzelabfrage‑Weg**, sondern für gezielte, gefilterte
Teilabzüge voll tauglich — sie bleibt aber das schlechtere *Backbone* für dieses Produkt.
Begründung direkt aus SQ1–SQ5:

1. **Speicher‑Anywhere‑Check (SQ4) verlangt den vollen Betreibergraph.** „Hat dieser Betreiber *irgendwo*
   einen Speicher?" ist eine **globale Aggregation über alle Einheiten und Einheitenarten** (Speicher sind
   eigene Objekte) je `AnlagenbetreiberMastrNummer`. Zwar zeigt auch die Web‑JSON je Einheit die
   Betreibernummer [9] — aber eine paginierte Einzelabfrage müsste den Gesamtbestand de facto rekonstruieren
   oder pro Lead/Woche zahlreiche gefilterte Abfragen (je Betreiber, je Einheitenart) gegen ein Endpoint mit
   undokumentierten Limits fahren. Der Export liefert den Graphen einmalig und lokal joinbar [3][9].
2. **Frische‑Logik (SQ3+SQ5) braucht beide Datumsfelder im selben Korpus.** „Neu" = junges
   `Registrierungsdatum` **und** junges `Inbetriebnahmedatum` (gegen Nachregistrierung). Beide Felder
   (+ `EegInbetriebnahmedatum`) liefern *beide* Wege [3][9]; der Export gibt sie aber im selben joinbaren
   Datensatz zusammen mit EEG‑Anlage und Speicher‑Objekt — entscheidend, weil die Frische‑ *und* die
   Speicher‑Logik dieselbe Verknüpfung brauchen [3][15][18].
3. **Stabilität, ToS, Wartung (SQ1+SQ2).** Der Export ist ein offiziell für „versierte IT‑Nutzer"
   bereitgestelltes, **versioniertes, XSD‑schematisiertes** Produkt mit gepflegtem Tool (open‑mastr) [1][3][5].
   Die Web‑JSON ist eine inoffizielle Frontend‑Schnittstelle (Referenz‑Spec seit 2022 ruhend [9]); eigene
   Messung zeigt zwar **keine** Drosselung/Deckelung in Stichproben (18+ Anfragen) und **kein**
   Deep‑Paging‑Limit [20] — offiziell zugesichert ist das aber nicht, und wöchentliche ~600‑Seiten‑Vollabzüge
   eines Frontend‑Endpunkts sind ToS‑seitig riskanter als der dafür vorgesehene Bulk‑Kanal.
4. **Reproduzierbarkeit & Dedupe.** Tägliche/Stichtag‑Exporte erlauben **Woche‑gegen‑Woche‑Diffs** auf
   `Registrierungsdatum` (und `DatumLetzteAktualisierung`) gegen einen lokalen Snapshot — sauber auditierbar
   und gegen frühere Läufe deduplizierbar; die Web‑JSON ist eine live‑bewegte Sicht ohne offizielle
   historische Stände [1][2].

**Konkrete Pipeline (Vorschlag):** wöchentlich das Tages‑ZIP ziehen → mit open‑mastr die Tabellen
`solar` + `storage` + `locations` + `market actors` (nicht nur Solar!) in lokale DB → SQL‑Filter:
PV‑Einheit `In Betrieb`, gewerblicher Betreiber, Ziel‑`Bundesland`/PLZ, `Registrierungsdatum` in letzter
Woche **und** `Inbetriebnahmedatum` jung → **ausschließen**, wenn derselbe `AnlagenbetreiberMastrNummer`
*oder* dieselbe `LokationMaStRNummer` einen Speicher führt bzw. `SpeicherAmGleichenOrt = true`. „ohne
Speicher" stets als „kein Speicher gemeldet" labeln (Unsicherheit ~9 %). **Post‑EEG‑Slice** als zweites
Produkt: Filter `EegInbetriebnahmedatum`‑Jahr ∈ {2006, 2007} ohne gemeldeten Speicher = Retrofit‑/
Optimierungs‑Leads mit Trigger „Förderende 2026/2027".

## Nachtrag N+1 — empirische Validierung (deepen, 2026-06-14)
_Offene Punkte aus N0 teils durch eigene Messungen an Live‑Daten geschlossen. Reproduzierbare Abfragen:
`notes.md`. Messquelle: offizieller MaStR‑Web‑JSON‑Endpunkt [20] + Filtermetadaten [21]._

**G1 · Web‑JSON ist offen und leistungsfähiger als in N0 angenommen — Annahme korrigiert.** Der Endpunkt
`GetErweiterteOeffentlicheEinheitStromerzeugung` liefert ohne Login/Cookies sauberes JSON `{Data, Total, …}`,
**ohne Deep‑Paging‑Cap** (gesamter Bestand seitenweise erreichbar, `pageSize ≥ 10.000`, in 18+ Anfragen keine
Drosselung) und exponiert je Einheit u. a. `AnlagenbetreiberMaStRNummer`, alle Datumsfelder, `Bundesland`,
Geo‑Koordinaten; serverseitig **filterbar** nach `Energieträger`, `Betriebs-Status`, Inbetriebnahmedatum
(Datumsbereich via `~gt~/~lt~`), `MaStR-Nr. der Lokation`, `MaStR-Nr. der Speichereinheit` [20][21]. ⇒ Die
Web‑JSON ist ein **valider Weg für gezielte, gefilterte Teilabzüge** — nicht nur Einzel‑Lookups. (confidence:
high für das Gemessene; offiziell zugesicherte Limits weiterhin keine, Vollabzug‑Verträglichkeit ungetestet)

**G5 · Aktuelle gemessene Bestandszahlen (Stand 2026-06-14)** [20]:
- öffentliche **Stromerzeugungseinheiten gesamt: 8.954.450**
- **Solar: 6.204.541** (davon „In Betrieb" 6.058.494)
- **Speicher** (Energieträger „Speicher", id 2496)**: 2.580.425** (davon „In Betrieb" 2.544.621)
  ⇒ Der Speicher‑Bestand ist riesig (~42 % der Solar‑Einheiten); „ohne Speicher" trennt gegen eine
  Mengenklasse von ~2,5 Mio. Einheiten. (confidence: high)

**G4 · Post‑EEG‑Kohorte — primär gemessen** (Solar‑Einheiten nach Inbetriebnahmejahr) [20]:

| Inbetriebnahmejahr | Solar‑Einheiten | EEG‑Förderende (Jahr + 20) | Hinweis |
| :-- | --: | :-- | :-- |
| 2000 | 9.308 | 2020 | Sanity: längst ausgefördert |
| 2001 | 21.940 | 2021 | |
| 2005 | 67.185 | 2025 | |
| **2006** | **63.807** (63.095 in Betrieb) | **2026** | **aktueller Jahrgang** |
| **2007** | **76.827** (76.456 in Betrieb) | **2027** | |
| 2008 | 115.345 | 2028 | |
| 2009 | 182.219 | 2029 | Boom beginnt |
| 2010 | 258.052 | 2030 | |
| 2011 | 260.128 | 2031 | |
| 2012 | 173.939 | 2032 | |

⇒ Der **2026er Post‑EEG‑Jahrgang ≈ 63.807 Solar‑Einheiten** (~99 % noch in Betrieb). _Methodenhinweis:_ die
Tabelle filtert auf das **Einheiten‑`Inbetriebnahmedatum`**; rechtlich richtet sich das Förderende nach
`EegInbetriebnahmedatum` (s. SQ3). Beide fallen i. d. R. zusammen, daher ist 63.807 eine **exakte Messung des
Inbetriebnahme‑Jahrgangs 2006, aber nur ein naher Proxy** für den genauen EEG‑Kohortenstand — er deckt sich
gut mit der unabhängig genannten Größe „über 66.000 Anlagen" 2026 [19]. **Strategisch wichtiger:** die Kohorte
**wächst steil** (2029–2032: 180k–260k/Jahr), der adressierbare Post‑EEG‑Markt vervielfacht sich bis Anfang
der 2030er. (confidence: high für die Jahrgangszählung; „noch auf EEG‑Tarif / Eigenverbrauch" ist nicht entschieden)

**G3 · Co‑Lokationsquote (PV+Speicher an einer SEL) — weiterhin nicht gemessen.** Die einzige Quelle für
arbiträres SQL (Datasette‑Mirror `ds.marktstammdatenregister.dev`) war im Messfenster **ausgefallen** (TCP
offen, keine L7‑Antwort; aus 6 Vantage‑Points inkl. Firecrawl/Tavily bestätigt). Der Live‑Endpunkt kann
„Solar **mit** co‑lokalem Speicher" nicht als Filter ausdrücken. Reproduzierbare Methode steht bereit
(Datasette‑SQL bzw. lokaler Join über `LokationMaStRNummer` / `SpeicherAmGleichenOrt` auf einem
Stichtag‑Export; exakte Queries in `notes.md`). Kontext: Speicher‑Bestand ~2,54 Mio.; Literatur ~75 % der
**neuen** Wohn‑PV mit Speicher, ~9 % Speicher unter-/spät registriert [13]. ⇒ Betreiber‑Nummer‑Rollup bleibt
der robuste Pfad; „ohne Speicher" = „kein Speicher gemeldet". (confidence: n/a — offen)

**G2 · Lokation & Nummernkonzept — offiziell belegt.** Gesetzliche Grundlage (§ 14 MaStRV): der Netzbetreiber
fasst Einheiten zu technischen Lokationen zusammen (für die er datenverantwortlich ist) [10] — eine
Stromerzeugungslokation ist demnach „jede
Konfiguration aus einer oder mehreren **elektrisch verbundenen**
Stromerzeugungseinheiten, die elektrische Energie über **einen oder mehrere Netzanschlusspunkte** … einspeisen
kann" [23]. MaStR‑Nummernpräfixe (Nummernkonzept): **SEE** Stromerzeugungseinheit, **SEL**
Stromerzeugungslokation, **SSE** Stromspeichereinheit, **ABR** Anlagenbetreiber, **SNB** Stromnetzbetreiber,
**EEG/KWK** Anlagen; Aufbau = 3 Buchstaben + Versionsziffer („9") + 10 Ziffern + Prüfziffer [22]. (In der
öffentlichen Übersicht erscheinen Batteriespeicher als Energieträger „Speicher" (2496); ob eine Speichereinheit
rechtlich in dieselbe SEL fällt, sagt § 14 nicht ausdrücklich — die Einheiten tragen aber je eine
`LokationMaStRNummer` [3].) (confidence: high für Definition/Präfixe)

## Uncertainties & contradictions
- **Exakte Einheitenzahl**: in N+1 gemessen — **8.954.450** öffentliche Stromerzeugungseinheiten (Solar
  6.204.541, Speicher 2.580.425), Stand 2026-06-14 [20]. Unkomprimierte Exportgröße weiterhin nicht offiziell
  beziffert (nur ~2,96 GB komprimiert) [1][2].
- **Vollständigkeit der co‑lokalen PV↔Speicher‑Zuordnung** (weiterhin offen): die exakte SEL‑Co‑Lokationsquote
  konnte in N+1 **nicht** gemessen werden (SQL‑Mirror Datasette ausgefallen; Live‑Endpunkt kann „Solar mit
  Speicher" nicht filtern — s. Nachtrag G3). Die Literatur matched bewusst **statistisch** (PV‑seitiges Flag),
  nicht per Record‑Join [13]. Der **Betreiber‑Nummer‑Weg** ist davon unberührt und bleibt der robuste Pfad.
  (Gegenposition s. u.)
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

## Open questions / next steps
**In N+1 geschlossen:** Web‑JSON‑Caps (kein Deep‑Paging‑Limit, keine Drosselung in Stichprobe) [20]; aktuelle
Bestandszahlen [20]; Post‑EEG‑Kohortengröße 2026/2027 (primär gemessen) [20]; Lokations‑Definition +
Nummernkonzept [22][23]. **Offen geblieben:**
- **Co‑Lokationsquote** (PV+Speicher an einer SEL): messen, sobald der Datasette‑Mirror wieder erreichbar ist,
  oder per lokalem Join auf einem Stichtag‑Export (Queries liegen in `notes.md`).
- **Gewerblich** sauber operationalisieren: `AnlagenbetreiberPersonenArt` (juristisch vs. natürlich) als
  Diskriminator [9]; im Export gegen `Marktakteure` verifizieren, ggf. mit Leistungsschwelle kombinieren.
- **Vollabzug‑Verträglichkeit** der Web‑JSON (ToS/Drosselung bei wöchentlich ~600 Seiten) bleibt ungetestet.

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

_Nachtrag N+1 (deepen, 2026-06-14):_
20. Eigene Live‑Messung am MaStR‑Web‑JSON‑Endpunkt `GetErweiterteOeffentlicheEinheitStromerzeugung` — https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetErweiterteOeffentlicheEinheitStromerzeugung — gemessen 2026-06-14 (exakte Abfragen in `notes.md`) — primär (Live‑Daten der BNetzA), hoch.
21. MaStR‑Filtermetadaten `GetFilterColumnsErweiterteOeffentlicheEinheitStromerzeugung` (Spalten/Kataloge, u. a. Energieträger „Speicher"=2496) — https://www.marktstammdatenregister.de/MaStR/Einheit/EinheitJson/GetFilterColumnsErweiterteOeffentlicheEinheitStromerzeugung — abgerufen 2026-06-14 — primär, hoch.
22. MaStR‑Nummernkonzept (Bundesnetzagentur; Kopie via Clearingstelle EEG|KWKG, Stand 2017) — https://www.clearingstelle-eeg-kwkg.de/sites/default/files/Nummernkonzept_MaStR_170301-1.pdf — abgerufen 2026-06-14 — primär (offizielles Konzept), hoch.
23. § 14 MaStRV „Daten zu technischen Lokationen" (Gesetzestext; kanonisch auch gesetze-im-internet.de/mastrv) — https://www.buzer.de/14_MaStRV.htm — abgerufen 2026-06-14 — primär (Recht), hoch.
