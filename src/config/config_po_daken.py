METADATA_DAKEN = {
    "dakpartner": {
        "name": "Dakpartner - Building - Woonstad Rotterdam",
        "type": "STRING",
        "attributeValueOptions": [
            "Cazdak Dakbedekkingen BV",
            "Oranjedak West BV",
            "Voormolen Dakbedekkingen B.V.",
        ],
    },
    "projectleider": {
        "name": "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam",
        "type": "STRING",
        "attributeValueOptions": ["Jack Robbemond", "Anton Jansen"],
    },
    "dakveiligheid": {
        "name": "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
        "type": "BOOLEAN",
    },
    "antenne": {
        "name": "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
        "type": "BOOLEAN",
    },
    "jaar_laatste_dakonderhoud": {
        "name": "Jaar laatste dakonderhoud - Building - Woonstad Rotterdam",
        "type": "STRING",  # We slaan het als string op, ook al is het jaartal
    }
}

# Mapping van Excel kolom naar interne keys in METADATA_DAKEN:
COLUMNS_MAPPING_DAKEN = {
    "identifier": "identifier",
    "Dakpartner - Building - Woonstad Rotterdam": "dakpartner",
    "Jaar laatste dakonderhoud - Building - Woonstad Rotterdam": "jaar_laatste_dakonderhoud",
    "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam": "projectleider",
    "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam": "dakveiligheid",
    "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam": "antenne"
}
