import pandas as pd
import json
from pathlib import Path


def maak_unieke_import_namen_json():
    """
    Deze functie leest uit twee specifieke Datamodel.xlsx-bestanden (productie en acceptatie)
    de unieke waarden uit de kolom 'ImportNaam'. Deze unieke waarden worden vervolgens
    gesorteerd en opgeslagen in aparte JSON-bestanden.

    Concreet:
    1. Bepaal de paden naar de twee Excel-bestanden (productie en acceptatie).
    2. Voor elk bestand:
       - Controleer of het bestand bestaat.
       - Lees het Excel-bestand in.
       - Controleer of de kolom 'ImportNaam' aanwezig is.
       - Haal alle unieke waarden uit 'ImportNaam'.
       - Sorteer en filter de waarden (verwijder lege/Nan waarden).
       - Schrijf de resultaten (inclusief aantal) naar een JSON-bestand.
    """

    try:
        # Basispad van het project: twee niveaus omhoog vanaf dit bestand
        # __file__ verwijst naar het huidige Python-bestand
        # parent.parent gaat twee niveaus omhoog naar de hoofdmap van het project
        basis_pad = Path(__file__).parent.parent

        # Definitie van de paden voor productie en acceptatie
        # We maken gebruik van een dictionary zodat we in een loop door de omgevingen kunnen itereren.
        omgeving_paden = {
            "productie": {
                "excel_pad": basis_pad / "data" / "datamodel_productie" / "Datamodel.xlsx",
                "json_pad": basis_pad / "src" / "api" / "objecttypes_productie.json"
            },
            "acceptatie": {
                "excel_pad": basis_pad / "data" / "datamodel_acceptatie" / "Datamodel.xlsx",
                "json_pad": basis_pad / "src" / "api" / "objecttypes_acceptatie.json"
            }
        }

        # Doorloop elke omgeving (productie, acceptatie)
        for omgeving, paden in omgeving_paden.items():
            excel_bestand = paden["excel_pad"]
            json_bestand = paden["json_pad"]

            # Controleer eerst of het Excel-bestand wel bestaat
            if not excel_bestand.exists():
                print(f"❌ Bestand niet gevonden: {excel_bestand}")
                continue

            # Lees het Excel-bestand in
            # Note: Dit kan enige tijd duren bij grote bestanden
            print(f"📖 Inlezen van: {excel_bestand}")
            df = pd.read_excel(excel_bestand)

            # Controleer of 'ImportNaam' kolom aanwezig is
            if 'ImportNaam' not in df.columns:
                print(f"❌ Kolom 'ImportNaam' niet gevonden in {excel_bestand}")
                continue

            # Haal de unieke waarden uit de kolom 'ImportNaam'
            unieke_waarden = df['ImportNaam'].unique()

            # Filter op niet-lege waarden en maak er strings van
            # Daarna sorteren we de lijst alfabetisch
            unieke_waarden = sorted([str(waarde) for waarde in unieke_waarden if pd.notna(waarde)])

            # Maak een JSON-structuur met de gevonden objecttypes en hun aantal
            json_data = {
                "objectTypes": unieke_waarden,
                "count": len(unieke_waarden)
            }

            # Zorg ervoor dat de map voor het JSON-bestand bestaat
            json_bestand.parent.mkdir(parents=True, exist_ok=True)

            # Schrijf de data weg als JSON, met netjes ingesprongen tekst
            with open(json_bestand, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            # Toon in de console een overzicht van wat er is aangetroffen en weggeschreven
            print(f"\n✅ Gevonden {len(unieke_waarden)} unieke importnamen voor {omgeving}:")
            print(f"💾 Weggeschreven naar: {json_bestand}\n")
            for waarde in unieke_waarden:
                print(f"- {waarde}")

    except Exception as e:
        # Als er iets fout gaat, print het foutbericht
        print(f"❌ Fout bij het verwerken van bestanden: {str(e)}")


if __name__ == "__main__":
    maak_unieke_import_namen_json()
