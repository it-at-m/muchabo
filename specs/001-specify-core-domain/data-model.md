# Data Model: Datenbankschema-Ist-Zustand von muchabo

**Stand**: 2026-11-17

**Feature**: `specs/001-specify-core-domain`

**Bezug**: [spec.md](spec.md), [plan.md](plan.md), [source-analysis.md](source-analysis.md)

## 1. Belegbasis und Umfang

Dieses Dokument beschreibt das aus den vorhandenen Migrationen V001–V003 und Java-Entitäten rekonstruierbare Anwendungsschema. Ob diese Migrationen in einer konkreten Datenbank angewandt wurden und ob dort manuelle Abweichungen existieren, wurde nicht durch eine Live-Abfrage untersucht.

Projektbezogene Basispfade für die folgenden Quellenangaben:

- **J**: `admin-backend/src/main/java/de/muenchen/oss/refarch/backend/`.
- **M**: `admin-backend/src/main/resources/db/migration/`.

Schemaquelle sind M `schema/V001__TheEntity_schema.sql`, `schema/V002__Project_Init.sql` und `schema/V003__Add_MCP.sql`. Entitätsmapping und Bean Validation ergänzen diese Datenbankregeln. M `testdata/R__Testdata.sql` verändert ausschließlich Beispieldaten.

**Inventar**: 7 Anwendungstabellen, 24 gespeicherte Spalten, 7 Primärschlüssel, 2 zusätzliche Unique-Constraints und 5 Fremdschlüssel. Nur `mcp_tool.description` ist nullable; die übrigen 23 Spalten sind ausdrücklich oder durch den Primärschlüssel nicht-null. Sechs Tabellen bilden die Kerndomäne; `the_entity` ist isolierter Beispielbestand.

Tabellennamen werden in SQL ohne Schemapräfix verwendet. Das tatsächliche PostgreSQL-Schema hängt von der Ausführungsumgebung und ihrem `search_path` ab. Eine durch Flyway verwaltete Schema-Historientabelle ist kein von diesen Migrationen definiertes fachliches Objekt und gehört nicht zu den sieben Anwendungstabellen.

## 2. Gemeinsame Identität und Notation

J `common/BaseEntity.java:17–31` ist eine `@MappedSuperclass` mit `UUID id`, `@Id` und `@GeneratedValue(strategy = GenerationType.UUID)`. Alle sieben Entitäten erben diese Kennung; eine eigene Tabelle für `BaseEntity` existiert nicht. Das Mapping-Attribut `length = 36` ändert den SQL-Typ `UUID` nicht zu einer Textspalte. `serialVersionUID` ist kein gespeichertes Fachattribut.

Alle Tabellen besitzen `id UUID` als Primärschlüssel. Die sechs Kerntabellen haben zusätzlich den SQL-Default `gen_random_uuid()`; `the_entity.id` hat keinen SQL-Default. Reguläre Anlage über das Java-Objektmodell generiert daher auch Beispielkennungen, direkte SQL-Anlage benötigt dort eine bereitgestellte Kennung.

„Keiner“ in einer Default-Spalte bedeutet, dass die Migration keinen SQL-Default vorgibt. Defaults greifen bei ausgelassener Spalte oder Verwendung des Defaults, nicht bei explizitem `NULL`. Bei nullable Spalten ohne Default kann Auslassung zu `NULL` führen; bei Pflichtspalten muss der erforderliche Wert bereitgestellt werden.

## 3. Tabellen und Spalten

### 3.1 `chatbot` — Benannter Chatbot

**Quellen**: J `chatbot/Chatbot.java:18–23`; M `schema/V002__Project_Init.sql:6–9`.

| Spalte | SQL-Typ | NULL erlaubt | SQL-Default | Datenbankregel | Java-Attribut / Typ |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Nein | `gen_random_uuid()` | Primärschlüssel | `id: UUID`, geerbt |
| `name` | `VARCHAR(100)` | Nein | Keiner | Höchstens 100 Zeichen, nicht eindeutig | `name: String` |

