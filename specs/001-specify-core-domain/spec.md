# Feature Specification: Fachliche Bestandsbeschreibung der muchabo-Kerndomäne

**Feature Branch**: `chore/try_speckit_for_database`

**Created**: 2026-11-17

**Status**: Rückwirkende Bestandsbeschreibung; Qualitätsprüfung abgeschlossen, bereit für Planung

**Input**: User description: "Analysiere unser bestehendes Datenmodell in admin-backend/src/main/java/de/muenchen/oss/muchabo/ (Entities, Repositories) sowie die Flyway-Migrationen in admin-backend/src/main/resources/db/migration/. Leite daraus rückwirkend die fachliche Spezifikation (spec.md) für unsere Kerndomäne ab, inklusive aller Entitäten, Beziehungen und Validierungsregeln."

## User Scenarios & Testing *(mandatory)*

Die Szenarien beschreiben fachlich zulässige Bestandsdaten und deren Änderungen. Sie belegen keine bereits bedienbare Chatbotverwaltung. Für die Kernentitäten sind Datenregeln vorhanden; konkrete Verwaltungsfunktionen sind nur für die isolierte Beispielentität belegt. Die technische Herleitung steht in [source-analysis.md](source-analysis.md).

### User Story 1 - Chatbots und Konfigurationen fachlich nachvollziehen (Priority: P1)

Als fachlich verantwortliche Person möchte ich Chatbots, ihre Konfigurationen und die zugehörigen Modelle eindeutig auseinanderhalten und die hinterlegten Einstellungen verstehen.

**Why this priority**: Chatbot, Modell und Konfiguration bilden die Grundlage für die fachliche Beschreibung des Chatbotverhaltens.

**Independent Test**: Ein Chatbot, ein Modell und zwei Konfigurationen genügen zum Prüfen von Identität, Pflichtangaben, Mehrfachkonfigurationen und Versionsbezeichnungen.

**Acceptance Scenarios**:

1. **Given** ein Chatbot und ein Modell mit vorhandenen Namen bis 100 Zeichen, **When** eine Konfiguration mit vorhandener Verhaltensanweisung, numerischer Temperatur und Versionsbezeichnung bis 20 Zeichen erfasst wird, **Then** besitzt sie eine eigene Kennung, genau diesen Chatbot, genau dieses Modell und einen automatisch gesetzten Erstellungszeitpunkt (FR-001–004).
2. **Given** eine bestehende Konfiguration, **When** für denselben Chatbot eine weitere Konfiguration mit demselben Modell und derselben Versionsbezeichnung erfasst wird, **Then** ist ein eigener Datensatz zulässig; die Versionsbezeichnung ist nicht eindeutig (FR-005).
3. **Given** eine Konfiguration, **When** eine Pflichtangabe fehlt oder ein Bezug auf einen nicht vorhandenen Chatbot beziehungsweise ein nicht vorhandenes Modell gesetzt wird, **Then** ist dieser Datenzustand unzulässig (FR-003, FR-012).
4. **Given** eine vorhandene Konfiguration, **When** Prompt oder Temperatur regulär geändert werden, **Then** bleibt ihr Erstellungszeitpunkt erhalten; eine allgemeine Unveränderlichkeit der Konfiguration ist nicht vorgeschrieben (FR-004–005).
5. **Given** ein Modell namens „Modell A“, **When** ein weiteres Modell mit exakt demselben Namen erfasst wird, **Then** ist der doppelte Modellname unzulässig; gleichnamige Chatbots sind dagegen zulässig (FR-002).

---

### User Story 2 - Werkzeuge je Konfiguration zuordnen und aktivieren (Priority: P2)

Als fachlich verantwortliche Person möchte ich festhalten, welche Werkzeuge eines MCP-Servers einer Konfiguration zugeordnet und dort aktiv oder inaktiv sind. Ein MCP-Server ist ein Anbieter solcher Werkzeuge.

**Why this priority**: Die Zuordnung beschreibt Fähigkeiten je Konfiguration, ohne daraus eine globale Aktivierung eines Werkzeugs abzuleiten.

**Independent Test**: Ein Server, ein Werkzeug und zwei vorbereitete Konfigurationen erlauben die Prüfung von Pflichtbezug, Mehrfachverwendung, Eindeutigkeit und unabhängigem Aktivstatus.

