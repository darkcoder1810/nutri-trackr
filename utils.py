import pandas as pd
from sheets_db import get_all_foods, add_food

def calculate_maintenance_calories(weight_kg):
    """Calculate maintenance calories based on weight."""
    # Basic calculation using weight in kg
    # Assuming moderate activity level and average height/age
    return weight_kg * 32

def load_food_database():
    """Load the food database from Google Sheets."""
    try:
        return get_all_foods()
    except Exception as e:
        # If there's an error, return an empty DataFrame with the correct columns
        return pd.DataFrame(columns=['name', 'calories', 'protein', 'fat', 'carbs'])

def save_food_to_database(food_data: dict):
    """Save a new food item to the Google Sheet."""
    add_food(food_data)
    return True