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

def get_or_create_sheet():
    """Get or create the food database sheet."""
    try:
        client = get_sheets_client()

        # Try to open existing sheet
        try:
            sheet = client.open("Calorie Tracker Food Database").sheet1
        except gspread.SpreadsheetNotFound:
            # Create new sheet if it doesn't exist
            spreadsheet = client.create("Calorie Tracker Food Database")
            sheet = spreadsheet.sheet1

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
        print(f"Error getting or creating sheet: {str(e)}")
        raise

def get_all_foods():
    """Get all foods from the sheet as a pandas DataFrame."""
    try:
        sheet = get_or_create_sheet()
        data = sheet.get_all_records()
        if not data:
            # If sheet is empty (except headers), return DataFrame with initial data
            return pd.DataFrame({
                'name': ['Chicken Breast', 'White Rice', 'Egg'],
                'calories': [165, 130, 72],
                'protein': [31, 2.7, 6.3],
                'fat': [3.6, 0.3, 4.8],
                'carbs': [0, 28, 0.4]
            })
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error getting foods from sheet: {str(e)}")
        # Return empty DataFrame with correct columns as fallback
        return pd.DataFrame(columns=['name', 'calories', 'protein', 'fat', 'carbs'])

def add_food(food_data):
    """Add a new food item to the sheet."""
    try:
        sheet = get_or_create_sheet()
        # Check if food already exists
        existing_foods = sheet.col_values(1)[1:]  # Get all food names except header
        if food_data['name'] in existing_foods:
            raise ValueError(f"Food item '{food_data['name']}' already exists")

        row = [
            food_data['name'],
            food_data['calories'],
            food_data['protein'],
            food_data['fat'],
            food_data['carbs']
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Error adding food to sheet: {str(e)}")
        raise