**Acceptance Scenarios**:

1. **Given** ein vorhandener Server, ein ihm zugeordnetes Werkzeug und eine vorhandene Konfiguration, **When** Werkzeug und Konfiguration erstmals zugeordnet werden, **Then** erhält die Zuordnung eine eigene Kennung und ist ohne abweichende Angabe aktiv (FR-001, FR-006–008).
2. **Given** eine bestehende Zuordnung, **When** dasselbe Werkzeug derselben Konfiguration erneut zugeordnet wird, **Then** ist die doppelte Zuordnung unzulässig, auch bei anderem Aktivstatus (FR-009).
3. **Given** ein Werkzeug mit aktiven Zuordnungen in zwei Konfigurationen, **When** eine Zuordnung deaktiviert wird, **Then** bleibt die andere aktiv; weder das Werkzeug noch die deaktivierte Zuordnung wird gelöscht (FR-008–009).
4. **Given** ein Server mit gültigen Pflichtangaben, **When** zwei Werkzeuge mit gleichem Namen und ohne Beschreibung erfasst werden, **Then** sind beide zulässig und jeweils genau diesem Server zugeordnet (FR-006–007).
5. **Given** ein Server oder Werkzeug, **When** eine Pflichtangabe fehlt, ein Name 101 Zeichen lang ist, eine Serveradresse 256 Zeichen lang ist oder ein Werkzeug auf einen nicht vorhandenen Server verweist, **Then** ist der betroffene Datenzustand unzulässig; ein vorhandener Adresstext bis 255 Zeichen unterliegt keiner belegten Formatprüfung (FR-006–007, FR-012–013).

---

### User Story 3 - Löschfolgen für abhängige Daten verstehen (Priority: P2)

Als fachlich verantwortliche Person möchte ich wissen, welche Datensätze bei einer Löschung erhalten bleiben oder mit entfernt werden und welche Beziehungen eine Löschung verhindern.

**Why this priority**: Die Regeln schützen die Zuordnung von Konfigurationen und verhindern verwaiste Werkzeugzuordnungen.

**Independent Test**: Vorbereitete Datensätze mit den fünf beschriebenen Beziehungen erlauben jede Löschprüfung unabhängig von einem Chatbotdialog.

**Acceptance Scenarios**:

1. **Given** ein Chatbot oder Modell mit mindestens einer Konfiguration, **When** der Chatbot beziehungsweise das Modell gelöscht werden soll, **Then** verhindert die bestehende Konfiguration die Löschung (FR-010).
2. **Given** eine Konfiguration mit Werkzeugzuordnungen, **When** die Konfiguration gelöscht wird, **Then** entfallen ihre Zuordnungen; Chatbot, Modell, Werkzeuge und Server bleiben bestehen (FR-011).
3. **Given** ein Werkzeug mit Zuordnungen in mehreren Konfigurationen, **When** das Werkzeug gelöscht wird, **Then** entfallen alle seine Zuordnungen; die Konfigurationen und der Server bleiben bestehen (FR-011).
4. **Given** ein Server mit Werkzeugen und deren Zuordnungen, **When** der Server gelöscht wird, **Then** entfallen seine Werkzeuge und deren Zuordnungen; betroffene Konfigurationen und Chatbots bleiben bestehen (FR-011).
5. **Given** eine Werkzeugzuordnung innerhalb einer Konfiguration, **When** diese Zuordnung aus der Konfiguration entfernt wird, **Then** entfällt nur die Zuordnung; Werkzeug und Konfiguration bleiben bestehen (FR-011).
6. **Given** ein Chatbot oder Modell ohne Konfiguration, **When** dieser Datensatz gelöscht wird, **Then** verhindert keine der beschriebenen Beziehungen seine Löschung (FR-010).

---

### User Story 4 - Vorhandene Beispielverwaltung einordnen (Priority: P3)

Als fachlich verantwortliche Person möchte ich die isolierte Beispielentität und ihre belegten Regeln kennen, ohne ihr eine unbelegte Bedeutung in der Chatbot-Kerndomäne zuzuschreiben.

