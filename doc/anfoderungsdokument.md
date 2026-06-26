# Anforderungsdokument

## Modulare KI-gestützte Onboarding-Plattform für Datenschutzprozesse

**Projektkontext:** Zweiplus
**Dokumentversion:** 0.2
**Status:** Entwurf
**Ziel:** Fachliche Grundlage für MVP-Abgrenzung, UX-Konzeption und anschließendes Architekturdokument

---

# 1. Ausgangslage

Zweiplus möchte Kunden künftig strukturierter durch datenschutzbezogene Onboarding-Prozesse führen. Heute entstehen in solchen Prozessen viele Rückfragen per E-Mail oder Telefon, weil Kunden häufig nicht verstehen, welche Informationen sie liefern müssen, warum diese Informationen benötigt werden oder wie fachliche Datenschutzbegriffe einzuordnen sind.

Die geplante Anwendung soll diesen Prozess verbessern. Kunden sollen nicht nur ein Formular ausfüllen, sondern durch klar strukturierte Module geführt werden. Innerhalb dieser Module sollen sie Fragen beantworten, Hilfestellung durch eine KI erhalten, Dokumente hochladen und bei Bedarf vorbereitete Vorlagen nutzen können, um Informationen bei Dritten einzuholen.

Die Plattform soll nicht als reine VVT-Anwendung entwickelt werden. Stattdessen soll eine **modulare KI-gestützte Onboarding-Plattform für Datenschutzprozesse** entstehen. Ein VVT-Onboarding kann das erste Pilotmodul sein, die technische und fachliche Struktur soll jedoch von Beginn an für weitere Module und Geschäftsprozesse erweiterbar sein.

Mögliche spätere Module sind beispielsweise:

- VVT-Onboarding
- AVV-Onboarding
- TOM-Erfassung
- DSFA-Vorprüfung
- Software-Erfassung
- Dienstleister-Erfassung
- Betroffenenanfragen
- Datenschutz-Audits
- Website-Datenschutzchecks
- weitere datenschutzbezogene Kundenprozesse

Die Plattform soll strukturierte Daten erzeugen, diese maschinell validieren und perspektivisch über Zielsystem-Adapter, insbesondere über die REST-Schnittstelle des bestehenden Datenschutzmanagementsystems DPMS, weiterverarbeiten können.

---

# 2. Zielsetzung

Ziel ist die Entwicklung einer webbasierten Plattform, mit der Zweiplus Datenschutz-Onboardings modular konfigurieren, durchführen, prüfen und in strukturierte Daten überführen kann.

Die Plattform soll:

- Datenschutzprozesse als konfigurierbare Module abbilden,
- pro Modul mehrere Steps mit Fragen bereitstellen,
- verschiedene Antworttypen unterstützen,
- Kunden bei der Beantwortung durch KI unterstützen,
- pro Modul spezifisches datenschutzrechtliches Wissen für die KI hinterlegen,
- strukturierte KI-Vorschläge erzeugen,
- KI-Vorschläge und Nutzereingaben im Backend validieren,
- Fortschritt, Zuständigkeiten und Bearbeitungsreihenfolgen transparent darstellen,
- Vorlagen für externe Informationsbeschaffung bereitstellen,
- Ergebnisse durch Zweiplus prüfen und freigeben lassen,
- validierte Daten in einem kanonischen Zwischenmodell speichern,
- Zielsystem-Mappings, insbesondere für DPMS, ermöglichen,
- später durch weitere Module und Geschäftsprozesse erweiterbar bleiben.

Der zentrale Produktgedanke lautet:

> Die Anwendung ist eine generische, modulare Onboarding-Plattform für Datenschutzprozesse. Fachliche Prozesse werden als Module abgebildet. Jedes Modul definiert eigene Steps, Fragen, Antworttypen, KI-Wissenskonfigurationen, Validierungsregeln, Zuständigkeiten, Vorlagen, Freischaltlogik und Zielsystem-Mappings.

---

# 3. Produktvision

Die Plattform soll als intelligenter Erfassungs-, Unterstützungs-, Strukturierungs- und Import-Layer zwischen Kunden, Zweiplus, externen Informationsquellen und bestehenden Datenschutzmanagementsystemen dienen.

Die KI ersetzt nicht die fachliche Prüfung durch Zweiplus. Sie unterstützt Nutzer dabei, Fragen zu verstehen, passende Antworten zu formulieren, Dokumente auszuwerten und Eingaben semantisch zu prüfen. Die finale technische und fachliche Absicherung erfolgt durch Backend-Validierung und Review-Prozesse.

Die Plattform soll langfristig nicht nur einzelne Datenschutzdokumente erzeugen, sondern unterschiedliche Datenschutzprozesse digitalisieren und modular orchestrieren.

---

# 4. Grundprinzipien

## 4.1 Module statt Einzelformulare

Die Plattform darf nicht fest auf einen einzelnen Prozess wie VVT zugeschnitten sein. Stattdessen müssen Datenschutzprozesse als wiederverwendbare Module modelliert werden.

Ein Modul ist eine fachliche Einheit mit eigenen:

- Steps,
- Fragen,
- Antworttypen,
- Erklärtexten,
- KI-Hilfen,
- Wissensquellen,
- Validierungsregeln,
- Vorlagen,
- Zuständigkeiten,
- Output-Schema,
- Zielsystem-Mapping.

## 4.2 Konfigurierbare Steps und Fragen

Fragen und Steps sollen nicht hart im Frontend codiert werden. Das Frontend soll Module dynamisch anhand von Moduldefinitionen darstellen können.

Dadurch können später neue Datenschutzmodule ergänzt werden, ohne die Grundarchitektur neu zu bauen.

## 4.3 KI als Assistenz, nicht als finale Entscheidungsinstanz

Die KI unterstützt bei:

- Erklärung von Fragen,
- Beantwortung von Fragen,
- Umwandlung von Freitext in strukturierte Daten,
- semantischer Prüfung,
- Dokumentenanalyse,
- Erkennung von Lücken,
- Formulierung von Rückfragen,
- Erstellung strukturierter Vorschläge.

Die KI darf jedoch nicht ungeprüft finale Daten in Zielsysteme schreiben oder verbindliche fachliche Freigaben ersetzen.

## 4.4 Modulbezogenes Datenschutzwissen

Jedes Modul muss definieren können, welches datenschutzrechtliche Fachwissen die KI für dieses Modul verwenden soll.

Die KI darf nicht nur mit einem allgemeinen Datenschutz-Prompt arbeiten. Stattdessen braucht jedes Modul eine eigene Wissenskonfiguration, die fachlich zu den jeweiligen Fragen und Zielen passt.

Beispiele:

Ein VVT-Modul benötigt Wissen zu Verarbeitungstätigkeiten, Zwecken, Datenkategorien, betroffenen Personen, Empfängern, Löschfristen und Rechtsgrundlagen.

Ein TOM-Modul benötigt Wissen zu technischen und organisatorischen Maßnahmen, Zugriffskontrolle, Backup, Verschlüsselung, Berechtigungskonzepten und Nachweisen.

Ein AVV-Modul benötigt Wissen zu Auftragsverarbeitung, Rollenverteilung, Unterauftragnehmern, Weisungsbindung, TOMs und Vertragsbestandteilen.

