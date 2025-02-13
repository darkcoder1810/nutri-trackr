import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd
import streamlit as st
from datetime import datetime
import pytz

# Prepare row data
ist_tz = pytz.timezone('Asia/Kolkata')  # Define the IST timezone


def get_user_sheet():
    """Get the user data sheet."""
    try:
        client = get_sheets_client()
        spreadsheet = client.open("DB's Food Database")

        # Get all worksheets
        worksheets = spreadsheet.worksheets()
        users_sheet = None

        # Look for existing Users sheet
        for worksheet in worksheets:
            if worksheet.title == 'Users':
                users_sheet = worksheet
                break

        # If Users sheet doesn't exist, create it
        if not users_sheet:
            users_sheet = spreadsheet.add_worksheet('Users', 1, 6)

        return users_sheet

    except Exception as e:
        st.error(f"Error getting user sheet: {str(e)}")
        raise


def save_user_info(user_data):
    """Save user information to the sheet."""
    try:
        sheet = get_user_sheet()
        headers = sheet.row_values(1)
        expected_headers = [
            'mobile', 'weight', 'calorie_mode', 'protein_per_kg',
            'fat_percent', 'last_updated'
        ]

        # Add headers if sheet is empty
        if not any(headers):
            sheet.append_row(expected_headers)

        # Get mobile number as user_id
        mobile = user_data.get('mobile') or st.session_state.get('mobile')
        if not mobile:
            raise ValueError("Mobile number is required")

        # Find existing user row
        all_rows = sheet.get_all_records()
        user_row = None
        for idx, row in enumerate(all_rows):
            if str(row.get('mobile', '')).strip() == str(mobile).strip():
                user_row = idx + 2  # +2 for header and 1-based index
                break

        # Prepare row data
        from datetime import datetime
        row_data = [
            mobile, user_data['weight'], user_data['calorie_mode'],
            user_data['protein_per_kg'], user_data['fat_percent'],
            datetime.now(ist_tz).isoformat()
        ]

        if user_row:
            # Update existing row
            for i, value in enumerate(row_data):
                sheet.update_cell(user_row, i + 1, value)
        else:
            # Add new row
            sheet.append_row(row_data)

        return True
    except ValueError as e:
        st.error(f"Error saving user data: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Error saving user data: {str(e)}")
        return False


def load_user_info():
    """Load user information from the sheet."""
    try:
        sheet = get_user_sheet()
        mobile = st.session_state.get('mobile', None)
        if not mobile:
            return None

        user_data_rows = sheet.get_all_records()
        # Filter rows for current user and sort by last_updated
        user_rows = [
            row for row in user_data_rows
            if str(row.get('mobile', '')).strip() == str(mobile).strip()
        ]
        if not user_rows:
            return None

        # Sort by last_updated and get the most recent entry
        latest_row = sorted(user_rows,
                            key=lambda x: x.get('last_updated', ''),
                            reverse=True)[0]
        return {
            'weight': float(latest_row.get('weight', 70.0)),
            'calorie_mode': latest_row.get('calorie_mode', 'maintenance'),
            'protein_per_kg': float(latest_row.get('protein_per_kg', 2.0)),
            'fat_percent': float(latest_row.get('fat_percent', 0.25))
        }
    except Exception as e:
        st.error(f"Error loading user data: {str(e)}")
        return None


def get_sheets_client():
    """Initialize and return Google Sheets client."""
    try:
        # Load credentials from environment variable
        creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_json:
            raise ValueError(
                "Google Sheets credentials not found in environment")

        credentials_dict = json.loads(creds_json)

        # Define the scope - explicitly include both APIs
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]

        # Authorize with credentials
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, scope)
        client = gspread.authorize(creds)

        # Test the connection by listing spreadsheets
        try:
            client.list_spreadsheet_files()
        except Exception as e:
            if "PERMISSION_DENIED" in str(e):
                st.error(
                    "Google Drive API access denied. Please ensure the API is enabled in Google Cloud Console."
                )
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
            st.error(
                "Could not find the sheet 'DB's Food Database'. Please make sure the sheet exists and is shared with the service account."
            )
            raise
        except Exception as e:
            if "PERMISSION_DENIED" in str(e):
                st.error(
                    "Access denied to the sheet. Please ensure the sheet is shared with the service account email."
                )
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
        existing_foods = sheet.col_values(1)[
            1:]  # Get all food names except header
        if food_data['Food Name'].strip().lower() in [
                f.strip().lower() for f in existing_foods
        ]:
            raise ValueError(
                f"Food item '{food_data['Food Name']}' already exists")

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
                    value = food_data.get('Category',
                                          food_data.get('category', 'veg'))
                elif header_lower == 'basis':
                    value = food_data.get('Basis',
                                          food_data.get('basis', 'gm'))

            row.append(value if value is not None else '')

        sheet.append_row(row)
        return True

    except Exception as e:
        st.error(f"Error adding food to sheet: {str(e)}")
        raise