**Why this priority**: Die Bestandsbeschreibung soll alle vorhandenen Entitäten erfassen und ihre fachliche Abgrenzung nachvollziehbar machen.

**Independent Test**: Ein Beispieldatensatz und Personen mit Lese- beziehungsweise Schreibberechtigung genügen für die unabhängige Prüfung.

**Acceptance Scenarios**:

1. **Given** eine Person mit Schreibberechtigung, **When** ein Beispieltext mit 2 oder 8 Zeichen erfasst wird, **Then** ist er zulässig und erhält eine Kennung; fehlender Text und Texte mit 1 oder 9 Zeichen sind bei der Beispielverwaltung unzulässig (FR-001, FR-014–015).
2. **Given** eine Person mit Leseberechtigung, **When** sie einzelne oder seitenweise aufgelistete Beispieldatensätze liest, **Then** ist dies erlaubt; Erstellen, Ändern und Löschen erfordern Schreibberechtigung (FR-015).
3. **Given** eine Person mit Schreibberechtigung und ein Beispieldatensatz, **When** sie seinen Text gültig ändert und ihn anschließend löscht, **Then** bleibt bei der Änderung die Kennung erhalten und nach der Löschung entfällt der Datensatz (FR-015).
4. **Given** eine nicht vorhandene Beispielkennung, **When** der Datensatz gelesen oder geändert wird, **Then** wird „nicht gefunden“ gemeldet (FR-016).
5. **Given** elf Beispieldatensätze, **When** ohne weitere Angaben seitenweise gelesen wird, **Then** enthält die erste Seite zehn Datensätze; negative Seitennummern und nicht positive Seitengrößen sind unzulässig (FR-016).

### Edge Cases

- **Fehlend und leer**: Ein Pflichttext darf nicht fehlen. Für die sechs Kernentitäten sind leere Texte und reine Leerzeichen jedoch nicht ausgeschlossen. Der Beispieltext darf aus Leerzeichen bestehen, muss bei der Beispielverwaltung aber die Länge 2–8 erfüllen.
- **Grenzlängen**: Namen bis 100 Zeichen, Serveradressen bis 255 Zeichen und Versionsbezeichnungen bis 20 Zeichen sind innerhalb ihrer Grenzen; jeweils ein Zeichen mehr überschreitet sie. Für Verhaltensanweisung und Werkzeugbeschreibung ist keine fachliche Maximallänge festgelegt.
- **Leerer Modellname**: Ein leerer Modellname ist möglich, ein zweiter identischer leerer Modellname verletzt die Eindeutigkeit. Eine Gleichsetzung unterschiedlich geschriebener Namen ist nicht fachlich festgelegt.
- **Temperatur**: Es gibt keinen festgelegten Standardwert und keinen belegten Mindest-/Höchstwert; gewöhnliche Werte wie −1 oder 3 werden nicht durch eine Bereichsregel ausgeschlossen. Nicht endliche Sonderwerte sind nicht als fachliche Garantie spezifiziert.
- **Mehrfachkonfigurationen**: Auch derselbe Chatbot kann mehrere Konfigurationen mit gleichem Modell und gleicher Versionsbezeichnung besitzen. Die Bezeichnung bestimmt weder eine Reihenfolge noch eine aktuelle oder freigegebene Konfiguration.
- **Optionale Zuordnungen**: Ein Chatbot darf ohne Konfiguration existieren; eine Konfiguration ohne Werkzeuge, ein Server ohne Werkzeuge und ein Werkzeug ohne Konfigurationszuordnung sind ebenfalls zulässig.
- **Inaktive Doppelzuordnung**: Eine inaktive Zuordnung bleibt bestehen und verhindert eine zweite Zuordnung desselben Konfiguration/Werkzeug-Paares.
- **Serverlöschung**: Die Löschung kann Zuordnungen in mehreren Chatbots betreffen, entfernt aber keine dieser Konfigurationen oder Chatbots.
- **Fehlende Beschreibung**: Eine fehlende und eine leere Werkzeugbeschreibung sind beide zulässig, aber verschiedene Werte.
- **Unbekannte Beispielkennung beim Löschen**: Die ausdrücklich belegte Nichtgefunden-Regel für Lesen und Ändern ist nicht identisch für das Löschen festgelegt.

