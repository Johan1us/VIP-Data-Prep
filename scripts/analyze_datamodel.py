import pandas as pd
import json
from pathlib import Path

def get_unique_import_names():
    """
    Read the Datamodel.xlsx file, extract unique values from ImportNaam column,
    and write them to a JSON file in the src/api directory.
    """
    try:
        # Construct paths
        file_path = Path(__file__).parent.parent / "data" / "datamodel_acceptatie" / "Datamodel.xlsx"
        json_path = Path(__file__).parent.parent / "src" / "api" / "objecttypes.json"

        # Check if Excel file exists
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return None

        # Read Excel file
        print(f"📖 Reading file: {file_path}")
        df = pd.read_excel(file_path)

        # Check if 'ImportNaam' column exists
        if 'ImportNaam' not in df.columns:
            print("❌ Column 'ImportNaam' not found in the Excel file")
            return None

        # Get unique values
        unique_values = df['ImportNaam'].unique()

        # Sort and remove any NaN values
        unique_values = sorted([str(val) for val in unique_values if pd.notna(val)])

        # Create JSON structure
        json_data = {
            "objectTypes": unique_values,
            "count": len(unique_values)
        }

        # Write to JSON file
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Found {len(unique_values)} unique import names:")
        print(f"💾 Written to: {json_path}\n")
        for val in unique_values:
            print(f"- {val}")

        return unique_values

    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")
        return None

if __name__ == "__main__":
    get_unique_import_names()