## 4.5 Backend als verbindliche Validierungsinstanz

Alle Eingaben und KI-Ausgaben müssen im Backend maschinell validiert werden.

Die KI kann semantisch prüfen und Vorschläge machen. Die verbindliche Prüfung von Format, Schema, Datentypen, Pflichtfeldern, erlaubten Werten, Statusübergängen und Importfähigkeit erfolgt jedoch im Backend.

## 4.6 Kanonisches Zwischenmodell

Die Plattform soll Daten zunächst in einem eigenen, zielsystemunabhängigen Zwischenmodell speichern.

Dieses Modell bildet die fachlichen Ergebnisse eines Moduls strukturiert ab. Erst danach wird über Adapter in konkrete Zielsystemformate gemappt, beispielsweise in DPMS-kompatibles JSON.

## 4.7 Zielsysteme über Adapter

Zielsysteme wie DPMS sollen über Adapter angebunden werden.

Die Onboarding-Module kennen nicht direkt die DPMS-API. Sie erzeugen strukturierte, validierte Daten. Der jeweilige Adapter übernimmt Mapping, technische API-Kommunikation, Fehlerbehandlung und Importstatus.

---

# 5. Zielgruppen und Rollen

## 5.1 Zweiplus-Administrator

Der Zweiplus-Administrator verwaltet die Plattform und konfiguriert Module, Fragen, Wissensquellen, Vorlagen, Reihenfolgen und Zielsystem-Mappings.

Typische Aufgaben:

- Module anlegen und bearbeiten,
- Modulreihenfolgen festlegen,
- parallele Bearbeitung konfigurieren,
- Steps und Fragen pflegen,
- Antworttypen definieren,
- Pflichtfelder und Validierungsregeln verwalten,
- KI-Wissenskonfigurationen je Modul hinterlegen,
- E-Mail- und Fragebogen-Vorlagen verwalten,
- Zielsystem-Mappings konfigurieren,
- Nutzer und Zuständigkeiten verwalten.

## 5.2 Zweiplus-Fachbearbeiter / Reviewer

Der Reviewer prüft Kundeneingaben, KI-Vorschläge und validierte strukturierte Daten.

Typische Aufgaben:

- Kundeneingaben prüfen,
- KI-Vorschläge akzeptieren, bearbeiten oder ablehnen,
- semantische KI-Prüfungen einsehen,
- Backend-Validierungsergebnisse prüfen,
- Rückfragen an Kunden formulieren,
- Module zur Korrektur zurückgeben,
- Module freigeben,
- Importvorschau prüfen,
- Import in Zielsysteme freigeben.

## 5.3 Kunde

Der Kunde bearbeitet ihm zugewiesene Module oder Teilbereiche eines Onboardings.

Typische Aufgaben:

- Dashboard öffnen,
- verfügbare und gesperrte Module erkennen,
- Zuständigkeiten nachvollziehen,
- Modul-Erklärtexte lesen,
- Steps bearbeiten,
- Fragen beantworten,
- Dokumente hochladen,
- KI-Hilfe nutzen,
- KI-Vorschläge prüfen und übernehmen,
- vorbereitete E-Mail- oder Fragebogen-Vorlagen nutzen,
- Rückfragen beantworten.

## 5.4 Externe Informationsgeber

Externe Informationsgeber sind Personen oder Organisationen, von denen Informationen benötigt werden können, beispielsweise IT-Dienstleister, Steuerberater, Softwareanbieter oder Fachabteilungen.

Im MVP müssen externe Informationsgeber noch nicht direkt in der Plattform mitarbeiten können.

Stattdessen soll die Plattform vorbereitete E-Mail-Texte und Fragebogen-Dateien bereitstellen, die der Kunde oder Zweiplus nutzen kann, um Informationen extern einzuholen.

Perspektivisch können externe Informationsgeber eigene Bearbeitungslinks, Zugänge oder Fragebogenansichten erhalten. Dies ist jedoch nicht Teil des initialen MVP.

## 5.5 System / KI-Agent

Der KI-Agent unterstützt je nach Kontext auf Dashboard-, Modul-, Step- oder Fragenebene.

Typische Aufgaben:

- allgemeine Fragen zum Onboarding beantworten,
- konkrete Modulfragen erklären,
- fachliche Datenschutzbegriffe erläutern,
- Antwortvorschläge erzeugen,
- Freitexte normalisieren,
- Dokumente auswerten,
- Eingaben semantisch prüfen,
- strukturierte Outputs erzeugen,
- offene Punkte erkennen,
- Rückfragen vorschlagen.

---

# 6. Fachliches Zielbild

Ein typischer Ablauf sieht wie folgt aus:

1. Zweiplus legt ein Onboarding für einen Kunden an.
2. Das System zeigt dem Kunden ein Dashboard mit allen relevanten Modulen.
3. Freigeschaltete Module sind aktiv, noch nicht verfügbare Module sind ausgegraut und mit Schloss dargestellt.
4. Die Bearbeitungsreihenfolge der Module ist konfigurierbar.
5. Manche Module können parallel freigeschaltet werden, wenn sie unabhängig voneinander oder durch unterschiedliche Personen bearbeitet werden können.
6. Für jedes Modul ist sichtbar, wer es bearbeiten soll.
7. Der Kunde öffnet ein Modul.
8. Das Modul zeigt Ziel, Warum, Wer, Aufwand und einen kurzen Explainer.
9. Das Modul besteht aus mehreren Steps.
10. Jeder Step enthält eine oder mehrere Fragen.
11. Fragen können als Einfachauswahl, Mehrfachauswahl, Textantwort oder Dateiupload beantwortet werden.
12. Bei Bedarf kann pro Modul oder Step eine Vorlage genutzt werden, beispielsweise ein E-Mail-Text oder ein Fragebogen als Datei.
13. Die KI unterstützt beim Verständnis und bei der Beantwortung.
14. Die KI nutzt dafür das für das jeweilige Modul definierte Datenschutzwissen.
15. Eingaben werden gespeichert.
16. Die KI kann Eingaben semantisch prüfen und strukturierte Vorschläge erzeugen.
17. Das Backend validiert Eingaben und KI-Ausgaben technisch und deterministisch.
18. Vollständige Steps werden abgehakt.
19. Die Progressanzeige des Moduls aktualisiert sich anhand abgeschlossener Steps.
20. Nach Abschluss eines Moduls können Folge-Module gemäß Freischaltlogik aktiviert werden.
21. Zweiplus prüft die Ergebnisse.
22. Nach Freigabe wird ein kanonischer Output erzeugt.
23. Der Output kann über einen Zielsystem-Adapter, beispielsweise DPMS, gemappt und importiert werden.

---

# 7. MVP-Zuschnitt

Der MVP soll bereits den Plattformgedanken abbilden, auch wenn zunächst nur ein oder wenige fachliche Module umgesetzt werden.

Der MVP soll kein reines VVT-Formular sein, sondern eine erste funktionsfähige Version der modularen Onboarding-Plattform.

## 7.1 Im MVP enthalten

Der MVP soll mindestens enthalten:

- Dashboard mit Modulübersicht,
- konfigurierbare Modulreihenfolge,
- gesperrte und freigeschaltete Module,
- parallele Modulfreischaltung,
- sichtbare Zuständigkeit pro Modul,
- allgemeiner KI-Chatbot auf dem Dashboard,
- Module mit mehreren Steps,
- Step-Status und abgehakte abgeschlossene Steps,
- Progressbalken je Modul,
- Modul-Erklärtext mit Ziel, Warum, Wer, Aufwand und kurzem Explainer,
- Antworttypen:
  - Einfachauswahl,
  - Mehrfachauswahl,
  - Textantwort,
  - Dateiupload für Bilder und Dokumente,

- KI-Unterstützung auf Modul-, Step- und Fragenebene,
- pro Modul definierbare KI-Wissenskonfiguration mit datenschutzrechtlichem Fachwissen,
- strukturierter KI-Output,
- semantische KI-Prüfung von Eingaben,
- Backend-Validierung von Eingaben und KI-Ausgaben,
- strukturierte Speicherung der Antworten,
- kanonisches Zwischenmodell,
- Review-Ansicht für Zweiplus,
- vorbereitete E-Mail-Vorlagen pro Modul oder Step,
- hinterlegbare Fragebogen-Dateien pro Modul oder Step,
- Ausgabe beziehungsweise Download/Kopieren dieser Vorlagen,
- Vorbereitung auf Zielsystem-Mapping, insbesondere DPMS.

## 7.2 Nicht im MVP enthalten

Nicht Teil des MVP sind:

- direkte externe Mitarbeit in der Plattform,
- externe Nutzeraccounts,
- externe Login-Links,
- automatischer Versand von E-Mails,
- Rücklauf-Tracking externer Fragebögen,
- Fristenmanagement für externe Beteiligte,
- vollständiger bidirektionaler DPMS-Sync,
- vollständig automatischer Import ohne Review,
- umfangreiche Rollen- und Rechteverwaltung,
- alle denkbaren Datenschutzmodule,
- vollständig automatisierte rechtliche Freigabe durch KI.

## 7.3 MVP-Kernsatz

Der MVP ist eine modulare KI-gestützte Datenschutz-Onboarding-Plattform, in der Kunden freigeschaltete Module mit Steps und Fragen bearbeiten, KI-Unterstützung auf Basis modulbezogener Datenschutz-Wissenskonfigurationen erhalten, Eingaben strukturiert gespeichert und validiert werden und Zweiplus die Ergebnisse prüfen sowie für spätere Zielsystem-Mappings freigeben kann.

---

# 8. Funktionale Anforderungen

## 8.1 Modulverwaltung

### FR-MOD-001: Module als konfigurierbare Einheiten

Das System muss Datenschutzprozesse als Module abbilden können.

Ein Modul enthält mindestens:

- Modul-ID,
- Name,
- Kurzbeschreibung,
- Ziel,
- Warum-Erklärung,
- zuständige Person oder Rolle,
- geschätzter Aufwand,
- kurzer Explainer,
- Steps,
- Fragen,
- Antworttypen,
- Validierungsregeln,
- KI-Wissenskonfiguration,
- Vorlagen,
- Output-Schema,
- Zielsystem-Mapping,
- Freischaltregeln,
- Bearbeitungsstatus.

### FR-MOD-002: Modul-Erklärtext

Für jedes Modul muss ein erklärender Einstieg hinterlegt werden können.

Bestandteile:

- Ziel,
- Warum,
- Wer,
- Aufwand,
- kurzer Explainer.

Beispiel:

- Ziel: Erfassung der eingesetzten Softwarelösungen.
- Warum: Die Angaben werden benötigt, um datenschutzrelevante Systeme und mögliche Auftragsverarbeiter zu erkennen.
- Wer: Auszufüllen durch IT-Verantwortliche oder Geschäftsführung.
- Aufwand: Ca. 10–20 Minuten.
- Explainer: Bitte geben Sie alle Systeme an, in denen personenbezogene Daten verarbeitet werden.

### FR-MOD-003: Modulreihenfolge

Die Bearbeitungsreihenfolge von Modulen muss konfigurierbar sein.

Das System muss unterstützen:

- lineare Reihenfolge,
- gesperrte Module,
- abhängige Freischaltung,
- parallele Freischaltung mehrerer Module,
- Freischaltung nach Abschluss bestimmter Module,
- manuelle Freischaltung durch Zweiplus.

### FR-MOD-004: Gesperrte Module

Noch nicht freigeschaltete Module müssen im Dashboard sichtbar, aber deaktiviert dargestellt werden.

Darstellung:

- ausgegraut,
- Schloss-Symbol,
- Hinweis, wodurch das Modul freigeschaltet wird.

### FR-MOD-005: Parallele Module

Das System muss erlauben, dass mehrere Module parallel bearbeitet werden können.

Dies ist erforderlich, wenn Module unabhängig voneinander sind oder unterschiedliche Personen Informationen liefern können.

### FR-MOD-006: Zuständigkeit je Modul

Für jedes Modul muss festgelegt und sichtbar angezeigt werden können, wer es bearbeiten soll.

Beispiele:

- Geschäftsführung,
- IT-Verantwortlicher,
- Personalabteilung,
- externer Dienstleister,
- Steuerberater,
- Zweiplus.

---

## 8.2 Step-Verwaltung innerhalb von Modulen

### FR-STEP-001: Module bestehen aus mehreren Steps

Jedes Modul muss aus einem oder mehreren Steps bestehen können.

Ein Step enthält mindestens:

- Step-ID,
- Titel,
- Beschreibung,
- Reihenfolge,
- Fragen,
- Pflichtfelder,
- Vorlagen,
- Status,
- Validierungsergebnis.

### FR-STEP-002: Step-Status

Jeder Step muss einen Status besitzen.

Mögliche Status:

- nicht gestartet,
- in Bearbeitung,
- unvollständig,
- vollständig,
- KI-Prüfung offen,
- Backend-Validierung fehlgeschlagen,
- durch Zweiplus zu prüfen,
- abgeschlossen.

### FR-STEP-003: Abhaken abgeschlossener Steps

Vollständig bearbeitete Steps müssen in der UI abgehakt werden.

Ein Step gilt als abgeschlossen, wenn:

- alle Pflichtfragen beantwortet wurden,
- alle technischen Backend-Validierungen erfolgreich sind,
- keine blockierenden Fehler offen sind,
- erforderliche Prüfungen abgeschlossen sind.

### FR-STEP-004: Progressanzeige pro Modul

Jedes Modul muss eine Fortschrittsanzeige besitzen.

Der Fortschritt soll sich primär aus abgeschlossenen Steps ergeben.

Beispiel:

- 2 von 5 Steps abgeschlossen = 40 % Fortschritt.

---

## 8.3 Fragen und Antworttypen

### FR-Q-001: Fragen als konfigurierbare Einheiten

Fragen müssen über eine QuestionDefinition abbildbar sein.

Eine Frage enthält mindestens:

- Frage-ID,
- Label,
- Beschreibung,
- Antworttyp,
- Pflichtfeldstatus,
- Optionen, falls Auswahlfrage,
- Hilfetext,
- KI-Hilfe aktiv/inaktiv,
- Validierungsregeln,
- Wissenskontext,
- Sichtbarkeitslogik,
- Abhängigkeiten zu anderen Fragen.