Gleichnamige Chatbots, leere Namen und reine Leerzeichen sind durch diese Regeln nicht ausgeschlossen. Ein Chatbot kann ohne Konfiguration existieren.

### 3.2 `model` — Wiederverwendbares Modell

**Quellen**: J `model/Model.java:18–23`; M `schema/V002__Project_Init.sql:1–4`.

| Spalte | SQL-Typ | NULL erlaubt | SQL-Default | Datenbankregel | Java-Attribut / Typ |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Nein | `gen_random_uuid()` | Primärschlüssel | `id: UUID`, geerbt |
| `model_name` | `VARCHAR(100)` | Nein | Keiner | `UNIQUE`, höchstens 100 Zeichen | `modelName: String` |

Es gibt keine Mindesttextlänge und keine fachlich definierte Namensnormalisierung. Ein leerer Modellname ist möglich, aber kein zweiter identischer leerer Name. Das konkrete Vergleichsverhalten einer Datenbankinstanz hängt zusätzlich von ihrer hier nicht explizit festgelegten Kollation ab.

### 3.3 `chatbot_config` — Chatbot-Konfiguration

**Quellen**: J `chatbot/ChatbotConfig.java:29–61`; M `schema/V002__Project_Init.sql:11–23`.

| Spalte | SQL-Typ | NULL erlaubt | SQL-Default | Datenbankregel | Java-Attribut / Typ |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Nein | `gen_random_uuid()` | Primärschlüssel | `id: UUID`, geerbt |
| `chatbot_id` | `UUID` | Nein | Keiner | FK auf `chatbot.id` | `chatbot: Chatbot` |
| `model_id` | `UUID` | Nein | Keiner | FK auf `model.id` | `model: Model` |
| `prompt` | `TEXT` | Nein | Keiner | Keine zusätzliche Längen-/Inhaltsprüfung | `prompt: String` |
| `temperature` | `DOUBLE PRECISION` | Nein | Keiner | Kein Bereichs-`CHECK` | `temperature: Double` |
| `version` | `VARCHAR(20)` | Nein | Keiner | Höchstens 20 Zeichen, nicht eindeutig | `version: String` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Nein | `CURRENT_TIMESTAMP` | Keine SQL-Unveränderlichkeitsregel | `createdAt: OffsetDateTime` |

Chatbot und Modell sind jeweils `@ManyToOne(fetch = LAZY, optional = false)` mit nicht-null Join-Spalte. Zusätzlich enthält das Java-Objekt `List<ChatbotTool> chatbotTools`: inverse `@OneToMany(mappedBy = "chatbotConfig", cascade = ALL, orphanRemoval = true)`-Beziehung, initial leer. Diese Sammlung ist keine zusätzliche gespeicherte Spalte; eine gespeicherte Reihenfolge ist nicht definiert.

`createdAt` verwendet `@CreationTimestamp` und `updatable = false`. Hibernate erzeugt den Zeitpunkt bei Anlage und nimmt ihn nicht in reguläre Update-Zuweisungen auf. SQL besitzt einen eigenen Insert-Default, aber keinen Trigger oder Constraint zur Unveränderlichkeit. PostgreSQL speichert einen Zeitpunkt, nicht den ursprünglichen Zeitzonennamen oder Offset als zusätzliche Information. `CURRENT_TIMESTAMP` bezieht sich auf den Beginn der aktuellen Transaktion, nicht zwingend auf einen neuen Zeitpunkt pro Zeile.

Die Versionsbezeichnung ist kein `@Version`-Locking-Attribut. Weder Format, automatische Reihenfolge, Freigabe-/Aktuellstatus noch Eindeutigkeit je Chatbot ist festgelegt. Für Prompt und Temperatur existiert keine allgemeine Unveränderlichkeitsregel.

### 3.4 `mcp_server` — Werkzeuganbieter

**Quellen**: J `mcp/McpServer.java:18–26`; M `schema/V003__Add_MCP.sql:1–5`.

