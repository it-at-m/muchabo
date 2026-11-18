# Quellenanalyse: muchabo-Kerndomäne

**Stand**: 2026-11-17

**Spezifikation**: [spec.md](spec.md)

## 1. Quellenumfang und Pfadzuordnung

Der angefragte Pfad `admin-backend/src/main/java/de/muenchen/oss/muchabo/` existiert im Checkout nicht. Die tatsächlich vorhandenen Java-Entitäten liegen unter `admin-backend/src/main/java/de/muenchen/oss/refarch/backend/`. Der angefragte Migrationspfad `admin-backend/src/main/resources/db/migration/` ist vorhanden.

Für die nachfolgenden Belegangaben gelten:

- **J**: `admin-backend/src/main/java/de/muenchen/oss/refarch/backend/`.
- **M**: `admin-backend/src/main/resources/db/migration/`.

Untersucht wurden alle sieben `@Entity`-Klassen, die gemeinsame Basisklasse, alle Repositories und sämtliche vier SQL-Dateien unter diesen Quellen. Request-DTO, Controller, Service und Berechtigungskonstanten der Beispielentität wurden ergänzend zur Eingabevalidierung und Bedienbarkeit gelesen. Die Migrationsorte wurden anhand der Anwendungskonfiguration geprüft.

Das Ergebnis ist aus Quellen rekonstruierter Bestand. Es wurden keine Migrationen ausgeführt und keine laufende Datenbank ausgelesen. Infrastrukturvalidierungen für Sicherheits- oder OpenAPI-Konfiguration sind keine fachlichen Regeln der Kerndomäne.

## 2. Vollständiges Entitäten- und Attributinventar

Alle sieben Entitäten erben `id` von J `common/BaseEntity.java:17–31`: `@MappedSuperclass`, `UUID`, `@Id` und `@GeneratedValue(strategy = GenerationType.UUID)`. Es gibt keine eigene Basistabelle. Die Annotation `length = 36` ist keine abweichende SQL-Textspalte; alle Kennungen sind in den Migrationen vom Typ `UUID`.

| Entität / Tabelle | Java-Quelle relativ zu J | Alle gespeicherten Spalten einschließlich Kennung | Migrationsbeleg relativ zu M | Anforderungen |
| --- | --- | --- | --- | --- |
| `Chatbot` / `chatbot` | `chatbot/Chatbot.java:18–23` | `id`, `name` | `schema/V002__Project_Init.sql:6–9` | FR-001–002, FR-005, FR-010 |
| `Model` / `model` | `model/Model.java:18–23` | `id`, `model_name` | `schema/V002__Project_Init.sql:1–4` | FR-001–002, FR-010 |
| `ChatbotConfig` / `chatbot_config` | `chatbot/ChatbotConfig.java:29–61` | `id`, `chatbot_id`, `model_id`, `prompt`, `temperature`, `version`, `created_at` | `schema/V002__Project_Init.sql:11–23` | FR-001, FR-003–005, FR-010–012 |
| `McpServer` / `mcp_server` | `mcp/McpServer.java:18–26` | `id`, `name`, `url` | `schema/V003__Add_MCP.sql:1–5` | FR-001, FR-006, FR-011 |
| `McpTool` / `mcp_tool` | `mcp/McpTool.java:21–35` | `id`, `mcp_server_id`, `name`, `description` | `schema/V003__Add_MCP.sql:7–14` | FR-001, FR-007, FR-011–012 |
| `ChatbotTool` / `chatbot_tool` | `mcp/ChatbotTool.java:18–42` | `id`, `chatbot_config_id`, `mcp_tool_id`, `is_active` | `schema/V003__Add_MCP.sql:16–25` | FR-001, FR-008–009, FR-011–012 |
| `TheEntity` / `the_entity` | `theentity/TheEntity.java:24–33` | `text_attribute`, `id` | `schema/V001__TheEntity_schema.sql:1–5` | FR-001, FR-014–016 |

Insgesamt: **7 Tabellen und 24 gespeicherte Spalten** (2 + 2 + 7 + 3 + 4 + 4 + 2). Hinzu kommt die inverse Objektsammlung `ChatbotConfig.chatbotTools`, die eine Beziehung abbildet, keine zusätzliche gespeicherte Spalte. `serialVersionUID` dient der Java-Serialisierung und ist kein persistiertes Fachattribut.

Java-Namen mit abweichenden Spaltennamen: `modelName` → `model_name`, `createdAt` → `created_at`, `isActive` → `is_active`, `textAttribute` → `text_attribute`. Die fünf Objektverweise werden über die in der Tabelle benannten Fremdschlüsselspalten gespeichert.

## 3. Migrationsfolge und aktive Orte

