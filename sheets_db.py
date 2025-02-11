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
            # Update the sheet name to match the user's existing sheet
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
        if food_data['name'] in existing_foods:
            raise ValueError(f"Food item '{food_data['name']}' already exists")

        # Create a row with values in the correct order based on sheet headers
        row = []
        for header in headers:
            # Convert header to lowercase for case-insensitive matching
            header_key = header.lower().replace(' ', '_')
            # Try to get the value using various possible key formats
            value = food_data.get(header_key) or food_data.get(header.lower()) or food_data.get(header) or ''
            row.append(value)

        sheet.append_row(row)
        st.success(f"Successfully added {food_data['name']} to database")
        return True
    except Exception as e:
        st.error(f"Error adding food to sheet: {str(e)}")
        raise