| Spalte | SQL-Typ | NULL erlaubt | SQL-Default | Datenbankregel | Java-Attribut / Typ |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Nein | `gen_random_uuid()` | Primärschlüssel | `id: UUID`, geerbt |
| `name` | `VARCHAR(100)` | Nein | Keiner | Höchstens 100 Zeichen, nicht eindeutig | `name: String` |
| `url` | `VARCHAR(255)` | Nein | Keiner | Höchstens 255 Zeichen, nicht eindeutig | `url: String` |

Es gibt keine Adressformat- oder Erreichbarkeitsprüfung. Vorhandene, aber leere Texte sind auf Schemaebene zulässig. Ein Server kann ohne Werkzeuge existieren.

### 3.5 `mcp_tool` — Werkzeug eines Servers

**Quellen**: J `mcp/McpTool.java:21–35`; M `schema/V003__Add_MCP.sql:7–14`.

| Spalte | SQL-Typ | NULL erlaubt | SQL-Default | Datenbankregel | Java-Attribut / Typ |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Nein | `gen_random_uuid()` | Primärschlüssel | `id: UUID`, geerbt |
| `mcp_server_id` | `UUID` | Nein | Keiner | FK auf `mcp_server.id`, Löschkaskade | `mcpServer: McpServer` |
| `name` | `VARCHAR(100)` | Nein | Keiner | Höchstens 100 Zeichen, nicht eindeutig | `name: String` |
| `description` | `TEXT` | Ja | Keiner | Optionale Beschreibung | `description: String` |

Die Serverreferenz ist `@ManyToOne(fetch = LAZY, optional = false)` mit nicht-null Join-Spalte. Werkzeugnamen sind auch innerhalb desselben Servers nicht eindeutig. Eine fehlende und eine leere Beschreibung sind beide zulässig, aber verschiedene Werte. Ein Werkzeug kann ohne Konfigurationszuordnung existieren.

### 3.6 `chatbot_tool` — Konfigurationsbezogene Werkzeugzuordnung

**Quellen**: J `mcp/ChatbotTool.java:18–42`; M `schema/V003__Add_MCP.sql:16–25`.

| Spalte | SQL-Typ | NULL erlaubt | SQL-Default | Datenbankregel | Java-Attribut / Typ |
| --- | --- | --- | --- | --- | --- |
| `id` | `UUID` | Nein | `gen_random_uuid()` | Primärschlüssel | `id: UUID`, geerbt |
| `chatbot_config_id` | `UUID` | Nein | Keiner | FK auf `chatbot_config.id`, Löschkaskade; Teil des Unique-Paares | `chatbotConfig: ChatbotConfig` |
| `mcp_tool_id` | `UUID` | Nein | Keiner | FK auf `mcp_tool.id`, Löschkaskade; Teil des Unique-Paares | `mcpTool: McpTool` |
| `is_active` | `BOOLEAN` | Nein | `TRUE` | Aktivstatus, nicht Teil des Unique-Paares | `isActive: boolean`, initial `true` |

Beide Objektverweise sind `@ManyToOne(fetch = LAZY, optional = false)` mit nicht-null Join-Spalte. Die Entität benennt ihre Tabelle mit `@Table` ausdrücklich und definiert denselben Unique-Constraint wie die Migration: `uq_chatbot_config_tool(chatbot_config_id, mcp_tool_id)`.

Die Zuordnung besitzt eine eigene Kennung; das Paar ist ein zusätzlicher eindeutiger Schlüssel, nicht ihr Primärschlüssel. Ein anderer Aktivstatus erlaubt keinen zweiten Datensatz desselben Paares.

### 3.7 `the_entity` — Isolierte Beispielentität

**Quellen**: J `theentity/TheEntity.java:24–33`; M `schema/V001__TheEntity_schema.sql:1–5`.