## Requirements *(mandatory)*

### Functional Requirements

Die Anforderungen formulieren die belegten Bestandsregeln. „Vorhanden“ bedeutet, dass ein Wert nicht fehlt; bei Texten bedeutet es nicht automatisch „nicht leer“.

- **FR-001 — Identität**: Jeder Datensatz der sieben Entitätsarten MUSS eine eigene Kennung besitzen, die innerhalb seiner Entitätsart eindeutig ist und bei regulärer Anlage automatisch vergeben wird. Werkzeugzuordnungen sind eigenständig identifizierbare Datensätze.
- **FR-002 — Chatbot und Modell**: Chatbotname und Modellname MÜSSEN vorhanden sein und dürfen höchstens 100 Zeichen umfassen. Modellnamen MÜSSEN eindeutig sein; exakt gleiche Modellnamen sind unzulässig. Chatbotnamen müssen nicht eindeutig sein.
- **FR-003 — Konfiguration**: Jede Konfiguration MUSS genau einem vorhandenen Chatbot und genau einem vorhandenen Modell zugeordnet sein. Verhaltensanweisung, numerischer Temperaturwert und Versionsbezeichnung MÜSSEN vorhanden sein; die Versionsbezeichnung darf höchstens 20 Zeichen umfassen.
- **FR-004 — Erstellungszeitpunkt**: Jede Konfiguration MUSS einen automatisch gesetzten Erstellungszeitpunkt als Zeitpunkt mit Zeitzonenbezug besitzen. Bei regulären Änderungen bleibt dieser erhalten. Daraus folgt keine Garantie, dass der ursprünglich verwendete Zeitzonenname erhalten bleibt.
- **FR-005 — Konfigurationsvielfalt**: Ein Chatbot MUSS mit 0..n Konfigurationen darstellbar sein. Dasselbe Modell und dieselbe Versionsbezeichnung dürfen mehrfach, auch beim selben Chatbot, verwendet werden. Versionen bestimmen keine belegte Reihenfolge, Unveränderlichkeit oder aktuelle Auswahl.
- **FR-006 — MCP-Server**: Jeder Server MUSS einen vorhandenen Namen bis 100 Zeichen und einen vorhandenen Adresstext bis 255 Zeichen besitzen. Beide Werte müssen nicht eindeutig sein. Ein Server kann 0..n Werkzeuge besitzen.
- **FR-007 — MCP-Werkzeug**: Jedes Werkzeug MUSS genau einem vorhandenen Server zugeordnet sein und einen vorhandenen Namen bis 100 Zeichen besitzen. Die Beschreibung ist optional. Werkzeugnamen müssen weder global noch innerhalb desselben Servers eindeutig sein.
- **FR-008 — Werkzeugaktivierung**: Jede Werkzeugzuordnung MUSS genau eine vorhandene Konfiguration, genau ein vorhandenes Werkzeug und einen Aktivstatus (aktiv/inaktiv) besitzen. Neue Zuordnungen sind standardmäßig aktiv. Der Status gilt ausschließlich für die einzelne Zuordnung; Deaktivieren löscht weder Werkzeug noch Zuordnung.
- **FR-009 — Zuordnungseindeutigkeit**: Pro Konfiguration und Werkzeug darf höchstens eine Zuordnung existieren, unabhängig von deren Aktivstatus. Eine Konfiguration kann 0..n verschiedene Werkzeuge verwenden; ein Werkzeug kann 0..n verschiedenen Konfigurationen zugeordnet sein.
- **FR-010 — Löschhindernisse**: Ein Chatbot oder Modell darf nicht gelöscht werden, solange eine Konfiguration darauf verweist. Ohne solche Verweise ist die Löschung durch keine der beschriebenen Beziehungen eingeschränkt.
- **FR-011 — Abhängige Löschungen**: Löschen einer Konfiguration MUSS ihre Werkzeugzuordnungen entfernen. Löschen eines Werkzeugs MUSS alle zugehörigen Zuordnungen entfernen. Löschen eines Servers MUSS seine Werkzeuge und damit deren Zuordnungen entfernen. Entfernen einer Zuordnung aus einer Konfiguration MUSS diese Zuordnung entfernen. Alle jeweils anderen Datensätze bleiben entsprechend der Beziehungstabelle bestehen.
- **FR-012 — Gültige Datenzustände**: Fehlende Pflichtwerte, fehlende oder nicht vorhandene Pflichtreferenzen, überschrittene Längengrenzen und die beiden beschriebenen Eindeutigkeitsverletzungen sind unzulässig. Ein abhängiger Datensatz MUSS jeweils genau das in der Beziehungstabelle benannte vorhandene übergeordnete Objekt referenzieren.
- **FR-013 — Bestandsgrenzen**: Für die Kernentitäten sind keine Mindesttextlänge, kein Ausschluss reiner Leerzeichen, keine Adressformatprüfung, kein Temperaturbereich und kein Versionsformat belegt. Für Verhaltensanweisung und Werkzeugbeschreibung ist keine fachliche Maximallänge definiert. Zusätzliche Regeln dürfen nicht als bereits bestehende Geschäftsregeln dargestellt werden.
- **FR-014 — Beispieltext**: Ein Beispieldatensatz MUSS einen vorhandenen Text mit höchstens 8 Zeichen besitzen. Die Beispielverwaltung prüft zusätzlich die Mindestlänge 2; Text-Eindeutigkeit und Ausschluss reiner Leerzeichen sind nicht vorgeschrieben. Die untere Grenze ist nicht auf jeder Speicherungsebene gleich abgesichert.
- **FR-015 — Beispielverwaltung**: Erstellen, Lesen, seitenweises Lesen, Ändern und Löschen sind für die Beispielentität belegt. Lese- oder Schreibberechtigung genügt zum Lesen; Erstellen, Ändern und Löschen erfordern Schreibberechtigung. Reguläres Ändern des Textes MUSS die Kennung erhalten.
- **FR-016 — Beispielsuche und Seiten**: Lesen oder Ändern einer unbekannten Beispielkennung MUSS „nicht gefunden“ melden. Ohne weitere Angaben beginnt die seitenweise Anzeige bei Seite 0 mit bis zu 10 Datensätzen. Seitennummern MÜSSEN nicht negativ und Seitengrößen positiv sein. Eine feste Reihenfolge oder fachliche maximale Seitengröße ist nicht belegt.
- **FR-017 — Dokumentationsvollständigkeit**: Diese Spezifikation MUSS alle sieben Entitäten, ihre sämtlichen Attribute einschließlich Kennungen, alle fünf direkten Beziehungen sowie belegte Validierungen und Löschregeln beschreiben. Abnahme: Vergleich mit dem Quelleninventar ohne fehlendes Attribut, fehlende Beziehung oder unbelegt ergänzte Geschäftsregel.