### FR-Q-002: Unterstützte Antworttypen

Das System muss mindestens folgende Antworttypen unterstützen:

- Einfachauswahl,
- Mehrfachauswahl,
- Textantwort,
- Dateiupload.

### FR-Q-003: Einfachauswahl

Bei Einfachauswahlfragen kann genau eine Option gewählt werden.

Beispiele:

- Ja / Nein,
- Branche,
- Unternehmensgröße,
- zuständiger Bereich.

### FR-Q-004: Mehrfachauswahl

Bei Mehrfachauswahlfragen können mehrere Optionen gewählt werden.

Beispiele:

- eingesetzte Software,
- Datenkategorien,
- betroffene Personengruppen,
- Empfängergruppen.

### FR-Q-005: Textantwort

Textantworten ermöglichen freie Angaben durch Nutzer.

Die KI kann Textantworten unterstützen, indem sie:

- Begriffe erklärt,
- Formulierungsvorschläge macht,
- Freitext in strukturierte Werte überführt,
- unklare Aussagen markiert,
- Rückfragen vorschlägt.

### FR-Q-006: Dateiupload

Fragen müssen Dateiuploads ermöglichen.

Unterstützte Upload-Arten:

- Bilder,
- Dokumente.

Beispiele:

- PDF-Dokumente,
- Word-Dokumente,
- Screenshots,
- Bilder,
- bestehende Verträge,
- Datenschutzerklärungen,
- TOM-Dokumente,
- Fragebogen-Rückläufe.

### FR-Q-007: Sichtbarkeitslogik

Fragen sollen abhängig von vorherigen Antworten ein- oder ausgeblendet werden können.

Beispiel:

Wenn die Frage „Nutzen Sie externe Dienstleister?“ mit „Nein“ beantwortet wird, müssen Detailfragen zu Dienstleistern nicht angezeigt werden.

---

## 8.4 Dashboard

### FR-DASH-001: Modulübersicht

Das Dashboard muss alle für den jeweiligen Kunden oder Prozess relevanten Module anzeigen.

Pro Modul müssen sichtbar sein:

- Modulname,
- Kurzbeschreibung,
- Status,
- Fortschritt,
- zuständige Person oder Rolle,
- gesperrt/freigeschaltet,
- nächste Aktion,
- geschätzter Aufwand.

### FR-DASH-002: Modulstatus

Das Dashboard muss den Status jedes Moduls anzeigen.

Mögliche Status:

- gesperrt,
- verfügbar,
- nicht gestartet,
- in Bearbeitung,
- wartet auf Kunde,
- wartet auf externe Information,
- wartet auf Zweiplus,
- KI-Prüfung offen,
- Backend-Validierung fehlgeschlagen,
- abgeschlossen,
- importbereit,
- importiert.

### FR-DASH-003: Zuständigkeit sichtbar machen

Für jedes Modul muss klar ersichtlich sein, wer es bearbeiten muss.

### FR-DASH-004: Allgemeiner KI-Chatbot

Auf der Dashboardseite muss ein allgemeiner KI-Chatbot verfügbar sein.

Dieser Chatbot dient für:

- allgemeine Fragen zum Onboarding,
- Orientierung im Prozess,
- Erklärung der nächsten Schritte,
- Erklärung gesperrter Module,
- allgemeine Datenschutzfragen,
- Hinweise auf zuständige Personen oder offene Aufgaben.

Der Dashboard-KI-Chatbot ist von modulbezogenen KI-Assistenten zu unterscheiden.

---

## 8.5 Modulbezogene KI-Unterstützung

### FR-AI-001: KI-Hilfe pro Modul, Step und Frage

Für Module, Steps und einzelne Fragen kann KI-Unterstützung aktiviert werden.

Die KI kann:

- den Zweck eines Moduls erklären,
- konkrete Fragen erklären,
- Beispiele nennen,
- typische Antworten vorschlagen,
- bisherige Angaben berücksichtigen,
- hochgeladene Dokumente berücksichtigen,
- branchenspezifische Hinweise geben,
- Rückfragen vorschlagen.

### FR-AI-002: Modulbezogene KI-Wissenskonfiguration

Jedes Modul muss eine eigene KI-Wissenskonfiguration besitzen können.

Diese legt fest, welches Wissen die KI für dieses Modul verwenden soll.

Konfigurierbar sein sollen insbesondere:

- allgemeines Datenschutzwissen,
- modulbezogenes Datenschutzwissen,
- feldbezogene Erklärungen,
- interne Zweiplus-Vorgaben,
- branchenspezifische Hinweise,
- DPMS-Feldlogik oder Zielsystemlogik,
- Beispielantworten,
- Negativbeispiele,
- typische Rückfragen,
- zulässige Wissensquellen.

### FR-AI-003: Wissen auf Modul-, Step- und Fragenebene

Die KI-Wissenskonfiguration soll auf mehreren Ebenen möglich sein:

- Modulebene: Grundwissen für das gesamte Modul,
- Stepebene: zusätzliches Wissen für einen bestimmten Abschnitt,
- Fragenebene: spezifisches Wissen zur Erklärung, Beantwortung oder Prüfung einer konkreten Frage.

Beispiel:

Eine Frage zur Löschfrist benötigt anderes Wissen als eine Frage zu Dienstleistern oder TOMs.

### FR-AI-004: Kontextabhängige KI-Antworten

Die KI muss abhängig von Modul, Step, Frage, bisherigen Antworten und hinterlegtem Wissen kontextbezogen antworten.

Beispiel:

Wenn ein Nutzer im Software-Modul Microsoft 365 und Lexware angegeben hat, kann die KI kontextbezogen vorschlagen, welche weiteren Angaben zu Software, Dienstleisterrolle oder Datenverarbeitung relevant sein könnten.

### FR-AI-005: Strukturierter KI-Output

Die KI muss strukturierte Outputs erzeugen können.

Der Output muss maschinell weiterverarbeitbar sein, beispielsweise als JSON.

Die KI-Ausgabe gilt nicht als finale Wahrheit, sondern als Vorschlag, der im Backend validiert und bei Bedarf durch Zweiplus geprüft wird.

### FR-AI-006: Semantische KI-Validierung

Die KI soll Eingaben semantisch prüfen.

Beispiele:

- Passt die Antwort zur Frage?
- Ist die Antwort plausibel?
- Fehlen offensichtliche Angaben?
- Gibt es Widersprüche zu vorherigen Antworten?
- Ist die Antwort zu allgemein?
- Sollte eine Rückfrage gestellt werden?
- Kann die Antwort in das Output-Schema normalisiert werden?

### FR-AI-007: Keine finale Freigabe durch KI

Die KI darf keine finale rechtliche oder fachliche Freigabe ersetzen.

Kritische Ergebnisse müssen durch Backend-Validierung und bei Bedarf durch Zweiplus-Review abgesichert werden.

---

## 8.6 Backend-Validierung

### FR-VAL-001: Technische Validierung

Das Backend muss alle Eingaben und KI-Ausgaben technisch validieren.

Prüfkriterien:

