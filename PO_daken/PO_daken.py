import requests
import json
from api_study.study import get_token  # Ensure this module is accessible and provides get_token()
import pandas as pd
import xlsxwriter


# Metadata definitions
metadata_dakpartner = {
    "name": "Dakpartner - Building - Woonstad Rotterdam",
    "type": "STRING",
    "attributeValueOptions": [
        "Cazdak Dakbedekkingen BV",
        "Oranjedak West BV",
        "Voormolen Dakbedekkingen B.V."
    ],
}

metadata_betrokken_projectleider_techniek_daken = {
    "name": "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam",
    "type": "STRING",
    "attributeValueOptions": [
        "Jack Robbemond",
        "Anton Jansen"
    ],
}

metadata_dakveiligheidsvoorzieningen_aangebracht = {
    "name": "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
    "type": "BOOLEAN",
}

metadata_antenne_opstelplaats_op_dak = {
    "name": "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
    "type": "BOOLEAN",
}


def get_all_buildings():
    """
    Fetches all buildings from the LUXS Accept API.

    Returns:
        list: Building data if successful, False otherwise
    """
    BUILDINGS_URL = "https://api.accept.luxsinsights.com/v1/objects/filterByObjectType"

    try:
        # Get token
        TOKEN = get_token()
        if not TOKEN:
            return False

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        }

        # Prepare request parameters
        params = {
            'objectType': 'Building',
            'pageSize': 10000
        }

        print("\n🔄 Fetching all buildings...")
        response = requests.get(BUILDINGS_URL, headers=headers, params=params)

        # Check if request was successful
        if response.status_code == 200:
            building_data = response.json()
            print("✅ Buildings retrieved successfully!")
            print(f"Amount of buildings is {len(building_data)}")
            return building_data
        else:
            print(f"❌ Building retrieval failed with status code: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def export_data_to_excel(data):
    """
    Export data to an Excel file with data validation for dropdown fields.

    Args:
        data (list): Data to export
    """
    print("\n📝 Exporting data to Excel file...")

    # Create a Pandas DataFrame from the data
    df = pd.DataFrame(data)
    df = pd.concat([df.drop(['attributes'], axis=1), df['attributes'].apply(pd.Series)], axis=1)

    # Keep only the columns we need
    columns = [
        'objectType',
        'identifier',
        'Dakpartner - Building - Woonstad Rotterdam',
        'Jaar laatste dakonderhoud - Building - Woonstad Rotterdam',
        'Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam',
        'Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam',
        'Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam',
    ]
    df = df[columns]

    # Generate unique filename
    time = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"data_{time}.xlsx"

    # Create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')

    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, index=False, sheet_name='Data')

    # Get the XlsxWriter workbook and worksheet objects.
    workbook = writer.book
    worksheet = writer.sheets['Data']

    # Create a sheet for lookup lists (unhide by not calling hide())
    lookup_sheet = workbook.add_worksheet('Lookup_Lists')

    # Write the options to the lookup sheet
    # Dakpartner options
    dakpartner_options = metadata_dakpartner["attributeValueOptions"]
    for row_num, option in enumerate(dakpartner_options):
        lookup_sheet.write(row_num, 0, option)
    dakpartner_list_range = f"'Lookup_Lists'!$A$1:$A${len(dakpartner_options)}"

    # Define named range for DakpartnerList (include '=' in the formula)
    workbook.define_name('DakpartnerList', f'={dakpartner_list_range}')

    # Projectleider options
    projectleider_options = metadata_betrokken_projectleider_techniek_daken["attributeValueOptions"]
    for row_num, option in enumerate(projectleider_options):
        lookup_sheet.write(row_num, 1, option)
    projectleider_list_range = f"'Lookup_Lists'!$B$1:$B${len(projectleider_options)}"

    # Define named range for ProjectleiderList
    workbook.define_name('ProjectleiderList', f'={projectleider_list_range}')

    # Boolean options
    boolean_options = ['TRUE', 'FALSE']
    for row_num, option in enumerate(boolean_options):
        lookup_sheet.write(row_num, 2, option)
    boolean_list_range = f"'Lookup_Lists'!$C$1:$C${len(boolean_options)}"

    # Define named range for BooleanList
    workbook.define_name('BooleanList', f'={boolean_list_range}')

    # Add data validation for Dakpartner column
    dakpartner_col = columns.index('Dakpartner - Building - Woonstad Rotterdam')
    start_row = 1  # Data starts from the second row (first row is header)
    end_row = len(df)

    worksheet.data_validation(start_row, dakpartner_col, start_row + end_row - 1, dakpartner_col, {
        'validate': 'list',
        'source': '=DakpartnerList'
    })

    # Add data validation for Projectleider column
    projectleider_col = columns.index('Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam')
    worksheet.data_validation(start_row, projectleider_col, start_row + end_row - 1, projectleider_col, {
        'validate': 'list',
        'source': '=ProjectleiderList'
    })

    # Add data validation for boolean columns
    boolean_columns = [
        'Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam',
        'Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam'
    ]
    for col_name in boolean_columns:
        col_index = columns.index(col_name)
        worksheet.data_validation(start_row, col_index, start_row + end_row - 1, col_index, {
            'validate': 'list',
            'source': '=BooleanList'
        })

    # Close the Pandas Excel writer and output the Excel file.
    writer.close()

    print(f"✅ Data saved successfully to {file_name} with dropdown validations!")


if __name__ == "__main__":
    # Fetch all buildings
    buildings = get_all_buildings()

    # Check if buildings were retrieved successfully
    if buildings:
        # Export data to Excel
        export_data_to_excel(buildings)
    else:
        print("No data to export.")
