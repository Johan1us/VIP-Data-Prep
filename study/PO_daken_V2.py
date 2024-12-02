import pandas as pd
import logging
from typing import Optional, List, Dict
from src.api.luxs_api import LuxsAPI
from src.api_client import LuxsAcceptClient

logger = logging.getLogger(__name__)

class RoofManager:
    """Manager for roof-related data operations"""
    
    # Metadata definitions as class attributes
    METADATA = {
        'dakpartner': {
            "name": "Dakpartner - Building - Woonstad Rotterdam",
            "type": "STRING",
            "attributeValueOptions": [
                "Cazdak Dakbedekkingen BV",
                "Oranjedak West BV",
                "Voormolen Dakbedekkingen B.V."
            ],
        },
        'projectleider': {
            "name": "Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam",
            "type": "STRING",
            "attributeValueOptions": [
                "Jack Robbemond",
                "Anton Jansen"
            ],
        },
        'dakveiligheid': {
            "name": "Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam",
            "type": "BOOLEAN",
        },
        'antenne': {
            "name": "Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam",
            "type": "BOOLEAN",
        }
    }

    def __init__(self):
        """Initialize with API client"""
        client = LuxsAcceptClient()
        self.api = LuxsAPI(client)

    def get_all_buildings(self, page_size: int = 10000) -> Optional[List[Dict]]:
        """Fetch all buildings with roof-related attributes"""
        logger.info("Fetching all buildings...")
        
        # Define the attributes we want to retrieve
        attributes = [
            'Dakpartner - Building - Woonstad Rotterdam',
            'Jaar laatste dakonderhoud - Building - Woonstad Rotterdam',
            'Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam',
            'Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam',
            'Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam',
        ]

        buildings = self.api.get_objects_by_type(
            object_type='Building',
            attributes=attributes,
            page_size=page_size
        )

        if buildings:
            logger.info(f"Retrieved {len(buildings)} buildings")
            return buildings
        else:
            logger.error("Failed to retrieve buildings")
            return None

    def export_to_excel(self, data: List[Dict], filename: Optional[str] = None) -> bool:
        """Export building data to Excel with validation"""
        if not data:
            logger.error("No data to export")
            return False

        try:
            logger.info("Preparing data for Excel export...")
            
            # Create DataFrame
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

            # Generate filename if not provided
            if not filename:
                time = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                filename = f"roof_data_{time}.xlsx"

            # Create Excel writer
            writer = pd.ExcelWriter(filename, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Data')

            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Data']
            lookup_sheet = workbook.add_worksheet('Lookup_Lists')

            # Add validation lists
            self._add_validation_lists(workbook, lookup_sheet)
            
            # Add data validation to columns
            self._add_column_validation(worksheet, df, columns)

            writer.close()
            logger.info(f"Data exported successfully to {filename}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            return False

    def _add_validation_lists(self, workbook, lookup_sheet):
        """Add validation lists to the lookup sheet"""
        # Dakpartner options
        for row_num, option in enumerate(self.METADATA['dakpartner']['attributeValueOptions']):
            lookup_sheet.write(row_num, 0, option)
        workbook.define_name('DakpartnerList', 
                           f"='Lookup_Lists'!$A$1:$A${len(self.METADATA['dakpartner']['attributeValueOptions'])}")

        # Projectleider options
        for row_num, option in enumerate(self.METADATA['projectleider']['attributeValueOptions']):
            lookup_sheet.write(row_num, 1, option)
        workbook.define_name('ProjectleiderList', 
                           f"='Lookup_Lists'!$B$1:$B${len(self.METADATA['projectleider']['attributeValueOptions'])}")

        # Boolean options
        boolean_options = ['TRUE', 'FALSE']
        for row_num, option in enumerate(boolean_options):
            lookup_sheet.write(row_num, 2, option)
        workbook.define_name('BooleanList', f"='Lookup_Lists'!$C$1:$C${len(boolean_options)}")

    def _add_column_validation(self, worksheet, df, columns):
        """Add data validation to specific columns"""
        start_row = 1  # Skip header
        end_row = len(df) + 1

        # Add validation for Dakpartner
        dakpartner_col = columns.index('Dakpartner - Building - Woonstad Rotterdam')
        worksheet.data_validation(start_row, dakpartner_col, end_row, dakpartner_col, {
            'validate': 'list',
            'source': '=DakpartnerList'
        })

        # Add validation for Projectleider
        projectleider_col = columns.index('Betrokken Projectleider Techniek Daken - Building - Woonstad Rotterdam')
        worksheet.data_validation(start_row, projectleider_col, end_row, projectleider_col, {
            'validate': 'list',
            'source': '=ProjectleiderList'
        })

        # Add validation for boolean columns
        boolean_columns = [
            'Dakveiligheidsvoorzieningen aangebracht  - Building - Woonstad Rotterdam',
            'Antenne(opstelplaats) op dak  - Building - Woonstad Rotterdam'
        ]
        for col_name in boolean_columns:
            col_index = columns.index(col_name)
            worksheet.data_validation(start_row, col_index, end_row, col_index, {
                'validate': 'list',
                'source': '=BooleanList'
            })

def main():
    """Main execution function"""
    try:
        # Initialize roof manager
        roof_manager = RoofManager()

        # Fetch all buildings
        buildings = roof_manager.get_all_buildings()
        if not buildings:
            logger.error("No buildings to export")
            return False

        # Export to Excel
        success = roof_manager.export_to_excel(buildings)
        return success

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        return False

if __name__ == "__main__":
    # Setup colored logging
    import colorlog

    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s:%(name)s:%(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))

    logger = colorlog.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Run main function
    success = main()
    exit(0 if success else 1) 