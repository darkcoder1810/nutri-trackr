import pandas as pd
from sheets_db import get_all_foods, add_food
import streamlit as st

def calculate_maintenance_calories(weight_kg):
    """Calculate maintenance calories based on weight."""
    # Basic calculation using weight in kg
    # Assuming moderate activity level and average height/age
    return weight_kg * 32

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_food_database():
    """Load the food database from Google Sheets."""
    try:
        df = get_all_foods()
        if df.empty:
            st.warning("No food items found in the database.")
            return pd.DataFrame(columns=['Food Name', 'Calories', 'Protein', 'Fat', 'Carbs'])

        # Ensure column names match exactly with the sheet
        # Map the column names to our expected format
        column_mapping = {
            'Food Name': ['Food Name', 'food name', 'name', 'Food'],
            'Calories': ['Calories', 'calories', 'kcal'],
            'Protein': ['Protein', 'protein', 'proteins'],
            'Fat': ['Fat', 'fat', 'fats'],
            'Carbs': ['Carbs', 'carbs', 'carbohydrates']
        }

        # Map columns to standardized names
        for std_name, possible_names in column_mapping.items():
            for col in df.columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    df = df.rename(columns={col: std_name})
                    break

        # Ensure all required columns exist
        required_columns = ['Food Name', 'Calories', 'Protein', 'Fat', 'Carbs']
        missing_columns = set(required_columns) - set(df.columns)

        if missing_columns:
            st.error(f"Missing required columns in sheet: {', '.join(missing_columns)}")
            return pd.DataFrame(columns=required_columns)

        # Convert numeric columns
        numeric_columns = ['Calories', 'Protein', 'Fat', 'Carbs']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    except Exception as e:
        st.error(f"Error loading food database: {str(e)}")
        return pd.DataFrame(columns=['Food Name', 'Calories', 'Protein', 'Fat', 'Carbs'])

def save_food_to_database(food_data: dict):
    """Save a new food item to the Google Sheet."""
    try:
        # Map the standardized names back to the sheet's format
        food_item = {
            'Food Name': food_data.get('name', ''),
            'Calories': food_data.get('calories', 0),
            'Protein': food_data.get('protein', 0),
            'Fat': food_data.get('fat', 0),
            'Carbs': food_data.get('carbs', 0)
        }

        add_food(food_item)
        st.cache_data.clear()  # Clear cache to reload updated data
        return True
    except ValueError as ve:
        st.warning(str(ve))
        return False
    except Exception as e:
        st.error(f"Error saving food to database: {str(e)}")
        return False