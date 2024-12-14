import pytest
import os
import json
from VIP_DataMakelaar.app.utils.config_loader import ConfigLoader

@pytest.fixture
def test_config_dir(tmp_path):
    # Maak een tijdelijke config dir
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    # Schrijf een testconfig
    config_data = {
        "dataset": "PO Daken",
        "objectType": "Building",
        "attributes": [
            {
                "excelColumnName": "Dakpartner",
                "AttributeName": "Dakpartner - Building - Woonstad Rotterdam"
            }
        ]
    }
    config_path = config_dir / "po_daken.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f)

    return config_dir

def test_load_config(test_config_dir):
    loader = ConfigLoader(config_dir=str(test_config_dir))
    config = loader.load_config("po_daken")
    assert config["dataset"] == "PO Daken"
    assert config["objectType"] == "Building"
    assert len(config["attributes"]) == 1
    assert config["attributes"][0]["excelColumnName"] == "Dakpartner"
