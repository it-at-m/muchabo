# Implementation Plan: Dokumentation des Datenbankschema-Ist-Zustands

**Branch**: `chore/try_speckit_for_database` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-specify-core-domain/spec.md`; Nutzerauftrag: „Erstelle auf Basis des vorhandenen Backend-Codes nur die Dokumentation (plan.md und data-model.md) für den Ist-Zustand unseres Datenbankschemas. Generiere keinen neuen Code.“

**Status**: Dokumentationsphasen 0 und 1 abgeschlossen.

**Feature directory**: `specs/001-specify-core-domain`. Das Plan-Setup liefert diesen Feature-Identifier im Feld `BRANCH`; der tatsächliche Git-Branch ist oben separat angegeben.

## Summary

Dieses Dokument beschreibt Vorgehen, technischen Kontext und Abgleich der bestehenden Datenbankstruktur. [data-model.md](data-model.md) dokumentiert den aus Flyway V001–V003 rekonstruierbaren Stand: **7 Anwendungstabellen, 24 Spalten, 7 Primärschlüssel, 2 zusätzliche Unique-Constraints und 5 Fremdschlüssel**.

Die SQL-Migrationen bilden die Belegbasis für das Schema; die Java-Entitäten ergänzen das Objektmapping und dessen Validierungen. Grundlage sind die vorhandenen Quellen unter `admin-backend/` und die fachliche Spezifikation samt [source-analysis.md](source-analysis.md). Der Begriff Ist-Zustand bezeichnet hier den versionierten Quellstand, nicht das Ergebnis einer Abfrage einer laufenden Datenbank.

Die Phase-0-Erkenntnisse und die Dokumentationsprüfung sind in diesem Plan integriert, entsprechend dem gewünschten Ergebnisumfang von zwei Dokumenten.

## Technical Context

**Language/Version**: Java 25 laut `admin-backend/pom.xml:40–45`; PostgreSQL-SQL in den Migrationen.

**Primary Dependencies**: Spring Boot 4.1.1 (POM-Parent), Spring Data JPA/Hibernate, Jakarta Persistence/Validation, Flyway mit PostgreSQL-Unterstützung sowie PostgreSQL-JDBC-Treiber. Lombok unterstützt die Entitätsklassen. Nicht einzeln versionierte Bibliotheken werden über Spring Boots Dependency-Management aufgelöst; ihre exakten transitiven Versionen sind für die Bestandsbeschreibung der Spalten und Constraints nicht erforderlich.

**Storage**: PostgreSQL. `stack/docker-compose.yml:14–21` definiert lokal `postgres:18.4-alpine`, Datenbank `postgres` und Port 5432. Migrationen verwenden unqualifizierte Tabellennamen; das tatsächlich verwendete PostgreSQL-Schema ergibt sich aus der Ausführungsumgebung und deren `search_path`.

**Testing**: Vorhandene Spring-Boot-Testabhängigkeiten, JUnit/Testcontainers mit PostgreSQL und ArchUnit laut POM. Für dieses Dokumentationsergebnis wird ein statischer Vergleich von Quellen, Spezifikation und Datenmodell durchgeführt. Dieser Vergleich attestiert keine ausgeführten Produkt- oder Integrationstests.

**Target Platform**: Serverseitiges Spring-Boot-Backend; `admin-backend/Dockerfile` verwendet UBI10/OpenJDK-25-Runtime. Der lokale Backend-Port ist 8086 laut `application-local.yml`.

**Project Type**: Administrativer Web-Service innerhalb des muchabo-Projekts. Das Schema der Chatbot-/MCP-Kerndomäne und der isolierten Beispielentität liegt im Java-Admin-Backend.

**Performance Goals**: In der untersuchten Belegbasis sind keine quantifizierten Datenbanklast- oder Laufzeitziele definiert. Für den Dokumentationsauftrag gelten die Vollständigkeits-, Prüfbarkeits- und Verständlichkeitsziele SC-001–005 der Spezifikation.

**Constraints**: Dokumentation des bestehenden Schemas ohne neue Implementierung. Flyway definiert die Schemaänderungen; Hibernate ist mit `ddl-auto: validate` konfiguriert. SQL-Constraints, JPA-Mapping, Bean Validation und Verwaltungsverhalten werden getrennt ausgewiesen.

**Scale/Scope**: 6 Kernentitäten plus `TheEntity`, 24 gespeicherte Spalten, 5 direkte Beziehungen, 3 versionierte Schema-Migrationen und 1 wiederholbare Testdatenmigration. Produktive Datenvolumina, tatsächlich angewandte Migrationen und installierte Serverversionen sind aus dem Quellstand nicht feststellbar und keine Voraussetzung für diese Bestandsdokumentation.

## Constitution Check

Grundlage: `.specify/memory/constitution.md`, Version 1.0.0 vom 2026-11-17. Bewertet wird die Konformität des Dokumentationsauftrags; eine vollständige Laufzeitprüfung des Produkts ist damit nicht verbunden.

| Prinzip / Gate | Prüfung vor Phase 0 | Erneute Bewertung nach Phase 1 |
| --- | --- | --- |
| I — Admin/Public-Trennung und Gateway | Die Verfassung nennt `admin-backend/`, `admin-frontend/` und die öffentliche Webkomponente. Der Umfang betrifft das vorhandene Admin-Schema. | Keine Architekturentscheidung erforderlich; die Dokumentation ordnet die Quellen dem Admin-Backend zu. Gateway-Verhalten ist durch Schemaquellen nicht verifizierbar. |
| II — Java, Spring Boot, PostgreSQL und Flyway | Technologiestack und versionierte Migrationen sind belegt. Das Java-Basispaket weicht von der Verfassung ab. | Schema und Entitätsmapping sind getrennt dokumentiert; die bestehende Paketabweichung ist in Complexity Tracking begründet. |
| III — Frontend-Standards | Keine Frontend-Umsetzung im Dokumentationsumfang. | Für dieses Ergebnis kein Frontend-Implementierungsgate einschlägig. |
| IV — Sicherheit und Authentifizierung | Die Beispielverwaltung besitzt belegte Lese-/Schreibrollen; eine Rechtezuordnung für die Kernentitäten ist aus dem Schema nicht ableitbar. | Rechte werden nicht als Datenbank-Constraint ausgegeben. Keine zusätzliche Schnittstellen- oder Berechtigungsentscheidung erforderlich. |
| V — Qualitätsgates und Tests | Die POM konfiguriert die Backend-Qualitätswerkzeuge; diese prüfen Produktcode. | Dokumentationsqualität durch Quellenabgleich und Konsistenzprüfung beurteilt. Produkt-Build- und Security-Gates werden dadurch nicht als bestanden attestiert. |
| Governance | Die bestehende Paketabweichung wird rekonstruiert. Die Verfassung verlangt einen Abgleich vor einer Architekturabweichung bei Implementierung. | Dokumentation ist zulässig; keine neue, unbegründete Architekturabweichung. Eine spätere strukturelle Umsetzung benötigt den vorgesehenen Verfassungsabgleich. |

**Ergebnis vor und nach Phase 1**: Dokumentationsgate erfüllt. Alle für den Umfang erforderlichen Angaben sind aus lokalen Quellen geklärt; fehlende Live-Instanzdaten sind als Beleggrenze bezeichnet, nicht als offene Designentscheidung.

## Project Structure

### Documentation (this feature)

```text
specs/001-specify-core-domain/
├── spec.md                      # Vorhandene fachliche Spezifikation
├── source-analysis.md           # Vorhandene Quellenbelege
├── checklists/requirements.md   # Vorhandene Spezifikationsprüfung
├── plan.md                      # Dokumentationsplan mit Phase-0-Erkenntnissen
└── data-model.md                # Schema-Ist-Zustand
```

### Source Code (repository root)
```text
admin-backend/
├── pom.xml
├── Dockerfile
└── src/
    ├── main/
    │   ├── java/de/muenchen/oss/refarch/backend/
    │   │   ├── common/BaseEntity.java
    │   │   ├── chatbot/         # Chatbot, ChatbotConfig
    │   │   ├── model/           # Model
    │   │   ├── mcp/             # McpServer, McpTool, ChatbotTool
    │   │   └── theentity/       # Beispielentität und Beispielverwaltung
    │   └── resources/
    │       ├── application.yml
    │       ├── application-local.yml
    │       └── db/migration/
    │           ├── schema/     # V001, V002, V003
    │           └── testdata/   # R__Testdata.sql
    └── test/java/de/muenchen/oss/refarch/backend/