### Key Entities *(include if feature involves data)*

Jede Entität besitzt zusätzlich zu den folgenden Fachattributen eine eigene Kennung (`id`) nach FR-001. Die Namen in Klammern ermöglichen den Bestandsabgleich, ohne eine Umsetzung vorzugeben.

| Entität | Fachliche Bedeutung | Vollständige Fachattribute und Regeln |
| --- | --- | --- |
| Chatbot (`Chatbot`) | Benannter Chatbot mit separat geführten Einstellungen. | Name (`name`): vorhanden, höchstens 100 Zeichen, nicht zwingend eindeutig. |
| Modell (`Model`) | Namentlich identifiziertes, wiederverwendbares KI-Modell. | Modellname (`modelName`): vorhanden, höchstens 100 Zeichen, eindeutig. |
| Konfiguration (`ChatbotConfig`) | Einstellungen eines bestimmten Chatbots einschließlich Modellbezug. | Chatbot (`chatbot`): genau einer, vorhanden. Modell (`model`): genau eines, vorhanden. Verhaltensanweisung (`prompt`): vorhandener Text ohne festgelegte fachliche Maximallänge. Temperatur (`temperature`): vorhandener numerischer Wert, ohne festgelegten Bereich oder Standardwert. Versionsbezeichnung (`version`): vorhanden, höchstens 20 Zeichen, nicht eindeutig. Erstellungszeitpunkt (`createdAt`): vorhanden, automatisch gesetzt, bei regulärer Änderung erhalten, mit Zeitzonenbezug. Werkzeugzuordnungen (`chatbotTools`): 0..n, initial leer, ohne belegte Reihenfolge. |
| MCP-Server (`McpServer`) | Anbieter von Werkzeugen. | Name (`name`): vorhanden, höchstens 100 Zeichen. Adresse (`url`): vorhandener Text, höchstens 255 Zeichen. Beide nicht zwingend eindeutig; keine belegte Adressformatprüfung. |
| MCP-Werkzeug (`McpTool`) | Benannte Fähigkeit eines bestimmten Servers. | Server (`mcpServer`): genau einer, vorhanden. Name (`name`): vorhanden, höchstens 100 Zeichen, nicht zwingend eindeutig. Beschreibung (`description`): optionaler Text ohne festgelegte fachliche Maximallänge. |
| Werkzeugzuordnung (`ChatbotTool`) | Verbindung von Konfiguration und Werkzeug mit konfigurationsbezogenem Aktivstatus. | Konfiguration (`chatbotConfig`): genau eine, vorhanden. Werkzeug (`mcpTool`): genau eines, vorhanden. Aktivstatus (`isActive`): vorhanden, aktiv/inaktiv, standardmäßig aktiv. Kombination aus Konfiguration und Werkzeug eindeutig. |
| Beispieldatensatz (`TheEntity`) | Isolierter Beispieldatensatz ohne belegte Bedeutung in der Chatbot-Domäne. | Text (`textAttribute`): vorhanden, gespeichert höchstens 8 Zeichen; bei der Beispielverwaltung zusätzlich Mindestlänge 2, nicht zwingend eindeutig. Keine Beziehungen zu den anderen Entitäten. |

