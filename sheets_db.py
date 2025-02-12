import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd
import streamlit as st

def get_sheets_client():
    """Initialize and return Google Sheets client."""
    try:
        # Load credentials from environment variable
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_json:
            raise ValueError("Google Sheets credentials not found in environment")

        credentials_dict = json.loads(creds_json)

        # Define the scope - explicitly include both APIs
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]

        # Authorize with credentials
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        client = gspread.authorize(creds)

        # Test the connection by listing spreadsheets
        try:
            client.list_spreadsheet_files()
        except Exception as e:
            if "PERMISSION_DENIED" in str(e):
                st.error("Google Drive API access denied. Please ensure the API is enabled in Google Cloud Console.")
            raise

        return client
    except json.JSONDecodeError:
        st.error("Invalid JSON format in Google Sheets credentials")
        raise
    except Exception as e:
        st.error(f"Error initializing sheets client: {str(e)}")
        raise

def get_sheet():
    """Get the existing food database sheet."""
    try:
        client = get_sheets_client()

        try:
            sheet = client.open("DB's Food Database").sheet1
            # Test sheet access
            sheet.row_values(1)
            return sheet
        except gspread.SpreadsheetNotFound:
            st.error("Could not find the sheet 'DB's Food Database'. Please make sure the sheet exists and is shared with the service account.")
            raise
        except Exception as e:
            if "PERMISSION_DENIED" in str(e):
                st.error("Access denied to the sheet. Please ensure the sheet is shared with the service account email.")
            raise

    except Exception as e:
        st.error(f"Error accessing sheet: {str(e)}")
        raise

def delete_food(food_name: str) -> bool:
    """Delete a food item from the sheet."""
    try:
        sheet = get_sheet()
        # Get all food names
        food_names = sheet.col_values(1)[1:]  # Skip header and get food names

        # Normalize food names for comparison (strip whitespace and convert to lowercase)
        food_name = food_name.strip()
        normalized_food_names = [name.strip().lower() for name in food_names]
        normalized_search = food_name.lower()

        try:
            # Find the row index (add 2 because: +1 for header, +1 for 1-based index)
            row_idx = normalized_food_names.index(normalized_search) + 2
            sheet.delete_rows(row_idx)
            st.success(f"Successfully deleted {food_name} from database")
            return True
        except ValueError:
            st.error(f"Food item '{food_name}' not found in database")
            return False

    except Exception as e:
        st.error(f"Error deleting food from sheet: {str(e)}")
        return False

def get_all_foods():
    """Get all foods from the sheet as a pandas DataFrame."""
    try:
        sheet = get_sheet()
        # Get headers first to validate structure
        headers = sheet.row_values(1)
        if not headers:
            st.warning("Sheet appears to be empty. Please check if data exists.")
            return pd.DataFrame()

        data = sheet.get_all_records()
        if not data:
            st.warning("No data found in the sheet (only headers present)")
            return pd.DataFrame(columns=headers)

        df = pd.DataFrame(data)
        st.success(f"Successfully loaded {len(df)} food items from database")
        return df
    except Exception as e:
        st.error(f"Error loading foods from sheet: {str(e)}")
        return pd.DataFrame()

def add_food(food_data):
    """Add a new food item to the sheet."""
    try:
        sheet = get_sheet()
        # Get the column headers from the sheet
        headers = sheet.row_values(1)
        if not headers:
            st.error("Sheet headers not found")
            raise ValueError("Sheet headers not found")

        # Check if food already exists
        existing_foods = sheet.col_values(1)[1:]  # Get all food names except header
        if food_data['Food Name'].strip().lower() in [f.strip().lower() for f in existing_foods]:
            raise ValueError(f"Food item '{food_data['Food Name']}' already exists")

        # Create a row with values in the correct order based on sheet headers
        row = []
        for header in headers:
            value = None
            # Try different key formats
            key_variants = [
                header,
                header.lower(),
                header.replace(' ', '_').lower(),
                header.lower().replace(' ', '_')
            ]

            # First try exact matches
            for key in key_variants:
                if key in food_data:
                    value = food_data[key]
                    break

            # If no value found, try special cases
            if value is None:
                header_lower = header.lower()
                if header_lower == 'fat':
                    value = food_data.get('Fat', food_data.get('fat', 0))
                elif header_lower == 'category':
                    value = food_data.get('Category', food_data.get('category', 'veg'))
                elif header_lower == 'basis':
                    value = food_data.get('Basis', food_data.get('basis', 'gm'))

            row.append(value if value is not None else '')

        # Debug logging
        st.write(f"Adding row: {list(zip(headers, row))}")

        sheet.append_row(row)
        st.success(f"Successfully added {food_data['Food Name']} to database")
        return True

    except Exception as e:
        st.error(f"Error adding food to sheet: {str(e)}")
        raise