| Datei relativ zu M | Wirkung |
| --- | --- |
| `schema/V001__TheEntity_schema.sql` | Beispielentität mit UUID-Primärschlüssel und `VARCHAR(8) NOT NULL`-Text; keine SQL-Mindestlängenregel und kein SQL-Default für die Kennung. |
| `schema/V002__Project_Init.sql` | Modell, Chatbot und Konfiguration; UUID-Defaults `gen_random_uuid()`; Modellname eindeutig; zwei Pflicht-Fremdschlüssel ohne Löschkaskade; Konfiguration mit Pflicht-Prompt, Pflicht-Temperatur, Pflicht-Version und Zeitstempel-Default. |
| `schema/V003__Add_MCP.sql` | Server, Werkzeug und Zuordnung; UUID-Defaults; drei Pflicht-Fremdschlüssel mit Löschkaskade; Aktivstatus-Default `TRUE`; zusammengesetzte Eindeutigkeit der Zuordnung. |
| `testdata/R__Testdata.sql` | Leert `the_entity` und setzt fünf Beispieldatensätze mit festen Kennungen und den Texten Alpha, Bravo, Charlie, Delta, Echo. Keine Schemaänderung, keine Chatbot- oder MCP-Stammdaten. |

`admin-backend/src/main/resources/application.yml:12–19` konfiguriert `ddl-auto: validate` und ausschließlich `classpath:db/migration/schema`. `application-local.yml:16–19` ergänzt `classpath:db/migration/testdata`. Die Testdatenoperation ist keine fachliche Löschregel. Eine erfolgreiche Schema-Validierung oder tatsächlich angewandte Migrationen werden damit nicht attestiert.

## 4. Beziehungen und Lebenszyklus

| Fremdschlüssel | Java-Beleg relativ zu J | SQL-Beleg | Datenbankwirkung beim Löschen des Ziels |
| --- | --- | --- | --- |
| `fk_chatbot_config_chatbot`: `chatbot_config.chatbot_id` → `chatbot.id` | `chatbot/ChatbotConfig.java:33–37` | M V002:21 | Standard `NO ACTION`: Bestehende Konfigurationen verhindern die Chatbotlöschung. |
| `fk_chatbot_config_model`: `chatbot_config.model_id` → `model.id` | `chatbot/ChatbotConfig.java:39–43` | M V002:22 | Standard `NO ACTION`: Bestehende Konfigurationen verhindern die Modelllöschung. |
| `fk_mcp_tool_server`: `mcp_tool.mcp_server_id` → `mcp_server.id` | `mcp/McpTool.java:25–29` | M V003:13 | `ON DELETE CASCADE`: Serverlöschung entfernt seine Werkzeuge und mittelbar deren Zuordnungen. |
| `fk_chatbot_tool_config`: `chatbot_tool.chatbot_config_id` → `chatbot_config.id` | `mcp/ChatbotTool.java:38–42` | M V003:22 | `ON DELETE CASCADE`: Konfigurationslöschung entfernt ihre Zuordnungen, nicht die Werkzeuge. |
| `fk_chatbot_tool_tool`: `chatbot_tool.mcp_tool_id` → `mcp_tool.id` | `mcp/ChatbotTool.java:29–33` | M V003:23 | `ON DELETE CASCADE`: Werkzeuglöschung entfernt sämtliche darauf bezogenen Zuordnungen, nicht die Konfigurationen. |

Alle fünf Beziehungen sind auf der abhängigen Seite `@ManyToOne(fetch = LAZY, optional = false)` mit nicht-null Join-Spalte und SQL-`NOT NULL`; je abhängiger Zeile ist genau ein bestehendes Ziel erforderlich. Auf der Zielseite folgt jeweils 0..n. Ein serverübergreifendes Verbot von Werkzeugzuordnungen oder ein direkter Werkzeugbezug am Chatbot ist nicht vorhanden.

J `chatbot/ChatbotConfig.java:58–61` definiert ergänzend `@OneToMany(mappedBy = "chatbotConfig", cascade = ALL, orphanRemoval = true)`. Beim Verarbeiten der verwalteten Sammlung werden Zuordnungen mitpersistiert und beim Entfernen aus der Sammlung gelöscht. Das ist objektspezifisches Verhalten, kein SQL-Constraint. Weder die beiden `ManyToOne`-Referenzen der Konfiguration noch der Server besitzen eine entsprechende allgemeine Löschkaskade im Objektmodell.

M V003:24 und J `mcp/ChatbotTool.java:19` definieren identisch `uq_chatbot_config_tool(chatbot_config_id, mcp_tool_id)`. Die Aktivität ist kein Bestandteil dieses Unique-Schlüssels. Die n:m-Beziehung Konfiguration/Werkzeug wird ausschließlich über diese Zuordnungsentität vermittelt. Es gibt keine gespeicherte Reihenfolge der Zuordnungssammlung.

