import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import (
    calculate_maintenance_calories, 
    load_food_database, 
    save_food_to_database,
    calculate_calories_from_macros,
    food_exists_in_database
)

# Page configuration
st.set_page_config(page_title="Calorie Tracker", layout="wide")

# Load custom CSS
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state
if 'daily_log' not in st.session_state:
    st.session_state.daily_log = {
        'breakfast': [],
        'lunch': [],
        'snacks': [],
        'dinner': []
    }

# Load food database
food_db = load_food_database()

# Main title
st.title("🥗 Calorie & Macro Tracker")

# Sidebar for user info and goals
with st.sidebar:
    st.header("User Information")
    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)

    maintenance_calories = calculate_maintenance_calories(weight)
    st.write(f"Maintenance Calories: {maintenance_calories:.0f} kcal")

    # Daily goals
    st.header("Daily Goals")
    calorie_goal = st.number_input("Calorie Goal", min_value=1200.0, max_value=5000.0, value=float(maintenance_calories), step=50.0)
    protein_goal = st.number_input("Protein Goal (g)", min_value=30.0, max_value=300.0, value=float(weight * 2), step=5.0)
    fat_goal = st.number_input("Fat Goal (g)", min_value=20.0, max_value=200.0, value=float(calorie_goal * 0.25 / 9), step=5.0)
    carb_goal = st.number_input("Carb Goal (g)", min_value=50.0, max_value=500.0, value=float((calorie_goal - (protein_goal * 4 + fat_goal * 9)) / 4), step=5.0)

# Add new food to database
st.header("Add New Food to Database")
with st.expander("Add New Food"):
    # Food name with instant search
    new_food_name = st.text_input("Food Name")
    if new_food_name and food_exists_in_database(new_food_name):
        st.warning(f"'{new_food_name}' already exists in the database")

    col1, col2, col3 = st.columns(3)

    with col1:
        new_food_protein = st.number_input("Protein", min_value=0.0, max_value=100.0, step=0.1)
        new_food_fat = st.number_input("Fat", min_value=0.0, max_value=100.0, step=0.1)
        new_food_carbs = st.number_input("Carbs", min_value=0.0, max_value=100.0, step=0.1)

        # Auto-calculate calories
        calories = calculate_calories_from_macros(new_food_protein, new_food_fat, new_food_carbs)
        st.metric("Calculated Calories", f"{calories:.1f} kcal")

    with col2:
        new_food_weight = st.number_input("Weight", min_value=0.1, max_value=1000.0, value=100.0, step=0.1)
        new_food_basis = st.selectbox("Basis", options=['gm', 'ml', 'p'])
        new_food_category = st.selectbox("Category", options=['veg', 'non-veg'])
        new_food_fibre = st.number_input("Fibre", min_value=0.0, max_value=100.0, step=0.1)

    with col3:
        new_food_avg_weight = st.text_input("Average Weight (optional)")
        new_food_source = st.text_input("Source (optional)")

    if st.button("Add to Database"):
        if new_food_name and not food_exists_in_database(new_food_name):
            new_food = {
                'Food Name': new_food_name,
                'Protein': new_food_protein,
                'Fat': new_food_fat,
                'Carbs': new_food_carbs,
                'Calories': calories,
                'Weight': new_food_weight,
                'Basis': new_food_basis,
                'Category': new_food_category,
                'Fibre': new_food_fibre,
                'Avg Weight': new_food_avg_weight,
                'Source': new_food_source
            }
            if save_food_to_database(new_food):
                st.success("Food added to database!")
                # Reload the food database
                food_db = load_food_database()

# Food logging section
st.header("Log Your Meals")
meal_types = ['breakfast', 'lunch', 'snacks', 'dinner']

for meal_type in meal_types:
    with st.container():
        st.subheader(f"{meal_type.title()}")
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Only show food selection if database has items
            if not food_db.empty and 'Food Name' in food_db.columns:
                food_selection = st.selectbox(
                    f"Select food for {meal_type}", 
                    options=food_db['Food Name'].tolist(),
                    key=f"food_select_{meal_type}"
                )
            else:
                st.warning("No foods available in database")
                continue

        with col2:
            portion = st.number_input(
                "Portion (g)", 
                min_value=0.0, 
                max_value=1000.0, 
                value=100.0,
                step=10.0,
                key=f"portion_{meal_type}"
            )

        with col3:
            if st.button("Add", key=f"add_{meal_type}"):
                food_item = food_db[food_db['Food Name'] == food_selection].iloc[0]
                multiplier = portion / 100
                logged_item = {
                    'name': food_item['Food Name'],
                    'calories': food_item['Calories'] * multiplier,
                    'protein': food_item['Protein'] * multiplier,
                    'fat': food_item['Fat'] * multiplier,
                    'carbs': food_item['Carbs'] * multiplier,
                    'portion': portion
                }
                st.session_state.daily_log[meal_type].append(logged_item)

# Display daily totals and progress
st.header("Daily Progress")

# Calculate totals
total_calories = sum(sum(item['calories'] for item in meal) for meal in st.session_state.daily_log.values())
total_protein = sum(sum(item['protein'] for item in meal) for meal in st.session_state.daily_log.values())
total_fat = sum(sum(item['fat'] for item in meal) for meal in st.session_state.daily_log.values())
total_carbs = sum(sum(item['carbs'] for item in meal) for meal in st.session_state.daily_log.values())

# Create progress gauges
col1, col2, col3, col4 = st.columns(4)

with col1:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_calories,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Calories"},
        gauge={
            'axis': {'range': [None, calorie_goal]},
            'bar': {'color': "#2ECC71"},
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': calorie_goal
            }
        }
    ))
    st.plotly_chart(fig)

with col2:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_protein,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Protein (g)"},
        gauge={
            'axis': {'range': [None, protein_goal]},
            'bar': {'color': "#3498DB"},
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': protein_goal
            }
        }
    ))
    st.plotly_chart(fig)

with col3:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_fat,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Fat (g)"},
        gauge={
            'axis': {'range': [None, fat_goal]},
            'bar': {'color': "#E74C3C"},
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': fat_goal
            }
        }
    ))
    st.plotly_chart(fig)

with col4:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_carbs,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Carbs (g)"},
        gauge={
            'axis': {'range': [None, carb_goal]},
            'bar': {'color': "#F1C40F"},
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': carb_goal
            }
        }
    ))
    st.plotly_chart(fig)

# Clear daily log button
if st.button("Clear Daily Log"):
    st.session_state.daily_log = {
        'breakfast': [],
        'lunch': [],
        'snacks': [],
        'dinner': []
    }
    st.experimental_rerun()