stack/docker-compose.yml        # Lokales PostgreSQL-Image
```

**Structure Decision**: Die dokumentierten Pfade entsprechen dem vorhandenen Checkout. Das aktive Feature wird über `.specify/feature.json` aufgelöst, unabhängig vom Git-Branchnamen. `setup-plan.sh --json` hat die aktive Plan-Vorlage bereitgestellt. Die technische Bestandsanalyse ist in die beiden angeforderten Dokumente integriert.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Bestehendes Java-Basispaket `de.muenchen.oss.refarch.backend` statt des in der Verfassung genannten `de.muenchen.oss.muchabo`. | Der Ist-Zustand muss die tatsächlich vorhandenen Entitäten und ihre Belegpfade korrekt benennen. Dies begründet die Beschreibung der Abweichung, keine Freigabe einer neuen Architektur. | Eine Dokumentation unter dem nicht vorhandenen Paket wäre unbelegt; eine Paketumbenennung wäre eine Implementierungsänderung. |

## Phase 0 — Research und geklärte Bestandsfragen

Die folgenden Erkenntnisse erfüllen die Quellenklärung für diesen Dokumentationsauftrag. Es sind keine neuen Technologie- oder Integrationsentscheidungen erforderlich.

### R-001 — Schemaquelle

- **Decision**: V001–V003 unter `admin-backend/src/main/resources/db/migration/schema/` bestimmen den rekonstruierbaren Schemastand.
- **Rationale**: SQL definiert Spaltentypen, Nullbarkeit, Defaults und Constraints ausdrücklich; `ddl-auto: validate` beschreibt die konfigurierte Rolle von Hibernate als Schema-Prüfer.
- **Alternatives considered**: Ausschließlich Entitätsannotationen würden SQL-Defaults und Datenbank-Löschkaskaden übersehen. Live-Instanzzustand wäre ohne Abfrage unbelegt.

### R-002 — Validierungsebenen und Defaults

- **Decision**: SQL-Regeln, JPA-Verhalten und Eingabevalidierung separat darstellen.
- **Rationale**: Alle Java-Entitäten erben UUID-Generierung, aber nur die sechs Kerntabellen besitzen einen SQL-UUID-Default. Beispieltext-Mindestlänge 2 ist Bean Validation, kein SQL-Constraint. `created_at` hat einen SQL-Insert-Default und objektseitigen Änderungsschutz, aber keinen Unveränderlichkeits-Trigger. Default-Werte ersetzen kein explizites `NULL`.
- **Alternatives considered**: Eine gemeinsame Regelauflistung ohne Ebenenkennzeichnung würde weitergehende Datenbankgarantien behaupten.

### R-003 — Beziehungen und Zustandsänderungen

- **Decision**: Zwei FK-Beziehungen mit standardmäßigem `NO ACTION` und drei FK-Beziehungen mit `ON DELETE CASCADE` dokumentieren; Collection-Orphan-Removal zusätzlich als Objektverhalten benennen.
- **Rationale**: Chatbot- und Modelllöschung sind bei Konfigurationsverweisen verhindert. Konfigurations-, Werkzeug- und Serverlöschungen entfernen abhängige Zuordnungen. `ChatbotConfig.chatbotTools` enthält `cascade = ALL` und `orphanRemoval = true`. Der Aktivstatus gehört zur Zuordnung, nicht zum Werkzeug insgesamt.
- **Alternatives considered**: Eine pauschale Löschkaskade oder eine globale Werkzeugaktivierung wäre fachlich und technisch falsch.

### R-004 — Testdaten und Indexbestand

- **Decision**: `R__Testdata.sql` als konfigurationsabhängigen Datenbestandseingriff behandeln; implizite Constraint-Indizes von expliziten Indizes unterscheiden.
- **Rationale**: Standardmäßig wird nur der Schemaordner geladen; lokal und in der Flyway-Maven-Konfiguration zusätzlich Testdaten. Die wiederholbare Migration leert ausschließlich die Beispielentität. SQL enthält kein `CREATE INDEX`; PostgreSQL erzeugt Indizes für sieben PK und zwei Unique-Constraints, aber nicht automatisch für alle FK-Spalten.
- **Alternatives considered**: Die fünf Beispieltexte als Kernstammdaten, das Leeren als Geschäftsregel oder alle Fremdschlüssel als separat indiziert auszugeben wäre unbelegt.

## Phase 1 — Datenmodell und Dokumentationsprüfung

### Ergebnis

[data-model.md](data-model.md) enthält sämtliche Tabellen und Spalten mit SQL-Typ, Nullbarkeit, Default und Java-Zuordnung, ein ER-Diagramm, alle Schlüssel und Beziehungen sowie Löschregeln, Zustandsänderungen und Validierungsgrenzen. Die Migrationen und ihr Konfigurationsbezug werden nachvollziehbar beschrieben.

Die bereits belegte Beispielverwaltung ist Anwendungskontext; ihre Rollen und Pagination sind keine SQL-Constraints. Für die sechs Kernentitäten sind keine eigenen Verwaltungs-Repositories, Services oder Controller belegt. Der Anforderungsbezug verweist deshalb bei FR-015–016 auf die vorhandene Quellenanalyse.

### Ausgeführter statischer Abgleich

| Prüfung | Erwarteter Befund | Ergebnis |
| --- | --- | --- |
| Entitäten und Tabellen | 7 Entitäten ↔ 7 Tabellen; Basisklasse ohne Tabelle | Vollständig zugeordnet. |
| Spalten | 2 + 2 + 7 + 3 + 4 + 4 + 2 = 24 | Jede Spalte mit Typ, Nullbarkeit, Default und Java-Attribut beschrieben. |
| Schlüssel und Löschaktionen | 7 PK, 2 zusätzliche Unique-Constraints, 5 FK; davon 2 ohne und 3 mit Löschkaskade | Vollständig dokumentiert. |
| Mapping und Validierung | Pflichtreferenzen, inverse Sammlung, Orphan Removal, Zeitstempel, Aktivstatus und Beispieltextprüfung | Von SQL-Absicherung getrennt ausgewiesen. |
| Spezifikationsabgleich | FR-001–014 und FR-017 als Schema-/Mappingbezug; FR-015–016 als Beispielverwaltungsverhalten | Anforderungszuordnung enthalten. |
| Migrationen und Defaults | V001–V003 plus R-Testdaten; fehlender SQL-UUID-Default für Beispielkennung | Bestandsunterschiede ausdrücklich benannt. |

Dieser Abgleich prüft Dokumentationsvollständigkeit und Belegtreue. Er enthält keine Aussage über bestandene Produkt-Akzeptanzszenarien, einen ausgeführten Build oder den tatsächlich angewandten Migrationsstand einer Umgebung.

Die Whitespace-Prüfung beider Ergebnisdateien war erfolgreich. `check-prerequisites.sh --json --require-spec` findet das aktive Feature, seine Spezifikation, den ausgefüllten Plan und `data-model.md` erfolgreich.

### Extension-Hooks

Bei der Vorprüfung und der abschließenden Post-Hook-Prüfung existiert `.specify/extensions.yml` nicht. Damit sind keine `before_plan`- oder `after_plan`-Hooks registriert.