## 5. Validierungsebenen und Bestandsgrenzen

| Gegenstand | Datenbank-/Entitätsbeleg | Fachliche Ableitung und Grenze |
| --- | --- | --- |
| Kennung | UUID-PK auf allen Tabellen; SQL-Default nur in V002/V003; geerbte Java-Generierung auf allen Entitäten | Automatische Kennung bei regulärer Anlage. Direkte SQL-Anlage der Beispielentität benötigt eine bereitgestellte Kennung; keine pauschale SQL-Generierung für alle Tabellen. |
| Kernnamen | `VARCHAR(100) NOT NULL` und entsprechende `@Column`-Metadaten | Vorhanden, höchstens 100 Zeichen; `NOT NULL` bedeutet nicht nicht-leer. Keine `@NotBlank`- oder Mindestlängenregel. |
| Modellname | SQL-`UNIQUE` und `unique = true` | Eindeutig; keine explizite Namensnormalisierung oder zusätzliche fachliche Gleichsetzung verschiedener Schreibweisen. Konkretes Kollationsverhalten einer Instanz wurde nicht bestimmt. |
| Adresse | `VARCHAR(255) NOT NULL` | Vorhandener Text bis 255 Zeichen, nicht eindeutig; keine URL-Format- oder Erreichbarkeitsprüfung. |
| Prompt / Beschreibung | `TEXT NOT NULL` / nullable `TEXT` | Prompt vorhanden, Beschreibung optional. Keine fachliche Maximallänge oder Inhaltsprüfung. |
| Temperatur | `DOUBLE PRECISION NOT NULL`, Java `Double` | Pflichtwert ohne Default und ohne Bereichs-`CHECK`. Ein verbreiteter Bereich wie 0–2 darf nicht hinzuerfunden werden; Sonderwerte sind nicht als fachliche Garantie abgeleitet. |
| Version | `VARCHAR(20) NOT NULL`, Java `String` | Maximal 20 Zeichen; keine Kombinationseindeutigkeit je Chatbot, Formatprüfung, Versionsfolge, Freigabe oder aktuelle Auswahl. Kein `@Version`-Locking-Attribut. |
| Erstellungszeitpunkt | SQL `TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP`; J `ChatbotConfig.java:54–56` mit `@CreationTimestamp`, `updatable = false` | Automatisch bei Anlage, bei regulären Objekt-Updates erhalten. SQL enthält keinen Unveränderlichkeits-Trigger; direkte Änderungen sind damit nicht generell ausgeschlossen. PostgreSQL bewahrt einen Zeitpunkt, nicht die ursprüngliche Zeitzonenbezeichnung. |
| Aktivstatus | SQL `BOOLEAN NOT NULL DEFAULT TRUE`; Java `boolean isActive = true` | Neue Zuordnung standardmäßig aktiv; Status nur je Zuordnung. Defaults ersetzen kein explizites SQL-`NULL`. |
| Zuordnungspaar | SQL/JPA Unique-Constraint auf Konfiguration/Werkzeug | Höchstens eine Zuordnung je Paar, auch bei anderem Aktivstatus. |
| Beispieltext | SQL `VARCHAR(8) NOT NULL`; J `TheEntity.java:32–33` und `TheEntityRequestDTO.java:6` mit `@NotNull`, `@Size(min = 2, max = 8)` | Mindestlänge 2 nur in Bean Validation; SQL selbst erlaubt kürzere vorhandene Texte. Leerzeichen sind nicht ausgeschlossen. Controller aktiviert Eingabeprüfung mit `@Valid` bei Erstellen/Ändern. |

Keine der sechs Kernentitäten enthält zusätzliche Bean-Validation-Annotationen für die beschriebenen Text-/Bereichsprüfungen. SQL enthält keine zusätzlichen `CHECK`-Regeln. JPA-Spaltenmetadaten allein belegen keine frühe Eingabevalidierung einer noch nicht vorhandenen Kernverwaltung.

Die Beispieltextvalidierung zählt Java-Zeichenkettenlänge; die SQL-Längenprüfung kann bei Unicode-Sonderzeichen anders ausfallen. Eine universell einheitliche Zählung sichtbarer Zeichen ist deshalb nicht als Fachregel abgeleitet. Grenzfallbeispiele der Spezifikation verwenden gewöhnliche Buchstaben.

## 6. Repositories, Verwaltungsfunktionen und Rollen