Die gemeinsame Kennung ist eine Identitätseigenschaft und keine zusätzliche fachliche Entität. Die Sammlung von Werkzeugzuordnungen ist eine Beziehung, kein zusätzliches Datenobjekt.

#### Beziehungen und Lebenszyklus

| Übergeordnetes Objekt | Abhängiges Objekt | Kardinalität und Pflichtbezug | Folge der Löschung des übergeordneten Objekts |
| --- | --- | --- | --- |
| Chatbot | Konfiguration | Chatbot hat 0..n Konfigurationen; jede Konfiguration genau 1 Chatbot. | Verhindert, solange eine Konfiguration darauf verweist. |
| Modell | Konfiguration | Modell hat 0..n Konfigurationen; jede Konfiguration genau 1 Modell. | Verhindert, solange eine Konfiguration darauf verweist. |
| MCP-Server | MCP-Werkzeug | Server hat 0..n Werkzeuge; jedes Werkzeug genau 1 Server. | Werkzeuge und deren Werkzeugzuordnungen entfallen; Konfigurationen bleiben bestehen. |
| Konfiguration | Werkzeugzuordnung | Konfiguration hat 0..n Zuordnungen; jede Zuordnung genau 1 Konfiguration. | Zuordnungen entfallen; Werkzeuge, Server, Chatbot und Modell bleiben bestehen. |
| MCP-Werkzeug | Werkzeugzuordnung | Werkzeug hat 0..n Zuordnungen; jede Zuordnung genau 1 Werkzeug. | Zuordnungen entfallen; Konfigurationen und Server bleiben bestehen. |

Diese fünf direkten Beziehungen vermitteln eine auf beiden Seiten optionale n:m-Beziehung zwischen Konfiguration und Werkzeug. Das Löschen einer Zuordnung entfernt weder ihr Werkzeug noch ihre Konfiguration. Das Entfernen eines abhängigen Datensatzes löscht kein übergeordnetes Objekt.

#### Validierungsmatrix