- JSON ist syntaktisch valide,
- Schema wird eingehalten,
- Pflichtfelder sind vorhanden,
- Datentypen stimmen,
- erlaubte Werte werden eingehalten,
- IDs existieren,
- Dateitypen sind erlaubt,
- Uploadgrößen werden eingehalten,
- Statusübergänge sind erlaubt,
- Nutzer ist berechtigt.

### FR-VAL-002: Fachlich deterministische Validierung

Neben der technischen Prüfung soll das Backend fachliche Regeln prüfen können.

Beispiele:

- Pflichtfelder je Modul vollständig,
- abhängige Felder korrekt ausgefüllt,
- Auswahlwerte in Zielsystem-Katalog vorhanden,
- Importfähigkeit gegeben,
- keine bekannten Widersprüche nach festen Regeln,
- erforderliche Vorlagen oder Dokumente vorhanden, falls Pflicht.

### FR-VAL-003: Trennung von KI- und Backend-Validierung

Die KI-Validierung ist unterstützend und semantisch.

Die Backend-Validierung ist verbindlich und deterministisch.

Beispiel:

Die KI kann erkennen, dass eine Löschfrist vermutlich unklar formuliert ist. Das Backend prüft anschließend, ob die normalisierte Löschfrist dem erwarteten Schema entspricht.

---

## 8.7 Vorlagen für externe Informationsbeschaffung

### FR-TPL-001: Vorlagen pro Modul oder Step

Das System muss ermöglichen, auf Modul- oder Step-Ebene Vorlagen zu hinterlegen.

Unterstützte Vorlagenarten im MVP:

- E-Mail-Vorlagen,
- Fragebogen-Dateien,
- erklärende Begleittexte.

### FR-TPL-002: E-Mail-Vorlagen

E-Mail-Vorlagen sollen genutzt werden können, um Informationen bei externen Personen einzuholen.

Eine E-Mail-Vorlage kann enthalten:

- Betreff,
- Nachrichtentext,
- Platzhalter,
- Bezug zum Modul oder Step,
- Hinweis auf benötigte Informationen,
- Verweis auf angehängte Fragebogen-Dateien.

Beispiel-Platzhalter:

- Kundenname,
- Modulname,
- Stepname,
- zuständige Person,
- Frist,
- Rücksendeadresse,
- Name des Fragebogens.

### FR-TPL-003: Fragebogen-Dateien

Fragebogen-Dateien müssen pro Modul oder Step hinterlegbar sein.

Die Plattform soll diese Dateien ausgeben können, beispielsweise als Download.

Beispiele:

- Word-Fragebogen,
- PDF-Fragebogen,
- Excel-Fragebogen,
- Checkliste.

### FR-TPL-004: Ausgabe der Vorlagen

Nutzer sollen Vorlagen im jeweiligen Step oder Modul verwenden können.

Im MVP reicht:

- E-Mail-Text anzeigen,
- E-Mail-Text kopieren,
- Fragebogen-Datei herunterladen,
- Begleittext anzeigen.

Nicht erforderlich im MVP:

- automatischer E-Mail-Versand,
- externe Bearbeitungslinks,
- Rücklaufverfolgung.

### FR-TPL-005: Verknüpfung mit Antworten

Wenn ein Nutzer Informationen extern eingeholt hat, muss er die erhaltene Antwort wieder im Modul erfassen können.

Dies kann erfolgen durch:

- Textantwort,
- Dateiupload,
- Auswahlfelder,
- manuelle Übertragung in Fragen.

---

## 8.8 Dokumenten- und Dateiverarbeitung

### FR-DOC-001: Upload von Bildern und Dokumenten

Nutzer müssen Dateien zu Fragen, Steps oder Modulen hochladen können.

### FR-DOC-002: Sichere Speicherung von Dateien

Dateien müssen sicher gespeichert und mit der jeweiligen Modulinstanz, dem Step oder der Frage verknüpft werden.

### FR-DOC-003: Dokumentenanalyse durch KI

Hochgeladene Dokumente können durch die KI analysiert werden, sofern dies für das jeweilige Modul aktiviert ist.

Mögliche Ergebnisse:

- erkannte relevante Informationen,
- extrahierte Textstellen,
- Vorschläge für Antworten,
- erkannte Lücken,
- Rückfragen,
- Hinweise für Zweiplus.

### FR-DOC-004: Nachvollziehbarkeit von KI-Vorschlägen

Bei KI-Vorschlägen aus Dokumenten soll nachvollziehbar sein, aus welchem Dokument oder welcher Eingabe ein Vorschlag abgeleitet wurde.

---

## 8.9 Review und Freigabe

### FR-REV-001: Review durch Zweiplus

Zweiplus muss Eingaben und KI-Vorschläge prüfen können.

Reviewer können:

- Vorschläge akzeptieren,
- Vorschläge bearbeiten,
- Vorschläge ablehnen,
- Rückfragen stellen,
- Module zur Korrektur zurückgeben,
- Module freigeben.

### FR-REV-002: Änderungsverlauf

Das System sollte nachvollziehen können:

- wer eine Antwort gegeben hat,
- wann sie gegeben wurde,
- ob sie durch KI vorgeschlagen wurde,
- ob sie aus einem Dokument abgeleitet wurde,
- ob sie manuell geändert wurde,
- wer sie freigegeben hat.

### FR-REV-003: Importfreigabe

Daten dürfen erst nach definierter Freigabe in Zielsysteme importiert oder für den Import final bereitgestellt werden.

---

## 8.10 Zielsystem-Mapping und DPMS-Integration

### FR-INT-001: Kanonisches Zwischenmodell

Die Plattform muss Daten zunächst in einem eigenen strukturierten Zwischenmodell speichern.

Dieses Modell ist unabhängig vom konkreten Zielsystem.

### FR-INT-002: Zielsystem-Adapter

Die Übertragung an Zielsysteme muss über Adapter erfolgen.

Der erste relevante Zielsystem-Adapter ist ein DPMS-Adapter.

### FR-INT-003: Mapping auf DPMS REST JSON

Der DPMS-Adapter muss validierte Daten in ein DPMS-kompatibles JSON-Format mappen können.

### FR-INT-004: Importvorschau

Das System soll eine Importvorschau bereitstellen können.

Diese zeigt:

- welche Objekte importiert werden,
- welche Felder gemappt wurden,
- welche Felder nicht gemappt werden konnten,
- welche Warnungen bestehen,
- welche Fehler bestehen,
- welches Zielsystem verwendet wird.

### FR-INT-005: Importstatus

Das System muss den Importstatus speichern.

Mögliche Status:

- nicht vorbereitet,
- Mapping bereit,
- validiert,
- freigegeben,
- Import läuft,
- importiert,
- Import fehlgeschlagen,
- erneuter Import erforderlich.

### FR-INT-006: Fehlerbehandlung

Fehler beim Zielsystem-Import müssen verständlich angezeigt und protokolliert werden.

---

# 9. UI-Anforderungen

## 9.1 Dashboard-Screen

Der Dashboard-Screen zeigt:

