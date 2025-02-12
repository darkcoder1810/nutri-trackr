import pandas as pd
from sheets_db import get_all_foods, add_food
import streamlit as st


def calculate_calories(weight_kg: float, mode: str = 'maintenance') -> float:
    """Calculate calories based on weight and selected mode."""
    maintenance = weight_kg * 28.6  # Base calculation

    if mode == 'bulk':
        return maintenance * 1.15  # 15% surplus
    elif mode == 'deficit':
        return maintenance * 0.85  # 15% deficit
    return maintenance  # maintenance calories


def calculate_macros(target_calories: float, protein_per_kg: float,
                     fat_percent: float, weight_kg: float) -> tuple:
    """Calculate macros based on target calories and custom ratios."""
    # Calculate protein based on weight
    protein = weight_kg * protein_per_kg

    # Calculate fat based on percentage of total calories
    fat = (target_calories * fat_percent) / 9

    # Calculate remaining calories for carbs
    remaining_calories = target_calories - (protein * 4) - (fat * 9)
    carbs = remaining_calories / 4

    return protein, fat, carbs


def calculate_calories_from_macros(protein: float, fat: float,
                                   carbs: float) -> float:
    """Calculate calories from macronutrients using the 4-4-9 rule."""
    return (protein * 4) + (fat * 9) + (carbs * 4)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_food_database():
    """Load the food database from Google Sheets."""
    try:
        df = get_all_foods()
        if df.empty:
            return pd.DataFrame(columns=[
                'Food Name', 'Calories', 'Protein', 'Fat', 'Carbs', 'Weight',
                'Basis', 'Category', 'Fibre', 'Avg Weight', 'Source'
            ])

        # Map column names to standardized format
        column_mapping = {
            'Food Name': ['Food Name', 'food name', 'name', 'Food'],
            'Calories': ['Calories', 'calories', 'kcal'],
            'Protein': ['Protein', 'protein', 'proteins'],
            'Fat': ['Fat', 'fat', 'fats'],
            'Carbs': ['Carbs', 'carbs', 'carbohydrates'],
            'Weight': ['Weight', 'weight'],
            'Basis': ['Basis', 'basis', 'unit'],
            'Category': ['Category', 'Veg/Non-Veg', 'veg_nonveg'],
            'Fibre': ['Fibre', 'Fiber', 'fibre', 'fiber'],
            'Avg Weight': ['Avg Weight', 'avg_weight', 'average weight'],
            'Source': ['Source', 'source']
        }

        # Map columns to standardized names
        for std_name, possible_names in column_mapping.items():
            for col in df.columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    df = df.rename(columns={col: std_name})
                    break

        # Ensure all required columns exist
        required_columns = [
            'Food Name', 'Calories', 'Protein', 'Fat', 'Carbs', 'Weight',
            'Basis', 'Category'
        ]
        missing_columns = set(required_columns) - set(df.columns)

        if missing_columns:
            return pd.DataFrame(columns=required_columns)

        # Convert numeric columns
        numeric_columns = ['Calories', 'Protein', 'Fat', 'Carbs', 'Fibre']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    except Exception as e:
        st.error(f"Error loading food database: {str(e)}")
        return pd.DataFrame(columns=[
            'Food Name', 'Calories', 'Protein', 'Fat', 'Carbs', 'Weight',
            'Basis', 'Category', 'Fibre', 'Avg Weight', 'Source'
        ])


def food_exists_in_database(food_name: str) -> bool:
    """Check if a food item already exists in the database."""
    df = load_food_database()
    if 'Food Name' not in df.columns:
        return False
    return food_name.lower() in df['Food Name'].str.lower().values


def save_food_to_database(food_data: dict):
    """Save a new food item to the Google Sheet."""
    try:
        # Calculate calories from macros if not provided
        if 'Calories' not in food_data or not food_data['Calories']:
            food_data['Calories'] = calculate_calories_from_macros(
                float(food_data.get('Protein', 0)),
                float(food_data.get('Fat', 0)),
                float(food_data.get('Carbs', 0)))

        # Check if food already exists
        if food_exists_in_database(food_data.get('Food Name', '')):
            st.warning(
                f"Food item '{food_data.get('Food Name')}' already exists in the database"
            )
            return False

        add_food(food_data)
        st.cache_data.clear()  # Clear cache to reload updated data
        return True
    except Exception as e:
        st.error(f"Error saving food to database: {str(e)}")
        return False