| Regelgruppe | Geltungsbereich | Zulässig | Unzulässig oder nicht festgelegt |
| --- | --- | --- | --- |
| Identität | Alle sieben Entitäten | Eigene vergebene Kennung je Datensatz. | Fehlende oder innerhalb einer Entitätsart doppelte Kennung. |
| Pflichtname und Länge | Chatbot, Modell, Server, Werkzeug | Vorhandener Name bis 100 Zeichen, auch leer. | Fehlender Name oder mehr als 100 Zeichen. |
| Serveradresse | Server | Vorhandener Adresstext bis 255 Zeichen, auch leer. | Fehlender Wert oder mehr als 255 Zeichen; keine zusätzliche Formatprüfung belegt. |
| Verhaltensanweisung | Konfiguration | Vorhandener Text, auch leer. | Fehlender Wert; keine fachliche Maximallänge belegt. |
| Temperatur | Konfiguration | Vorhandener numerischer Wert. | Fehlender Wert; Bereich, Standardwert und fachliches Sonderwertverhalten nicht festgelegt. |
| Versionsbezeichnung | Konfiguration | Vorhandener Text bis 20 Zeichen, auch leer oder mehrfach verwendet. | Fehlender Wert oder mehr als 20 Zeichen; Format und Eindeutigkeit nicht festgelegt. |
| Erstellungszeitpunkt | Konfiguration | Automatisch gesetzter Zeitpunkt, bei regulärer Änderung erhalten. | Fehlender Zeitpunkt; reguläre Änderungen dürfen ihn nicht ersetzen. |
| Beschreibung | Werkzeug | Fehlender oder vorhandener Text, auch leer. | Keine zusätzliche fachliche Längen- oder Inhaltsregel belegt. |
| Pflichtbeziehung | Fünf direkte Beziehungen | Genau ein vorhandenes übergeordnetes Objekt je abhängigem Datensatz. | Fehlender Bezug oder nicht vorhandenes Ziel. |
| Modellnamen-Eindeutigkeit | Modell | Unterschiedliche Namen. | Exakt gleiche Namen, einschließlich zweier leerer Namen; weitere Namensnormalisierung nicht festgelegt. |
| Zuordnungseindeutigkeit | Werkzeugzuordnung | Unterschiedliche Konfiguration/Werkzeug-Paare. | Gleiches Paar mehrfach, unabhängig vom Aktivstatus. |
| Aktivstatus | Werkzeugzuordnung | Aktiv/inaktiv; ohne abweichende Angabe aktiv. | Fehlender Status eines bestehenden Datensatzes. |
| Beispieltext | Beispieldatensatz und Beispielverwaltung | Gespeicherter vorhandener Text bis 8 Zeichen; bei der Beispielverwaltung zusätzlich mindestens 2. Reine Leerzeichen innerhalb dieser Grenzen sind zulässig. | Fehlender Text oder mehr als 8 Zeichen; in der Beispielverwaltung zusätzlich weniger als 2. Mindestlänge nicht auf jeder Speicherungsebene abgesichert. |
| Beispielberechtigung | Beispielverwaltung | Lesen mit Lese-/Schreibberechtigung; Änderungen mit Schreibberechtigung. | Änderungen ohne Schreibberechtigung; keine Übertragung auf Kernentitäten belegt. |
| Beispielseiten | Beispielverwaltung | Seitennummer ab 0, Größe ab 1; Standard erste Seite, Größe 10. | Negative Seitennummer oder nicht positive Größe; feste Reihenfolge und maximale Größe nicht festgelegt. |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 — Vollständigkeit**: 100 % der sechs Kernentitäten und der einen Beispielentität, ihrer Attribute und der fünf direkten Beziehungen sind beschrieben; beim Bestandsabgleich bleibt kein Element ohne Zuordnung.
- **SC-002 — Prüfbarkeit**: Für jede der 15 Regelgruppen kann eine fachlich prüfende Person anhand der Spezifikation zulässige, unzulässige und nicht festgelegte Fälle unterscheiden. Alle 17 Anforderungen besitzen Akzeptanzszenarien oder einen ausdrücklich benannten Vollständigkeitsvergleich.
- **SC-003 — Löschfolgen**: Für alle fünf direkten Beziehungen sowie das Entfernen einer einzelnen Werkzeugzuordnung sind erhaltene und entfallende Datensätze beziehungsweise Löschhindernisse ohne Zusatzannahmen bestimmbar.
- **SC-004 — Verständlichkeit**: Bei einer fachlichen Abnahme können zwei verantwortliche Personen unabhängig alle vier Abläufe erklären und die Ergebnisse der 21 Akzeptanzszenarien übereinstimmend begründen; keine widersprüchliche Regelinterpretation bleibt offen.
- **SC-005 — Bestandstreue**: Bei der Prüfung gegen das Quelleninventar gibt es null unbelegt ergänzte Pflichtvalidierungen, Versionsauswahlregeln oder Aussagen über bereits bedienbare Kernverwaltungsfunktionen.