- Begrüßung und Kontext des Onboardings,
- allgemeine Fortschrittsübersicht,
- alle relevanten Module,
- Status je Modul,
- Zuständigkeit je Modul,
- gesperrte und freigeschaltete Module,
- nächste empfohlene Aktion,
- allgemeinen KI-Chatbot.

## 9.2 Modulkarte im Dashboard

Eine Modulkarte zeigt:

- Modulname,
- kurzer Explainer,
- Status,
- Fortschritt,
- zuständige Person oder Rolle,
- geschätzten Aufwand,
- Schloss-Symbol bei gesperrten Modulen,
- Hinweis zur Freischaltung,
- Call-to-Action, z. B. „Starten“, „Fortsetzen“, „Warten auf Prüfung“.

## 9.3 Modul-Startscreen

Der Modul-Startscreen zeigt:

- Modulname,
- Ziel,
- Warum,
- Wer,
- Aufwand,
- kurzer Explainer,
- Bearbeitungsstatus,
- Start- oder Fortsetzen-Button,
- optional verfügbare Vorlagen.

## 9.4 Modul-Bearbeitungsscreen

Der Modul-Bearbeitungsscreen zeigt:

- Step-Navigation,
- abgehakte abgeschlossene Steps,
- aktuellen Step,
- Progressbalken,
- Fragen,
- Antwortfelder,
- KI-Hilfe pro Frage,
- Uploadmöglichkeiten,
- verfügbare Vorlagen im Step,
- Validierungshinweise,
- Speichern-/Weiter-Button.

## 9.5 Vorlagenanzeige im Step

Wenn für einen Step Vorlagen hinterlegt sind, sollen diese klar sichtbar dargestellt werden.

Beispiel:

- „E-Mail-Vorlage an IT-Dienstleister kopieren“
- „Fragebogen herunterladen“
- „Begleittext anzeigen“

## 9.6 Review-Screen für Zweiplus

Der Review-Screen zeigt:

- Kundendaten,
- Modulstatus,
- Antworten,
- KI-Vorschläge,
- KI-Validierungen,
- Backend-Validierungen,
- offene Rückfragen,
- Änderungsmöglichkeiten,
- Freigabeoption,
- Importvorschau.

---

# 10. KI-Konzept

## 10.1 KI-Kontexte

Die Plattform unterscheidet mehrere KI-Kontexte:

- Dashboard-KI,
- Modul-KI,
- Step-KI,
- Fragen-KI,
- Prüf-KI.

## 10.2 Dashboard-KI

Die Dashboard-KI beantwortet allgemeine Fragen zum Onboarding.

Beispiele:

- „Was muss ich als Nächstes tun?“
- „Warum ist dieses Modul gesperrt?“
- „Wer muss dieses Modul ausfüllen?“
- „Was bedeutet Auftragsverarbeitung?“
- „Welche Unterlagen sollte ich bereithalten?“

## 10.3 Modul-KI

Die Modul-KI unterstützt innerhalb eines konkreten Moduls.

Sie nutzt die für dieses Modul definierte KI-Wissenskonfiguration.

Beispiele:

- erklärt den Zweck des Moduls,
- erklärt fachliche Datenschutzbegriffe,
- gibt Beispiele,
- schlägt Antworten vor,
- berücksichtigt bisherige Antworten,
- berücksichtigt hochgeladene Dokumente,
- prüft Eingaben semantisch.

## 10.4 Step-KI

Die Step-KI unterstützt innerhalb eines bestimmten Abschnitts.

Beispiele:

- erklärt, was in diesem Step erledigt werden soll,
- weist auf benötigte Unterlagen hin,
- erklärt, wann externe Informationen benötigt werden,
- hilft beim Nutzen von Vorlagen.

## 10.5 Fragen-KI

Die Fragen-KI arbeitet direkt an einer einzelnen Frage.

Beispiele:

- „Was ist mit Datenkategorien gemeint?“
- „Welche Antwort passt auf Basis meiner bisherigen Angaben?“
- „Kannst du meine Antwort besser formulieren?“
- „Ist diese Antwort ausreichend?“

## 10.6 Prüf-KI

Die Prüf-KI analysiert Eingaben semantisch.

Sie prüft:

- Plausibilität,
- Vollständigkeit,
- Widersprüche,
- fehlende Rückfragen,
- mögliche Normalisierung,
- unklare Formulierungen.

## 10.7 Strukturierter Output

KI-Ausgaben sollen, wenn sie für die Weiterverarbeitung relevant sind, strukturiert erfolgen.

Beispielhaftes Format:

```json
{
  "suggestionType": "answer_normalization",
  "moduleId": "software_inventory",
  "stepId": "software_usage",
  "questionId": "used_software",
  "proposedValue": {
    "software": ["Microsoft 365", "Lexware"],
    "notes": "Nutzer gibt an, Microsoft 365 und Lexware für Rechnungsprozesse zu verwenden."
  },
  "confidence": 0.82,
  "requiresReview": true,
  "openQuestions": ["Wird Lexware lokal oder cloudbasiert genutzt?"]
}
```

---

# 11. Modulbezogene KI-Wissenskonfiguration

## 11.1 Zweck

Jedes Modul benötigt eine fachlich passende Wissensbasis, damit die KI nicht allgemein, sondern kontextbezogen unterstützen kann.

Die Wissenskonfiguration legt fest, welches Datenschutzwissen, welche internen Vorgaben und welche Zielsysteminformationen der KI zur Verfügung stehen.

## 11.2 Inhalte einer Wissenskonfiguration

Eine KI-Wissenskonfiguration kann enthalten:

- allgemeines Datenschutzwissen,
- modulbezogenes Datenschutzwissen,
- rechtliche Grundlagen und Begriffe,
- feldbezogene Erklärungen,
- interne Zweiplus-Leitlinien,
- branchenspezifische Hinweise,
- Zielsysteminformationen, z. B. DPMS-Feldlogik,
- Beispielantworten,
- Negativbeispiele,
- typische Rückfragen,
- Validierungshinweise,
- erlaubte Wissensquellen.

## 11.3 Beispiel: TOM-Modul

```json
{
  "moduleId": "tom_erfassung",
  "aiKnowledgeConfig": {
    "privacyKnowledge": [
      "tom_basics",
      "technical_organizational_measures",
      "access_control",
      "backup_and_recovery",
      "encryption",
      "logging",
      "incident_response"
    ],
    "internalKnowledge": [
      "zweiplus_tom_review_guideline",
      "zweiplus_customer_question_style"
    ],
    "fieldKnowledge": [
      "tom_security_measure_examples",
      "tom_evidence_requirements"
    ]
  }
}
```

## 11.4 Beispiel: AVV-Modul

```json
{
  "moduleId": "avv_onboarding",
  "aiKnowledgeConfig": {
    "privacyKnowledge": [
      "processor_controller_distinction",
      "subprocessor_requirements",
      "processing_subject_matter",
      "processing_duration",
      "data_subjects",
      "data_categories",
      "technical_organizational_measures"
    ],
    "internalKnowledge": [
      "zweiplus_avv_review_guideline",
      "dpms_avv_mapping_rules"
    ]
  }
}
```

## 11.5 Beispiel: Frageebene

