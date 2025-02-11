import pandas as pd
import os
from models import FoodItem, get_db
from sqlalchemy.orm import Session

def calculate_maintenance_calories(weight_kg):
    """Calculate maintenance calories based on weight."""
    # Basic calculation using weight in kg
    # Assuming moderate activity level and average height/age
    return weight_kg * 32

def load_food_database():
    """Load the food database from PostgreSQL."""
    db = next(get_db())
    foods = db.query(FoodItem).all()

    if not foods:
        # Create initial database with some common foods
        initial_data = {
            'name': ['Chicken Breast', 'White Rice', 'Egg', 'Apple', 'Banana', 'Salmon'],
            'calories': [165, 130, 72, 52, 89, 208],
            'protein': [31, 2.7, 6.3, 0.3, 1.1, 22],
            'fat': [3.6, 0.3, 4.8, 0.2, 0.3, 13],
            'carbs': [0, 28, 0.4, 14, 23, 0]
        }

        # Add initial foods to database
        for i in range(len(initial_data['name'])):
            food_item = FoodItem(
                name=initial_data['name'][i],
                calories=initial_data['calories'][i],
                protein=initial_data['protein'][i],
                fat=initial_data['fat'][i],
                carbs=initial_data['carbs'][i]
            )
            db.add(food_item)
        db.commit()
        foods = db.query(FoodItem).all()

    # Convert to DataFrame for compatibility with existing code
    return pd.DataFrame([{
        'name': food.name,
        'calories': food.calories,
        'protein': food.protein,
        'fat': food.fat,
        'carbs': food.carbs
    } for food in foods])

def save_food_to_database(food_data: dict):
    """Save a new food item to the database."""
    db = next(get_db())
    food_item = FoodItem(**food_data)
    db.add(food_item)
    db.commit()
    return food_item