| Spalte | SQL-Typ | NULL erlaubt | SQL-Default | Datenbankregel | Java-Attribut / Typ |
| --- | --- | --- | --- | --- | --- |
| `text_attribute` | `VARCHAR(8)` | Nein | Keiner | Höchstens 8 Zeichen, keine SQL-Mindestlänge | `textAttribute: String` |
| `id` | `UUID` | Nein | Keiner | Primärschlüssel | `id: UUID`, geerbt |

Die Spaltenreihenfolge entspricht V001. Entität und Request-DTO verwenden zusätzlich `@NotNull` und `@Size(min = 2, max = 8)`; der Controller prüft Eingaben beim Erstellen und Ändern mit `@Valid`. SQL allein erlaubt dagegen auch einen leeren Text oder einen Text unter zwei Zeichen. Reine Leerzeichen werden innerhalb der jeweiligen Längengrenzen nicht ausgeschlossen.

Es gibt keine Beziehungen zur Kerndomäne. Die SQL-Generierung einer Kennung per Default fehlt hier; das geerbte Java-Mapping generiert Kennungen bei regulärer Anlage.

## 4. Schlüssel, Beziehungen und ER-Diagramm

### 4.1 Primär- und zusätzliche Eindeutigkeitsschlüssel

| Tabelle | Primärschlüssel | Zusätzlicher Unique-Constraint |
| --- | --- | --- |
| `chatbot` | `id` | Keiner |
| `model` | `id` | `UNIQUE(model_name)`; kein expliziter Constraint-Name vorgegeben |
| `chatbot_config` | `id` | Keiner, insbesondere nicht `(chatbot_id, version)` |
| `mcp_server` | `id` | Keiner |
| `mcp_tool` | `id` | Keiner, insbesondere nicht `(mcp_server_id, name)` |
| `chatbot_tool` | `id` | `uq_chatbot_config_tool(chatbot_config_id, mcp_tool_id)` |
| `the_entity` | `id` | Keiner |

Die Migrationen geben keine eigenen Namen für die Primärschlüssel vor. Automatisch vergebene Constraint-Namen sind hier kein aus einer Instanz überprüfter Befund.

### 4.2 Fremdschlüssel und Kardinalitäten

Alle fünf Referenzen sind verpflichtend. Je abhängiger Zeile wird genau ein bestehendes Ziel referenziert; jedes Ziel kann 0..n abhängige Zeilen haben. SQL definiert keine explizite Update-Aktion oder Deferrability. PostgreSQL-Standard ist `ON UPDATE NO ACTION` und `NOT DEFERRABLE`.

| Constraint | Abhängige Spalte | Ziel | Ziel → abhängige Objekte | ON DELETE | ON UPDATE |
| --- | --- | --- | --- | --- | --- |
| `fk_chatbot_config_chatbot` | `chatbot_config.chatbot_id` | `chatbot.id` | 1 → 0..n Konfigurationen | `NO ACTION` (Standard) | `NO ACTION` (Standard) |
| `fk_chatbot_config_model` | `chatbot_config.model_id` | `model.id` | 1 → 0..n Konfigurationen | `NO ACTION` (Standard) | `NO ACTION` (Standard) |
| `fk_mcp_tool_server` | `mcp_tool.mcp_server_id` | `mcp_server.id` | 1 → 0..n Werkzeuge | `CASCADE` | `NO ACTION` (Standard) |
| `fk_chatbot_tool_config` | `chatbot_tool.chatbot_config_id` | `chatbot_config.id` | 1 → 0..n Zuordnungen | `CASCADE` | `NO ACTION` (Standard) |
| `fk_chatbot_tool_tool` | `chatbot_tool.mcp_tool_id` | `mcp_tool.id` | 1 → 0..n Zuordnungen | `CASCADE` | `NO ACTION` (Standard) |

Zwischen Konfiguration und Werkzeug besteht eine auf beiden Seiten optionale n:m-Beziehung über `chatbot_tool`. Ein direkter Werkzeugbezug zu `chatbot` ist nicht vorhanden.

### 4.3 ER-Diagramm