```json
{
  "questionId": "retention_period",
  "label": "Wie lange werden die Daten gespeichert?",
  "aiKnowledgeConfig": {
    "requiredKnowledge": [
      "retention_period_basics",
      "legal_retention_obligations",
      "deletion_concepts",
      "dpms_delete_period_fields"
    ],
    "answerGuidance": "Erkläre dem Nutzer den Unterschied zwischen gesetzlicher Aufbewahrung, interner Löschfrist und tatsächlicher Löschroutine.",
    "validationFocus": [
      "Ist die Antwort als Zeitraum interpretierbar?",
      "Ist ein Startpunkt für die Frist erkennbar?",
      "Ist die Antwort zu allgemein?"
    ]
  }
}
```

---

# 12. Datenmodell auf hoher Ebene

Die Plattform sollte mindestens folgende Kernobjekte enthalten.

## 12.1 ProcessDefinition

Beschreibt einen gesamten Onboarding-Prozess.

Beispiele:

- Datenschutz-Basis-Onboarding,
- VVT-Onboarding,
- AVV-Onboarding,
- TOM-Onboarding.

## 12.2 ProcessInstance

Konkrete Durchführung eines Prozesses für einen Kunden.

## 12.3 ModuleDefinition

Beschreibt ein Modul mit Steps, Fragen, Texten, KI-Wissenskonfiguration, Regeln, Vorlagen und Mapping.

## 12.4 ModuleInstance

Konkrete Bearbeitung eines Moduls innerhalb eines Kundenprozesses.

## 12.5 StepDefinition

Beschreibt einen Schritt innerhalb eines Moduls.

## 12.6 StepInstance

Konkreter Bearbeitungsstatus eines Steps.

## 12.7 QuestionDefinition

Beschreibt eine Frage, ihren Antworttyp, Hilfetext, Validierungsregeln und KI-Kontext.

## 12.8 Answer

Speichert die konkrete Antwort eines Nutzers.

## 12.9 FileUpload

Speichert Metadaten zu hochgeladenen Dateien.

## 12.10 TemplateDefinition

Beschreibt eine Vorlage, beispielsweise E-Mail-Text oder Fragebogen-Datei.

## 12.11 AiKnowledgeConfig

Beschreibt, welches Wissen der KI für Modul, Step oder Frage zur Verfügung steht.

## 12.12 AiSuggestion

Speichert KI-generierte Vorschläge.

## 12.13 AiValidationResult

Speichert Ergebnisse der semantischen KI-Prüfung.

## 12.14 BackendValidationResult

Speichert Ergebnisse der technischen und deterministischen Backend-Prüfung.

## 12.15 ReviewTask

Speichert Prüfaufgaben für Zweiplus.

## 12.16 CanonicalOutput

Speichert den strukturierten, zielsystemunabhängigen Output eines Moduls.

## 12.17 TargetMapping

Beschreibt, wie ein kanonischer Output in ein Zielsystemformat übersetzt wird.

## 12.18 ImportJob

Speichert Importvorgänge in Zielsysteme wie DPMS.

---

# 13. Beispiel für eine Moduldefinition

```json
{
  "moduleId": "software_inventory",
  "name": "Software-Erfassung",
  "intro": {
    "goal": "Erfassung der eingesetzten Softwarelösungen.",
    "why": "Die Angaben werden benötigt, um datenschutzrelevante Systeme, Dienstleister und mögliche Auftragsverarbeitungen zu erkennen.",
    "who": "IT-Verantwortliche oder Geschäftsführung.",
    "effort": "Ca. 10–20 Minuten.",
    "explainer": "Bitte geben Sie alle Systeme an, in denen personenbezogene Daten verarbeitet werden."
  },
  "aiKnowledgeConfig": {
    "privacyKnowledge": [
      "software_privacy_basics",
      "processor_definitions",
      "data_processing_systems",
      "third_country_transfer_basics"
    ],
    "internalKnowledge": ["zweiplus_software_inventory_guideline"],
    "targetSystemKnowledge": [
      "dpms_software_mapping",
      "dpms_subcontractor_mapping"
    ]
  },
  "steps": [
    {
      "stepId": "basic_information",
      "title": "Grunddaten",
      "description": "Bitte geben Sie an, welche Softwarelösungen verwendet werden.",
      "templates": [
        {
          "templateId": "software_vendor_email",
          "type": "email",
          "title": "E-Mail an Softwareanbieter",
          "subject": "Rückfragen zum Datenschutz-Onboarding",
          "body": "Sehr geehrte Damen und Herren,\n\nfür unser Datenschutz-Onboarding benötigen wir einige Angaben zu Ihrer Softwarelösung..."
        },
        {
          "templateId": "software_vendor_questionnaire",
          "type": "file",
          "title": "Fragebogen Softwareanbieter",
          "fileType": "docx"
        }
      ],
      "questions": [
        {
          "questionId": "used_software",
          "label": "Welche Softwarelösungen werden verwendet?",
          "type": "multi_select",
          "required": true,
          "options": [
            "Microsoft 365",
            "DATEV",
            "Lexware",
            "HubSpot",
            "Sonstige"
          ],
          "aiHelpEnabled": true,
          "knowledgeScope": ["software_privacy_basics", "processor_definitions"]
        },
        {
          "questionId": "additional_notes",
          "label": "Gibt es weitere Hinweise zur Nutzung dieser Software?",
          "type": "text",
          "required": false,
          "aiHelpEnabled": true
        },
        {
          "questionId": "software_contract_upload",
          "label": "Bitte laden Sie vorhandene Verträge oder Dokumente zur Software hoch.",
          "type": "file_upload",
          "required": false,
          "allowedFileTypes": ["pdf", "docx", "png", "jpg"]
        }
      ]
    }
  ],
  "outputSchema": "software_inventory_canonical_v1",
  "targetMappings": ["dpms_v1"]
}
```

---

# 14. Nicht-funktionale Anforderungen

## 14.1 Erweiterbarkeit

Das System muss so aufgebaut sein, dass neue Module ohne grundlegende Änderung der Gesamtarchitektur ergänzt werden können.

Neue Module sollen definieren können:

- Steps,
- Fragen,
- Antworttypen,
- KI-Wissenskonfiguration,
- Validierungsregeln,
- Vorlagen,
- Output-Schema,
- Zielsystem-Mapping,
- Freischaltlogik,
- Zuständigkeiten.

## 14.2 Datenschutz und Sicherheit

Die Plattform verarbeitet sensible Unternehmens- und Datenschutzinformationen.

Daher gelten folgende Anforderungen:

- Authentifizierung für Nutzer,
- rollenbasierte Zugriffe,
- sichere Dateispeicherung,
- Verschlüsselung bei Übertragung,
- Protokollierung wichtiger Aktionen,
- Trennung von Kundendaten,
- keine ungeprüfte KI-Übertragung in Zielsysteme,
- minimale Datenweitergabe an KI-Dienste,
- datenschutzkonforme KI-Nutzung,
- perspektivisch selbst hostbare KI-Komponenten oder datenschutzkonforme Modellanbieter.

## 14.3 Nachvollziehbarkeit

Das System muss nachvollziehbar machen:

- welche Daten vom Nutzer stammen,
- welche Daten durch KI vorgeschlagen wurden,
- welche Daten aus Dokumenten extrahiert wurden,
- welche Daten manuell bearbeitet wurden,
- welche Daten freigegeben wurden,
- welche Daten importiert wurden.

