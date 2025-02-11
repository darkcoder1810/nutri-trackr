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
            st.warning("No food items found in the database. Adding some default items...")
            df = pd.DataFrame({
                'name': ['Chicken Breast', 'White Rice', 'Egg'],
                'calories': [165, 130, 72],
                'protein': [31, 2.7, 6.3],
                'fat': [3.6, 0.3, 4.8],
                'carbs': [0, 28, 0.4]
            })
        return df
    except Exception as e:
        st.error(f"Error loading food database: {str(e)}")
        # Return a minimal DataFrame with the correct columns
        return pd.DataFrame(columns=['name', 'calories', 'protein', 'fat', 'carbs'])

def save_food_to_database(food_data: dict):
    """Save a new food item to the Google Sheet."""
    try:
        add_food(food_data)
        st.cache_data.clear()  # Clear cache to reload updated data
        return True
    except ValueError as ve:
        st.warning(str(ve))
        return False
    except Exception as e:
        st.error(f"Error saving food to database: {str(e)}")
        return False