def get_daily_log_sheet():
    """Get the daily log sheet."""
    try:
        client = get_sheets_client()
        spreadsheet = client.open("DB's Food Database")

        # Get all worksheets
        worksheets = spreadsheet.worksheets()
        log_sheet = None

        # Look for existing Daily Logs sheet
        for worksheet in worksheets:
            if worksheet.title == 'Daily Logs':
                log_sheet = worksheet
                break

        # If Daily Logs sheet doesn't exist, create it with headers
        if not log_sheet:
            log_sheet = spreadsheet.add_worksheet('Daily Logs', 1, 11)
            headers = [
                'Mobile', 'Timestamp', 'Meal Type', 'Weight', 'Basis',
                'Food Name', 'Category', 'Calories', 'Protein', 'Carbs', 'Fat'
            ]
            log_sheet.append_row(headers)

        return log_sheet
    except Exception as e:
        st.error(f"Error getting daily log sheet: {str(e)}")
        raise


def save_meal_log(meal_data):
    """Save meal log to the sheet."""
    try:
        sheet = get_daily_log_sheet()

        ist_time = datetime.now(ist_tz)  # Get current time in IST

        row_data = [
            meal_data['mobile'],
            ist_time.isoformat(),  # Use the IST timestamp
            meal_data['meal_type'],
            meal_data['weight'],
            meal_data['basis'],
            meal_data['food_name'],
            meal_data['category'],
            meal_data['calories'],
            meal_data['protein'],
            meal_data['carbs'],
            meal_data['fat']
        ]

        sheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Error saving meal log: {str(e)}")
        return False


def get_daily_logs(mobile, date=None):
    """Get daily logs for a specific mobile number and optional date."""
    try:
        sheet = get_daily_log_sheet()
        records = sheet.get_all_records()

        # Filter by mobile
        logs = [r for r in records if str(r['Mobile']) == str(mobile)]

        # Convert and format timestamps
        for log in logs:
            dt = datetime.fromisoformat(log['Timestamp'])
            log['Date'] = dt.strftime('%d-%m-%Y')
            log['Time'] = dt.strftime('%H:%M')
            log['Timestamp'] = dt

        # Filter by date if provided
        if date:
            logs = [r for r in logs if log['Date'] == date]

        return sorted(logs, key=lambda x: x['Timestamp'])
    except Exception as e:
        st.error(f"Error getting daily logs: {str(e)}")
        return []


def delete_logs_by_date(mobile, date):
    """Delete all logs for a specific mobile number and date."""
    try:
        sheet = get_daily_log_sheet()
        records = sheet.get_all_records()
        all_values = sheet.get_all_values()
        headers = all_values[0]

        # Find rows to delete
        rows_to_delete = []
        for idx, record in enumerate(
                records, start=2):  # Start from 2 to account for headers
            if (str(record['Mobile']) == str(mobile)
                    and record['Timestamp'].split('T')[0] == date):
                rows_to_delete.append(idx)

        # Delete rows in reverse order to maintain correct indices
        for row in sorted(rows_to_delete, reverse=True):
            sheet.delete_rows(row)

        return True
    except Exception as e:
        st.error(f"Error deleting logs: {str(e)}")
        return False


def get_daily_summaries(mobile):
    """Get daily summaries of calorie intake."""
    try:
        logs = get_daily_logs(mobile)
        summaries = {}

        for log in logs:
            date = log[
                'Date']  # Using the already formatted date from get_daily_logs
            if date not in summaries:
                summaries[date] = {
                    'total_calories': 0,
                    'total_protein': 0,
                    'total_carbs': 0,
                    'total_fat': 0
                }

            summaries[date]['total_calories'] += log['Calories']
            summaries[date]['total_protein'] += log['Protein']
            summaries[date]['total_carbs'] += log['Carbs']
            summaries[date]['total_fat'] += log['Fat']

        return [{'date': k, **v} for k, v in summaries.items()]
    except Exception as e:
        st.error(f"Error getting daily summaries: {str(e)}")
        return []
