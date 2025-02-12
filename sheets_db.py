import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd
import streamlit as st

def get_user_sheet():
    """Get the user data sheet."""
    try:
        client = get_sheets_client()
        try:
            spreadsheet = client.open("DB's Food Database")
            try:
                return spreadsheet.worksheet('Users')
            except:
                # Create Users sheet if it doesn't exist
                return spreadsheet.add_worksheet('Users', 1, 6)
        except Exception as e:
            st.error(f"Error accessing spreadsheet: {str(e)}")
            raise
    except Exception as e:
        st.error(f"Error getting user sheet: {str(e)}")
        raise

def save_user_info(user_data):
    """Save user information to the sheet."""
    try:
        sheet = get_user_sheet()
        # Check if headers exist
        headers = sheet.row_values(1)
        if not headers:
            headers = ['user_id', 'weight', 'calorie_mode', 'protein_per_kg', 'fat_percent', 'last_updated']
            sheet.append_row(headers)
            
        # Get user's row if exists
        user_id = st.session_state.get('user_id', None)
        if not user_id:
            import uuid
            user_id = str(uuid.uuid4())
            st.session_state['user_id'] = user_id
            
        user_row = None
        try:
            user_data_rows = sheet.get_all_records()
            for idx, row in enumerate(user_data_rows):
                if row.get('user_id') == user_id:
                    user_row = idx + 2  # +2 for 1-based index and header row
                    break
        except:
            pass
            
        # Prepare row data
        from datetime import datetime
        row_data = [
            user_id,
            user_data['weight'],
            user_data['calorie_mode'],
            user_data['protein_per_kg'],
            user_data['fat_percent'],
            datetime.now().isoformat()
        ]
        
        if user_row:
            # Update existing row
            for i, value in enumerate(row_data):
                sheet.update_cell(user_row, i + 1, value)
        else:
            # Add new row
            sheet.append_row(row_data)
            
        return True
    except Exception as e:
        st.error(f"Error saving user data: {str(e)}")
        return False

def load_user_info():
    """Load user information from the sheet."""
    try:
        sheet = get_user_sheet()
        user_id = st.session_state.get('user_id', None)
        if not user_id:
            return None
            
        user_data_rows = sheet.get_all_records()
        for row in user_data_rows:
            if row.get('user_id') == user_id:
                return {
                    'weight': float(row.get('weight', 70.0)),
                    'calorie_mode': row.get('calorie_mode', 'maintenance'),
                    'protein_per_kg': float(row.get('protein_per_kg', 2.0)),
                    'fat_percent': float(row.get('fat_percent', 0.25))
                }
        return None
    except Exception as e:
        st.error(f"Error loading user data: {str(e)}")
        return None

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
        # Get all values including headers
        all_values = sheet.get_all_values()
        if not all_values:
            st.error("Sheet appears to be empty")
            return False

        # Get header and data rows
        headers = all_values[0]
        data_rows = all_values[1:]

        # Find the food name column index (usually 0, but let's be sure)
        try:
            food_name_col = headers.index('Food Name')
        except ValueError:
            st.error("Could not find 'Food Name' column in sheet")
            return False

        # Search for the food item
        target_name = food_name.strip().lower()
        found_idx = None

        for idx, row in enumerate(data_rows):
            current_food = row[food_name_col].strip().lower()
            if current_food == target_name:
                found_idx = idx
                break

        if found_idx is not None:
            # Add 2 to account for 1-based indexing and header row
            row_to_delete = found_idx + 2
            sheet.delete_rows(row_to_delete)
            return True
        else:
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
            return pd.DataFrame()

        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=headers)

        return pd.DataFrame(data)
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

        sheet.append_row(row)
        return True

    except Exception as e:
        st.error(f"Error adding food to sheet: {str(e)}")
        raise