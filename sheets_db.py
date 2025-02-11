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
    except Exception as e:
        raise Exception(f"Failed to initialize Google Sheets client: {str(e)}")

def get_or_create_sheet():
    """Get or create the food database sheet."""
    try:
        client = get_sheets_client()
        
        # Try to open existing sheet
        try:
            sheet = client.open("Calorie Tracker Food Database").sheet1
        except gspread.SpreadsheetNotFound:
            # Create new sheet if it doesn't exist
            sheet = client.create("Calorie Tracker Food Database").sheet1
            
            # Set up headers
            headers = ['name', 'calories', 'protein', 'fat', 'carbs']
            sheet.insert_row(headers, 1)
            
            # Add some initial food items
            initial_data = [
                ['Chicken Breast', 165, 31, 3.6, 0],
                ['White Rice', 130, 2.7, 0.3, 28],
                ['Egg', 72, 6.3, 4.8, 0.4],
                ['Apple', 52, 0.3, 0.2, 14],
                ['Banana', 89, 1.1, 0.3, 23],
                ['Salmon', 208, 22, 13, 0]
            ]
            
            for row in initial_data:
                sheet.append_row(row)
        
        return sheet
    except Exception as e:
        raise Exception(f"Failed to get or create sheet: {str(e)}")

def get_all_foods():
    """Get all foods from the sheet as a pandas DataFrame."""
    try:
        sheet = get_or_create_sheet()
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        raise Exception(f"Failed to get foods from sheet: {str(e)}")

def add_food(food_data):
    """Add a new food item to the sheet."""
    try:
        sheet = get_or_create_sheet()
        row = [
            food_data['name'],
            food_data['calories'],
            food_data['protein'],
            food_data['fat'],
            food_data['carbs']
        ]
        sheet.append_row(row)
    except Exception as e:
        raise Exception(f"Failed to add food to sheet: {str(e)}")