```mermaid
erDiagram
    chatbot ||--o{ chatbot_config : besitzt
    model ||--o{ chatbot_config : konfiguriert
    mcp_server ||--o{ mcp_tool : bietet
    chatbot_config ||--o{ chatbot_tool : umfasst
    mcp_tool ||--o{ chatbot_tool : zugeordnet

    chatbot {
        UUID id PK
        VARCHAR_100 name
    }
    model {
        UUID id PK
        VARCHAR_100 model_name UK
    }
    chatbot_config {
        UUID id PK
        UUID chatbot_id FK
        UUID model_id FK
        TEXT prompt
        DOUBLE_PRECISION temperature
        VARCHAR_20 version
        TIMESTAMPTZ created_at
    }
    mcp_server {
        UUID id PK
        VARCHAR_100 name
        VARCHAR_255 url
    }
    mcp_tool {
        UUID id PK
        UUID mcp_server_id FK
        VARCHAR_100 name
        TEXT description
    }
    chatbot_tool {
        UUID id PK
        UUID chatbot_config_id FK
        UUID mcp_tool_id FK
        BOOLEAN is_active
    }
    the_entity {
        VARCHAR_8 text_attribute
        UUID id PK
    }
```

Die Typnamen im Diagramm sind verkürzt; exakte SQL-Typen, Nullbarkeit, Defaults, Löschaktionen und der zusammengesetzte Unique-Constraint stehen in den Tabellen.

## 5. Löschfolgen und Zustandsänderungen

| Änderung | Datenbankfolge | Objektseitige Ergänzung |
| --- | --- | --- |
| Chatbot oder Modell mit bestehenden Konfigurationsverweisen löschen | Löschung wird durch den jeweiligen FK verhindert. Ohne Verweise besteht dieses Löschhindernis nicht. | Keine Löschkaskade vom Chatbot oder Modell zu Konfigurationen definiert. |
| Konfiguration löschen | Ihre Werkzeugzuordnungen entfallen; Chatbot, Modell, Werkzeuge und Server bleiben bestehen. | Konfigurationssammlung besitzt `cascade = ALL`. |
| Werkzeug löschen | Alle darauf bezogenen Zuordnungen entfallen; Konfigurationen und Server bleiben bestehen. | Die beschriebene Löschkaskade stammt aus SQL. |
| Server löschen | Seine Werkzeuge und deren Zuordnungen entfallen; Konfigurationen und Chatbots bleiben bestehen. | Keine entsprechende Werkzeug-Sammlung auf `McpServer`; die Wirkung stammt aus SQL. |
| Zuordnung löschen | Nur die Zuordnung entfällt; Werkzeug und Konfiguration bleiben bestehen. | Entfernen aus der verwalteten Konfigurationssammlung löst bei Synchronisierung über `orphanRemoval = true` ebenfalls das Entfernen aus. |
| Beispieldatensatz löschen | Nur der Beispieldatensatz entfällt. | Keine Domänenbeziehungen vorhanden. |

**Aktivstatus**: `chatbot_tool.is_active` kann zwischen `TRUE` und `FALSE` wechseln. Deaktivieren entfernt keinen Datensatz und lässt die Paar-Eindeutigkeit bestehen. Weitere Statuswerte oder fachliche Statusübergänge sind nicht definiert.

**Konfiguration**: Prompt, Temperatur, Version und Referenzen besitzen keine allgemeine SQL-Unveränderlichkeitsregel. Gleiche Versionsbezeichnungen können mehrfach vorkommen; ein Auswahlverfahren für eine aktuelle Konfiguration ist nicht definiert. Der Erstellungszeitpunkt ist nur im regulären Objekt-Update vor Änderung geschützt.

**Referenzen**: Neuzuordnungen müssen auf bestehende Ziele zeigen und bei Werkzeugzuordnungen weiterhin das Unique-Paar einhalten. `ON UPDATE NO ACTION` betrifft Änderungen referenzierter Schlüssel; es verbietet keine gültige Neuzuordnung einer Fremdschlüsselspalte.