- J `theentity/TheEntityRepository.java:8–9` ist das einzige Repository im untersuchten Java-Quellstand. Es kombiniert `CrudRepository<TheEntity, UUID>` und `PagingAndSortingRepository<TheEntity, UUID>` ohne eigene Suchmethoden.
- J `theentity/TheEntityService.java:23–59` belegt Einzel-/Seitenlesen, Erstellen, Ändern des Textes unter Beibehaltung der Kennung und Löschen. Lesen/Ändern verwenden eine vorherige Suche mit `NotFoundException`; Löschen ruft direkt `deleteById` auf. Die gleiche explizite Nichtgefunden-Regel beim Löschen ist nicht definiert.
- J `theentity/TheEntityController.java:54–60` verwendet Seite 0 und Größe 10 als Defaults; der Service verwendet `PageRequest.of`, das eine nicht negative Seitennummer und positive Größe verlangt. Feste Ergebnisreihenfolge und fachliche maximale Größe sind nicht definiert.
- J `theentity/TheEntityController.java:69,81` prüft Requests beim Erstellen/Ändern mit `@Valid`. J `theentity/dto/TheEntityRequestDTO.java:6` enthält die Text-Pflicht- und Längenregeln.
- J `security/Authorities.java:10–15` erlaubt `reader` oder `writer` das Lesen; Erstellen, Ändern und Löschen erfordern `writer`. Die Servicemethoden nutzen diese aktiven Konstanten. Auskommentierte permissions-basierte Alternativen sind keine Bestandsregeln.
- Für die sechs Kernentitäten existieren keine eigenen Repositories, Services oder Controller im untersuchten Quellstand. Verwaltungsbedienbarkeit, fachliche Such-/Auswahlregeln, Werkzeugausführung und Rechtevergabe sind daraus nicht belegbar.

## 7. Verfassung und Spec-Kit-Kontext

Die aktuelle `.specify/memory/constitution.md` wurde gelesen. Version 1.0.0 nennt bereits `admin-backend/` und `admin-frontend/` und fordert interne/öffentliche Trennung, gesicherte Administration sowie versionierte Migrationen. Ihr Java-Basispaket `de.muenchen.oss.muchabo` weicht weiterhin vom vorhandenen `de.muenchen.oss.refarch.backend` ab. Diese Abweichung wird dokumentiert, ohne daraus eine neue Architekturentscheidung abzuleiten. Die bereits modifizierte Verfassung wurde nicht bearbeitet.

Weder die Vorprüfung noch die abschließende Post-Hook-Prüfung fand eine `.specify/extensions.yml`; damit sind keine Before-/After-Specify-Hooks registriert. `.specify/init-options.json` verwendet `feature_numbering: sequential`; `specs/` war bei dieser Ausführung leer. Deshalb wurde genau ein Feature `specs/001-specify-core-domain` angelegt und `.specify/feature.json` darauf aktualisiert. Der bestehende Git-Branch ist `chore/try_speckit_for_database` und bestimmt den Feature-Pfad nicht.

Die aktive Vorlage wurde mit `resolve-template.sh spec-template --json` erfolgreich über den Spec-Kit-Auflösungsstapel ermittelt. Es sind keine Projekt-Overrides, Presets oder Extensions vorhanden; verwendet wurde die Core-Vorlage `.specify/templates/spec-template.md`. Ihre Abschnittsreihenfolge ist in `spec.md` erhalten.

## 8. Anforderungs- und Abnahmezuordnung

| Anforderungen | Akzeptanzbeleg in spec.md |
| --- | --- |
| FR-001–004 | Story 1, Szenarien 1 und 3–5; Story 2, Szenario 1; Story 4, Szenario 1; Attribut- und Validierungsmatrix. |
| FR-005 | Story 1, Szenarien 2 und 4; Randfälle zu Mehrfachkonfigurationen und optionalen Zuordnungen. |
| FR-006–007 | Story 2, Szenarien 1, 4–5; Attribut-/Validierungsmatrix. |
| FR-008–009 | Story 2, Szenarien 1–3; Randfall inaktive Doppelzuordnung. |
| FR-010–011 | Story 3, Szenarien 1–6; Beziehungstabelle und Serverlöschungsrandfall. |
| FR-012–013 | Story 1, Szenario 3; Story 2, Szenario 5; vollständige Validierungsmatrix und Randfälle. |
| FR-014–016 | Story 4, Szenarien 1–5; dokumentierte Unterschiede der Absicherungsebenen. |
| FR-017 | Vollständigkeitsvergleich dieses Inventars (7 Entitäten, 24 Spalten, 5 direkte Beziehungen plus inverse Sammlung) mit den Entitäts-/Beziehungstabellen und Validierungen. |

Die technische Qualitätsprüfung der Spezifikation bestätigt ihre Belegtreue und Abdeckung. Sie ist kein Ersatz für ausgeführte Produkt-Akzeptanztests oder die noch vorzunehmende fachliche Abnahme durch zwei verantwortliche Personen.