## 14.4 Usability

Die Plattform muss für fachfremde Nutzer verständlich sein.

Dazu gehören:

- klare Sprache,
- sichtbarer Fortschritt,
- kurze Erklärtexte,
- verständliche Fragen,
- KI-Hilfe direkt im Kontext,
- klare Zuständigkeiten,
- klare nächste Schritte,
- keine Überladung mit Datenschutzjargon.

## 14.5 Performance

Das System sollte für typische Onboarding-Prozesse flüssig nutzbar sein.

Längere Aufgaben wie Dokumentenanalyse, KI-Prüfung oder Zielsystem-Import sollten asynchron verarbeitet werden.

## 14.6 Wartbarkeit

Module, Fragen, Vorlagen und Wissenskonfigurationen sollen möglichst ohne Codeänderungen angepasst werden können.

---

# 15. Systemkontext

Die Plattform steht zwischen Nutzern, KI-Diensten und Zielsystemen.

```text
Kunde / Zweiplus
        ↓
Web-Frontend
        ↓
Backend / Modul-Engine
        ↓
KI-Service + Validierung + Review
        ↓
Kanonisches Datenmodell
        ↓
Zielsystem-Adapter
        ↓
DPMS oder andere Systeme
```

Die KI unterstützt innerhalb der Plattform. Sie schreibt nicht direkt in Zielsysteme.

---

# 16. Abgrenzung

Die Plattform soll nicht:

- das DPMS ersetzen,
- ausschließlich auf VVT beschränkt sein,
- Fragen und Prozesse hart im Frontend codieren,
- KI-Antworten ungeprüft übernehmen,
- rechtliche Freigaben automatisiert ohne Review treffen,
- externe Nutzer im MVP direkt im System arbeiten lassen,
- automatisch E-Mails im MVP versenden,
- vollständig bidirektional mit DPMS synchronisieren,
- alle Datenschutzprozesse bereits im MVP vollständig abbilden.

---

# 17. Risiken und offene Punkte

## 17.1 Offene fachliche Fragen

- Welches Modul wird als erstes Pilotmodul umgesetzt?
- Wie viele Module sollen im MVP enthalten sein?
- Welche Zielsystemobjekte sollen initial gemappt werden?
- Soll der DPMS-Import im MVP bereits automatisch erfolgen oder zunächst nur als JSON-/Importvorschau?
- Welche Rollen und Berechtigungen sind im MVP erforderlich?
- Welche Dateitypen müssen initial unterstützt werden?
- Welche KI-Modelle dürfen aus Datenschutzsicht verwendet werden?
- Welche Wissensbasis stellt Zweiplus bereit?
- Wer pflegt Moduldefinitionen, Vorlagen und Wissenskonfigurationen?
- Wie detailliert muss die Review-Funktion im MVP sein?

## 17.2 Technische Risiken

- KI-Ausgaben können unvollständig oder uneinheitlich sein.
- Zielsystem-Mapping kann komplexer werden als erwartet.
- DPMS-Katalogwerte und interne Antwortwerte müssen sauber gemappt werden.
- Dokumentenanalyse kann je nach Dateiformat fehleranfällig sein.
- Zu flexible Moduldefinitionen können die Implementierung verkomplizieren.
- Modulbezogene KI-Wissenskonfigurationen müssen sauber gepflegt werden.

## 17.3 Produktbezogene Risiken

- Nutzer könnten durch zu viele Module überfordert werden.
- KI-Hilfe darf nicht zu allgemein oder rechtlich zu verbindlich wirken.
- Zu viel Automatisierung ohne Review kann fachlich riskant sein.
- Wenn das System zu stark auf VVT optimiert wird, leidet die spätere Erweiterbarkeit.
- Vorlagen für externe Informationsbeschaffung müssen verständlich und aktuell gehalten werden.

---

# 18. Priorisierte Architekturprinzipien

Die folgenden Prinzipien sollten unabhängig vom finalen MVP gelten:

1. Module statt Einzelformulare.
2. Steps und Fragen sind konfigurierbar.
3. Antworttypen sind generisch.
4. Modulreihenfolge und parallele Bearbeitung sind konfigurierbar.
5. Zuständigkeiten sind immer sichtbar.
6. Jedes Modul besitzt einen erklärenden Einstieg.
7. KI-Hilfe ist pro Modul, Step und Frage kontextualisierbar.
8. Jedes Modul kann eigenes datenschutzrechtliches KI-Wissen definieren.
9. KI liefert strukturierte Vorschläge.
10. KI prüft semantisch, das Backend validiert verbindlich.
11. Daten werden in einem kanonischen Zwischenmodell gespeichert.
12. Zielsysteme werden über Adapter angebunden.
13. DPMS ist ein Zielsystem, nicht die Plattformlogik.
14. Review und Freigabe bleiben eigenständige Prozessschritte.
15. Vorlagen für externe Informationsbeschaffung sind pro Modul oder Step hinterlegbar.
16. Direkte externe Bearbeitung ist perspektivisch möglich, aber nicht Teil des MVP.
17. Die Plattform bleibt für weitere Datenschutzprozesse erweiterbar.

---

# 19. Zusammenfassung

Die geplante Anwendung ist eine modulare, KI-gestützte Onboarding-Plattform für Datenschutzprozesse. Sie führt Kunden durch konfigurierbare Module, die aus mehreren Steps und Fragen bestehen. Die Module können in einer definierten Reihenfolge oder parallel freigeschaltet werden. Für jedes Modul ist sichtbar, wer es bearbeiten soll, wie weit die Bearbeitung fortgeschritten ist und welche Schritte noch offen sind.

Die KI unterstützt Nutzer auf Dashboard-, Modul-, Step- und Fragenebene. Besonders wichtig ist, dass jedes Modul eine eigene KI-Wissenskonfiguration besitzen kann. Dadurch erhält die KI genau das datenschutzrechtliche Fachwissen, die internen Zweiplus-Vorgaben und die Zielsysteminformationen, die für das konkrete Modul relevant sind.

Die KI erzeugt strukturierte Vorschläge und prüft Eingaben semantisch. Die verbindliche technische und deterministische Validierung erfolgt im Backend. Nach Review und Freigabe werden die Daten in einem kanonischen Zwischenmodell gespeichert und können über Zielsystem-Adapter, insbesondere Richtung DPMS, weiterverarbeitet werden.

Der MVP soll bereits den Plattformgedanken abbilden. Er enthält Module, Steps, Antworttypen, Progressanzeige, KI-Unterstützung, modulbezogene Wissenskonfigurationen, Backend-Validierung, Review-Funktion und Vorlagen für externe Informationsbeschaffung. Externe Personen müssen im MVP noch nicht direkt in der Plattform mitarbeiten; es reicht, E-Mail-Vorlagen und Fragebogen-Dateien pro Modul oder Step bereitzustellen.

Der wichtigste Architekturgedanke bleibt die Erweiterbarkeit: Nicht VVT als Einzelfall steht im Zentrum, sondern eine wiederverwendbare Plattform für KI-gestützte Datenschutz-Onboardings.