Die Erfolgskriterien bewerten das Dokumentationsergebnis. Neue Laufzeit-, Last- oder Bedienzeitziele für das Produkt sind aus dem Bestand nicht abgeleitet. Die fachliche Abnahme durch zwei Personen ist ein überprüfbares Ziel, kein bereits ausgeführter Nachweis.

## Assumptions

- **Belegbasis**: Maßgeblich sind die vorhandenen Quellen am 2026-11-17, nicht der ausgelesene Zustand einer laufenden Datenbank. Das Java-Modell liegt unter einem vom Auftrag abweichenden Basispaket; die tatsächlichen Pfade und Einzelbelege stehen in [source-analysis.md](source-analysis.md).
- **Scope**: Die Kerndomäne umfasst Chatbots und deren Konfigurationen, den Modellkatalog sowie MCP-Server, Werkzeuge und Zuordnungen. Der isolierte Beispieldatensatz wird der Vollständigkeit halber aufgenommen. Gespräche, Nachrichten, Nutzendenprofile, Wissensbestände, Mandanten, Abrechnung und Veröffentlichungs-/Freigabestatus sind in der untersuchten Belegbasis nicht als eigene fachliche Datenobjekte definiert.
- **Akteure und Grundsätze**: „Fachlich verantwortliche Person“ ist die angenommene Perspektive für die Beschreibung des Datenmodells, keine belegte konkrete Berechtigungsrolle der Kernentitäten. Die Projektgrundsätze trennen interne Verwaltung und öffentliche Nutzung; eine konkrete Rechtezuordnung für die sechs Kernentitäten ist aus dem Modell nicht ableitbar. Die belegten Lese-/Schreibrollen betreffen die Beispielverwaltung.
- **Bedienbarkeit**: Die Szenarien formulieren gültige Bestandsdaten und Änderungen. Eigene Verwaltungsfunktionen oder fachliche Suchregeln der sechs Kernentitäten sind nicht belegt. Eine aktive Werkzeugzuordnung garantiert weder Ausführung noch Erreichbarkeit des Servers oder Verfügbarkeit des Modells.
- **Abhängigkeiten**: Konfigurationen benötigen bestehende Chatbots und Modelle; Werkzeuge benötigen bestehende Server; Zuordnungen benötigen bestehende Konfigurationen und Werkzeuge. Die Beteiligten können ansonsten ohne abhängige Datensätze existieren.
- **Validierungsebenen**: Die Regelbeschreibung ist keine Zusage einer frühen Eingabeprüfung oder bestimmter Fehlermeldungen für die Kernentitäten. Die Beispielverwaltung prüft ihre Mindesttextlänge zusätzlich bei Eingaben; die Speicherung sichert diese untere Grenze nicht überall ab. Der Erstellungszeitpunkt bleibt bei regulären Konfigurationsänderungen erhalten; ein Schutz gegen Änderungen über jeden möglichen Speicherzugriff ist nicht belegt. Die technische Unterscheidung steht in der Quellenanalyse.
- **Textlänge**: Grenzfallprüfungen beziehen sich auf gewöhnliche Buchstaben. Eine für alle Unicode-Sonderzeichen einheitliche Zählung sichtbarer Zeichen ist aus den vorhandenen Regeln nicht ableitbar.
- **Version und Status**: Die Versionsbezeichnung ist frei vergeben, ohne belegte Format- oder Auswahlregel. Aktivierung betrifft nur die Werkzeugzuordnung. Weitergehende Archivierungs-/Freigabeprozesse, Aufbewahrungsfristen, fachliche Sortierungen oder Namensnormalisierungen werden mangels Beleg nicht festgelegt.
- **Governance**: Die aktuelle Projektverfassung und das tatsächliche Java-Basispaket weichen voneinander ab. Die Dokumentation hält den Bestand fest; eine spätere strukturelle Umsetzung benötigt den in der Verfassung vorgesehenen Abgleich. Die Paketabweichung ist in der Quellenanalyse konkret benannt.
