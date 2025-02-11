import pandas as pd
import os

def calculate_maintenance_calories(weight_kg):
    """Calculate maintenance calories based on weight."""
    # Basic calculation using weight in kg
    # Assuming moderate activity level and average height/age
    return weight_kg * 32

def load_food_database():
    """Load the food database from CSV file."""
    if not os.path.exists('data/food_database.csv'):
        # Create initial database with some common foods
        initial_data = {
            'name': ['Chicken Breast', 'White Rice', 'Egg', 'Apple', 'Banana', 'Salmon'],
            'calories': [165, 130, 72, 52, 89, 208],
            'protein': [31, 2.7, 6.3, 0.3, 1.1, 22],
            'fat': [3.6, 0.3, 4.8, 0.2, 0.3, 13],
            'carbs': [0, 28, 0.4, 14, 23, 0]
        }
        df = pd.DataFrame(initial_data)
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/food_database.csv', index=False)
    return pd.read_csv('data/food_database.csv')

def save_food_database(df):
    """Save the food database to CSV file."""
    df.to_csv('data/food_database.csv', index=False)
