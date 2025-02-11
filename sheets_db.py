import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd

def get_sheets_client():
    """Initialize and return Google Sheets client."""
    try:
        # Load credentials from environment variable
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_json:
            raise ValueError("Google Sheets credentials not found in environment")

        credentials_dict = json.loads(creds_json)

        # Define the scope
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']

        # Authorize with credentials
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        client = gspread.authorize(creds)

        return client
    except json.JSONDecodeError:
        raise Exception("Invalid JSON format in Google Sheets credentials")
    except Exception as e:
        print(f"Error initializing sheets client: {str(e)}")
        raise

def get_sheet():
    """Get the existing food database sheet."""
    try:
        client = get_sheets_client()

        # Try to open existing sheet
        try:
            # Update the sheet name to match the user's existing sheet
            sheet = client.open("DB's Food Database").sheet1
            return sheet
        except gspread.SpreadsheetNotFound:
            raise Exception("Could not find the sheet 'DB's Food Database'. Please make sure the sheet exists and is shared with the service account.")

    except Exception as e:
        print(f"Error getting sheet: {str(e)}")
        raise

def get_all_foods():
    """Get all foods from the sheet as a pandas DataFrame."""
    try:
        sheet = get_sheet()
        data = sheet.get_all_records()
        if not data:
            raise ValueError("No data found in the sheet")
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error getting foods from sheet: {str(e)}")
        # Return empty DataFrame with correct columns as fallback
        return pd.DataFrame()

def add_food(food_data):
    """Add a new food item to the sheet."""
    try:
        sheet = get_sheet()
        # Get the column headers from the sheet
        headers = sheet.row_values(1)

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
        return True
    except Exception as e:
        print(f"Error adding food to sheet: {str(e)}")
        raise