Diese Regeln beschreiben zulässige Datenzustände. Für die sechs Kernentitäten sind keine eigenen Verwaltungs-Repositories, Services oder Controller belegt; eine tatsächliche Werkzeugausführung folgt nicht aus dem Aktivstatus.

## 6. Indizes und weitere Schemaobjekte

- Keine Schema-Migration enthält ein explizites `CREATE INDEX`.
- PostgreSQL erzeugt automatisch eindeutige Indizes für sieben PK und zwei zusätzliche Unique-Constraints. Damit sind neun solche Indizes für ein aus diesen Migrationen neu aufgebautes Anwendungsschema ableitbar; ein Live-Indexinventar wurde nicht ermittelt.
- Fremdschlüssel erzeugen keine automatischen zusätzlichen Indizes auf den referenzierenden Spalten. Der Unique-Index auf `(chatbot_config_id, mcp_tool_id)` besitzt `chatbot_config_id` als führende Spalte; das ist kein separat definierter Index auf `mcp_tool_id`.
- Die Migrationen definieren keine zusätzlichen `CHECK`-Constraints, Views, Sequenzen, Trigger, fachlichen Funktionen oder expliziten Erweiterungsinstallationen. `gen_random_uuid()` und `CURRENT_TIMESTAMP` sind verwendete PostgreSQL-Funktion beziehungsweise Zeitausdruck.

## 7. Validierungsebenen und Bestandsgrenzen

| Regel | SQL-Absicherung | JPA / Bean Validation / Eingabe | Abgrenzung |
| --- | --- | --- | --- |
| Identität | UUID-PK überall; SQL-UUID-Default nur auf sechs Kerntabellen | Geerbte UUID-Generierung überall | Direkte SQL-Anlage eines Beispieldatensatzes benötigt eine Kennung. |
| Pflicht und Textlänge | `NOT NULL`, `VARCHAR`-Grenzen; Beschreibung nullable | Entsprechende Spalten-/Join-Metadaten | Metadaten allein sind keine frühe Eingabevalidierung. |
| Leere Texte / Namen | Keine Mindestlänge oder Nicht-leer-Regel für Kerntexte | Keine zusätzlichen Bean-Validation-Regeln der Kernentitäten | Leere Texte und reine Leerzeichen sind nicht ausgeschlossen. |
| Eindeutigkeit | Modellname und Konfiguration/Werkzeug-Paar | Entsprechende Unique-Metadaten | Keine weitere Namens-, Adress- oder Versionseindeutigkeit. |
| Serveradresse | Pflichttext bis 255 Zeichen | Längen-/Nullbarkeitsmetadaten | Keine Format-/Erreichbarkeitsprüfung. |
| Temperatur | Pflichtwert, kein Default oder Bereichs-`CHECK` | `Double` mit nicht-null Spaltenmetadaten | Kein Bereich wie 0–2 und keine fachliche Sonderwertregel. |
| Version | Pflichttext bis 20 Zeichen | `String`, kein `@Version` | Kein Format, keine Versionsfolge oder Aktuell-Auswahl. |
| Erstellungszeitpunkt | Pflichtzeitpunkt mit Insert-Default | `@CreationTimestamp`, `updatable = false` | SQL selbst erzwingt keine Unveränderlichkeit. |
| Aktivstatus | `BOOLEAN NOT NULL DEFAULT TRUE` | `boolean`, initial `true` | Status nur je Zuordnung; Default ersetzt kein explizites SQL-`NULL`. |
| Beispieltext | Pflichttext bis 8 Zeichen | Zusätzlich `@Size(min = 2, max = 8)`, `@NotNull`, Eingaben mit `@Valid` | Die Mindestlänge 2 ist kein SQL-Constraint. |
| Zuordnung aus Sammlung entfernen | Keine Collection-Semantik in SQL | `orphanRemoval = true` | Setzt Verarbeitung des verwalteten Objektmodells voraus. |

