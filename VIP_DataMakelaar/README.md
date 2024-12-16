# VIP DataMakelaar

De **VIP DataMakelaar** is een interne tool om datasets vanuit het Vastgoed Informatie Programma (VIP) op een gestructureerde manier te beheren. Met deze tool kun je eenvoudig data downloaden, lokaal bewerken in Excel, valideren en vervolgens terugzetten naar VIP. Hierdoor houd je de data actueel, foutvrij en consistent.

## Inhoudsopgave

1. [Overzicht](#overzicht)
2. [Functionaliteiten](#functionaliteiten)
3. [Installatie & Vereisten](#installatie--vereisten)
4. [Configuratie](#configuratie)
5. [Gebruik](#gebruik)
6. [Veelvoorkomende Problemen](#veelvoorkomende-problemen)
7. [Onderhoud & Uitbreiding](#onderhoud--uitbreiding)
8. [Contact & Support](#contact--support)

## Overzicht

De VIP DataMakelaar is vooral bedoeld voor medewerkers die regelmatig data uit VIP moeten aanpassen, verrijken of corrigeren. Het doel is om dit proces zo eenvoudig mogelijk te maken:

- Download datasets als Excel
- Pas ze lokaal aan met ingebouwde validatie (dropdowns, datumnotaties, verplichte velden, etc.)
- Upload de gewijzigde data
- Laat de app de data valideren
- Stuur de goedgekeurde data terug naar VIP

Dit bespaart tijd, voorkomt fouten en zorgt voor consistente data in het VIP-systeem.

## Functionaliteiten

- **Inloggen (optioneel):** Alleen geautoriseerde gebruikers krijgen toegang tot de tool.
- **Dataset Selectie:** Kies uit een lijst van datasets welke je wilt bijwerken.
- **Download als Excel:** Ontvang een Excel-bestand met vooraf ingestelde validatieregels (datumformaten, dropdowns voor toegestane waarden, etc.).
- **Bewerken in Excel:** Pas de data lokaal aan. Alle validatieregels zijn meteen zichtbaar in de spreadsheet.
- **Upload & Validatie:** Upload de bijgewerkte Excel terug. De app checkt automatisch of de data aan alle eisen voldoet.
- **Doorvoeren in VIP:** Is de dataset goedgekeurd? Met één klik stuur je deze terug naar VIP.

## Installatie & Vereisten

- **Python:** Versie 3.9 of hoger aanbevolen.
- **Streamlit:** Voor het draaien van de webinterface.
- **Andere afhankelijkheden:** Zie `requirements.txt`.

**Stappen om te starten:**
1. Clone deze repository:
   `git clone [repository_url] && cd vip-datamakelaar`
2. Installeer afhankelijkheden:
   `pip install -r requirements.txt`
3. Start de app:
```bash
streamlit run app/main.py
```
4.

Open vervolgens de link die Streamlit toont in je browser (meestal http://localhost:8501).

## Configuratie

In de map `config/` staan JSON-bestanden per dataset. Deze bestanden bevatten enkel de mapping van Excel-kolomnamen naar VIP-attributenamen. De app haalt alle overige informatie (zoals datatypes, toegestane waarden en datumformaten) dynamisch uit de VIP-API. Hierdoor hoef je de config-bestanden nauwelijks te updaten als er iets verandert in de metadata.

**Werkwijze:**
- Voeg voor een nieuwe dataset een nieuw JSON-bestand toe in `config/`.
- Geef de dataset een naam, het bijbehorende `objectType` en voor elke kolom een `excelColumnName` en `AttributeName`.
- De app doet de rest!

## Gebruik

**Stapsgewijze workflow:**
1. **Inloggen (indien nodig):** Start de app en log in.
2. **Dataset kiezen:** Selecteer de gewenste dataset in de app.
3. **Download Excel:** Klik op de downloadknop. Je krijgt een Excel-bestand dat al voorzien is van validatieregels.
4. **Data bewerken:** Open het Excel-bestand in bijvoorbeeld Microsoft Excel. Pas hier waarden aan, voeg nieuwe rijen toe of corrigeer data. Dankzij dropdowns en datumformaten is de kans op fouten kleiner.
5. **Upload:** Ga terug naar de app en upload de aangepaste Excel.
6. **Validatie:** De app controleert direct of alles klopt. Fouten? Pas de Excel aan en upload opnieuw.
7. **Doorvoeren in VIP:** Is alles in orde, klik dan op de knop om de data naar VIP te sturen. Je krijgt een bevestiging wanneer dit geslaagd is.

## Veelvoorkomende Problemen

- **Kan niet inloggen:** Controleer of je de juiste inloggegevens hebt. Neem anders contact op met de beheerder.
- **Upload faalt:** Controleer of je Excel nog in het juiste format is. Heb je kolomnamen aangepast of ongewenste data ingevoegd? Herstel dit en upload opnieuw.
- **Enumeraties kloppen niet:** Mogelijk is de metadata veranderd. Start de app opnieuw om de laatste metadata op te halen.

## Onderhoud & Uitbreiding

- **Aanpassen Validatieregels:** Dit gaat via de VIP-API. De app haalt deze informatie dynamisch op.
- **Nieuwe Datasets:** Voeg een nieuwe config in `config/` toe, met de juiste mapping. Geen codeaanpassingen nodig!
- **Tests:** In `app/tests/` vind je voorbeeldtests. Deze kun je runnen om de betrouwbaarheid van de code te waarborgen.

## Contact & Support

- Voor technische vragen kun je terecht bij het interne IT-team.
- Voor inhoudelijke vragen over de data, neem contact op met de data-beheerders.
- Issue melden? Doe dit via het interne ticketsysteem of meld het direct bij de beheerder.