Prompt und Werkzeugbeschreibung besitzen keine fachlich festgelegte Maximallänge oder Inhaltsprüfung. Die Beispieltextvalidierung zählt Java-Zeichenkettenlänge; SQL-Längenprüfungen können bei Unicode-Sonderzeichen anders ausfallen. Eine einheitliche Zählung sichtbarer Zeichen oder Namensnormalisierung ist aus diesen Regeln nicht ableitbar.

## 8. Migrationsfolge und Konfiguration

| Datei relativ zu M | Art | Wirkung |
| --- | --- | --- |
| `schema/V001__TheEntity_schema.sql` | Versioniert, V001 | `the_entity`: 2 Spalten, 1 PK. |
| `schema/V002__Project_Init.sql` | Versioniert, V002 | `model`, `chatbot`, `chatbot_config`: zusammen 11 Spalten, 3 PK, 1 Unique-Constraint, 2 FK ohne Löschkaskade. |
| `schema/V003__Add_MCP.sql` | Versioniert, V003 | `mcp_server`, `mcp_tool`, `chatbot_tool`: zusammen 11 Spalten, 3 PK, 1 Unique-Constraint, 3 FK mit Löschkaskade. |
| `testdata/R__Testdata.sql` | Wiederholbar | Leert `the_entity` und setzt fünf Texte mit festen UUIDs: Alpha, Bravo, Charlie, Delta, Echo. Keine Schemaänderung oder Kernstammdaten. |

`admin-backend/src/main/resources/application.yml:12–19` konfiguriert `spring.jpa.hibernate.ddl-auto: validate`, `open-in-view: false` und nur `classpath:db/migration/schema`. `application-local.yml:16–19` ergänzt `classpath:db/migration/testdata`; die Flyway-Maven-Konfiguration in `admin-backend/pom.xml:75–79` enthält ebenfalls beide Orte.

Wird die wiederholbare Migration ausgeführt, ersetzt sie vorhandene Beispieldaten. Das ist ein konfigurationsabhängiger Testdatenvorgang, kein fachlicher Löschprozess. Wiederholbar bedeutet nicht unabhängig von Flyways Änderungsprüfung bei jedem Start erneut ausgeführt.

Lokal definiert `stack/docker-compose.yml:14–21` PostgreSQL 18.4 (Alpine), Datenbank `postgres` und Port 5432. Damit ist keine Version einer produktiven Instanz festgestellt.

## 9. Zuordnung zur fachlichen Spezifikation

| Anforderungen | Beleg im Datenmodell |
| --- | --- |
| FR-001–002 | Kennungen, Chatbot-/Modellname, Modellnamen-Unique. |
| FR-003–005 | Konfigurationsspalten, Pflichtreferenzen, Zeitstempelverhalten und freie Versionsbezeichnung. |
| FR-006–007 | Server-/Werkzeugattribute und verpflichtender Serverbezug. |
| FR-008–009 | Aktivstatus, eigene Zuordnungsidentität und Unique-Paar. |
| FR-010–012 | Fünf FK mit Löschaktionen, Pflichtbezug und objektseitiges Orphan Removal. |
| FR-013–014 | Grenzen der Kernvalidierung und zusätzlich anwendungsseitige Beispiel-Mindestlänge. |
| FR-015–016 | Rollen, Beispielverwaltung, Nichtgefunden-Verhalten und Pagination sind Anwendungsfunktionen, keine Schemaobjekte; ihre Belege stehen in [source-analysis.md](source-analysis.md). |
| FR-017 | Vollständigkeitsinventar mit 7 Tabellen, 24 Spalten, 5 Beziehungen und allen belegten Schlüssel-/Validierungs-/Löschregeln. |

Gespräche, Nachrichten, Nutzendenprofile, Wissensbestände, Mandanten, Abrechnung und Veröffentlichungs-/Freigabestatus sind in den untersuchten Migrationen nicht als eigene fachliche Datenobjekte definiert. Die bestehende Paketabweichung zur Projektverfassung ist im [Plan](plan.md) eingeordnet.
