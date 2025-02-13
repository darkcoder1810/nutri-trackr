import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import (calculate_calories, calculate_macros, load_food_database,
                   save_food_to_database, calculate_calories_from_macros,
                   food_exists_in_database)
from sheets_db import load_user_info, save_user_info, save_meal_log

# Page configuration
st.set_page_config(page_title="Calorie Tracker", layout="wide")

# Load custom CSS
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session states
if 'daily_log' not in st.session_state:
    st.session_state.daily_log = {
        'breakfast': [],
        'lunch': [],
        'snacks': [],
        'dinner': []
    }

if 'user_info' not in st.session_state:
    st.session_state.user_info = {}

if 'mobile_verified' not in st.session_state:
    st.session_state.mobile_verified = False

# Mobile number verification section
if not st.session_state.mobile_verified:
    st.title("Welcome to NutriTrackr")
    st.subheader("Please enter your mobile number to continue")

    mobile = st.text_input("Mobile Number")
    if st.button("Continue", key="continue_mobile"):
        if not mobile:
            st.error("Please enter a mobile number")
        else:
            st.session_state.mobile = mobile
            user_data = load_user_info()
            
            if user_data:
                st.session_state.user_info = user_data
                st.session_state.mobile_verified = True
                st.rerun()
            else:
                st.warning("No existing data found. Please enter your information.")
                st.switch_page("pages/user_info.py")

# Main application
elif st.session_state.mobile_verified:
    # Add tabs for navigation
    tabs = st.tabs(["🏠 Home", "➕ Add Food", "📊 Daily Log"])

    with tabs[0]:  # Home tab
        st.header("Welcome to NutriTrackr")
        # Rest of the home content
        # Load food database
        food_db = load_food_database()

        # Main title
        st.title("🥗 Calorie & Macro Tracker")

        # Sidebar for user info and goals
        with st.sidebar:
            st.header("User Information")
            weight = st.session_state.user_info.get('weight', 70.0)
            # Update mobile in user_info if not present
            if 'mobile' not in st.session_state.user_info and 'mobile' in st.session_state:
                st.session_state.user_info['mobile'] = st.session_state.mobile
                
            st.write(f"Weight: {weight} kg")

            # Calorie mode selection
            st.header("Calorie Mode")
            calorie_mode = st.radio(
                "Select calorie target",
                options=['maintenance', 'bulk', 'deficit'],
                index=['maintenance', 'bulk', 'deficit'
                       ].index(st.session_state.user_info['calorie_mode']))
            st.session_state.user_info['calorie_mode'] = calorie_mode

            # Macro customization
            st.header("Macro Settings")
            protein_per_kg = st.slider(
                "Protein (g) per kg of bodyweight", 1.6, 3.0,
                st.session_state.user_info['protein_per_kg'], 0.1)
            st.session_state.user_info['protein_per_kg'] = protein_per_kg

            fat_percent = st.slider(
                "Fat (% of total calories)", 20, 35,
                int(st.session_state.user_info['fat_percent'] * 100), 5) / 100
            st.session_state.user_info['fat_percent'] = fat_percent

            # Save user info whenever it changes
            save_user_info(st.session_state.user_info)

            # Calculate target calories based on mode
            target_calories = calculate_calories(weight, calorie_mode)
            protein_target, fat_target, carb_target = calculate_macros(
                target_calories, protein_per_kg, fat_percent, weight)

            # Display calculated targets
            st.markdown("### Daily Targets")
            st.write(f"Target Calories: {target_calories:.0f} kcal")
            st.write(f"Protein: {protein_target:.1f}g")
            st.write(f"Fat: {fat_target:.1f}g")
            st.write(f"Carbs: {carb_target:.1f}g")

        # Food logging section
        st.header("Log Your Meals")
        meal_types = ['breakfast', 'lunch', 'snacks', 'dinner']

        for meal_type in meal_types:
            with st.container():
                st.subheader(f"{meal_type.title()}")
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    # Food selection with integrated search
                    if not food_db.empty and 'Food Name' in food_db.columns:
                        food_selection = st.selectbox(
                            f"Select food for {meal_type}",
                            options=food_db['Food Name'].tolist(),
                            key=f"food_select_{meal_type}",
                            placeholder="Search for food...",
                        )
                    else:
                        st.warning("No foods available in database")
                        continue

                with col2:
                    # Get the basis for the selected food
                    selected_food = food_db[food_db['Food Name'] ==
                                            food_selection].iloc[0]
                    basis = selected_food.get('Basis', 'gm')

                    # Display portion input with dynamic unit
                    portion_unit = 'p' if basis == 'p' else (
                        'ml' if basis == 'ml' else 'gm')
                    portion = st.number_input(f"Portion ({portion_unit})",
                                              min_value=0.0,
                                              max_value=1000.0,
                                              step=1.0 if basis == 'p' else 10.0,
                                              key=f"portion_{meal_type}")

                with col3:
                    if st.button("Add", key=f"add_{meal_type}"):
                        food_item = food_db[food_db['Food Name'] ==
                                            food_selection].iloc[0]
                        # Calculate multiplier based on basis
                        base_weight = 100 if basis != 'p' else 1
                        multiplier = portion / base_weight

                        logged_item = {
                            'name': food_item['Food Name'],
                            'calories': food_item['Calories'] * multiplier,
                            'protein': food_item['Protein'] * multiplier,
                            'fat': food_item['Fat'] * multiplier,
                            'carbs': food_item['Carbs'] * multiplier,
                            'portion': portion,
                            'unit': portion_unit
                        }
                        # Add to session state
                        st.session_state.daily_log[meal_type].append(logged_item)
                        
                        # Save to daily log sheet
                        meal_log = {
                            'mobile': st.session_state.mobile,
                            'meal_type': meal_type,
                            'weight': portion,
                            'basis': basis,
                            'food_name': food_item['Food Name'],
                            'category': food_item.get('Category', 'N/A'),
                            'calories': logged_item['calories'],
                            'protein': logged_item['protein'],
                            'carbs': logged_item['carbs'],
                            'fat': logged_item['fat']
                        }
                        save_meal_log(meal_log)

        # Display daily totals and progress
        st.header("Daily Progress")

        # Calculate totals
        total_calories = sum(
            sum(item['calories'] for item in meal)
            for meal in st.session_state.daily_log.values())
        total_protein = sum(
            sum(item['protein'] for item in meal)
            for meal in st.session_state.daily_log.values())
        total_fat = sum(
            sum(item['fat'] for item in meal)
            for meal in st.session_state.daily_log.values())
        total_carbs = sum(
            sum(item['carbs'] for item in meal)
            for meal in st.session_state.daily_log.values())

        # Create progress gauges
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            fig = go.Figure(
                go.Indicator(mode="gauge+number",
                             value=total_calories,
                             domain={
                                 'x': [0, 1],
                                 'y': [0, 1]
                             },
                             title={'text': "Calories"},
                             gauge={
                                 'axis': {
                                     'range': [None, target_calories]
                                 },
                                 'bar': {
                                     'color': "#2ECC71"
                                 },
                                 'threshold': {
                                     'line': {
                                         'color': "red",
                                         'width': 4
                                     },
                                     'thickness': 0.75,
                                     'value': target_calories
                                 }
                             }))
            st.plotly_chart(fig)

        with col2:
            fig = go.Figure(
                go.Indicator(mode="gauge+number",
                             value=total_protein,
                             domain={
                                 'x': [0, 1],
                                 'y': [0, 1]
                             },
                             title={'text': "Protein (g)"},
                             gauge={
                                 'axis': {
                                     'range': [None, protein_target]
                                 },
                                 'bar': {
                                     'color': "#3498DB"
                                 },
                                 'threshold': {
                                     'line': {
                                         'color': "red",
                                         'width': 4
                                     },
                                     'thickness': 0.75,
                                     'value': protein_target
                                 }
                             }))
            st.plotly_chart(fig)

        with col3:
            fig = go.Figure(
                go.Indicator(mode="gauge+number",
                             value=total_fat,
                             domain={
                                 'x': [0, 1],
                                 'y': [0, 1]
                             },
                             title={'text': "Fat (g)"},
                             gauge={
                                 'axis': {
                                     'range': [None, fat_target]
                                 },
                                 'bar': {
                                     'color': "#E74C3C"
                                 },
                                 'threshold': {
                                     'line': {
                                         'color': "red",
                                         'width': 4
                                     },
                                     'thickness': 0.75,
                                     'value': fat_target
                                 }
                             }))
            st.plotly_chart(fig)

        with col4:
            fig = go.Figure(
                go.Indicator(mode="gauge+number",
                             value=total_carbs,
                             domain={
                                 'x': [0, 1],
                                 'y': [0, 1]
                             },
                             title={'text': "Carbs (g)"},
                             gauge={
                                 'axis': {
                                     'range': [None, carb_target]
                                 },
                                 'bar': {
                                     'color': "#F1C40F"
                                 },
                                 'threshold': {
                                     'line': {
                                         'color': "red",
                                         'width': 4
                                     },
                                     'thickness': 0.75,
                                     'value': carb_target
                                 }
                             }))
            st.plotly_chart(fig)

        # Clear daily log button
        if st.button("Clear Daily Log"):
            st.session_state.daily_log = {
                'breakfast': [],
                'lunch': [],
                'snacks': [],
                'dinner': []
            }
            st.rerun()

    with tabs[1]:  # Add Food tab
        st.header("Add New Food")
        # Add new food to database

        # Check for form reset
        if 'reset_form' in st.session_state and st.session_state['reset_form']:
            for key in list(st.session_state.keys()):
                if key.startswith('new_food_'):
                    del st.session_state[key]
            del st.session_state['reset_form']

        # Initialize form fields with default values if not in session state
        default_fields = {
            'new_food_name': '',
            'new_food_protein': 0.0,
            'new_food_fat': 0.0,
            'new_food_carbs': 0.0,
            'new_food_weight': 100.0,
            'new_food_basis': 'gm',
            'new_food_category': 'veg',
            'new_food_fibre': 0.0,
            'new_food_avg_weight': '',
            'new_food_source': ''
        }

        for field, default_value in default_fields.items():
            if field not in st.session_state:
                st.session_state[field] = default_value

        with st.expander("Add New Food"):
            col1, col2, col3 = st.columns(3)

            with col1:
                new_food_name = st.text_input("Food Name",
                                              value="",
                                              key='new_food_name')
                if new_food_name and food_exists_in_database(new_food_name):
                    st.warning(f"'{new_food_name}' already exists in the database")

                new_food_protein = st.number_input("Protein",
                                                   min_value=0.0,
                                                   max_value=100.0,
                                                   step=0.1,
                                                   key='new_food_protein')
                new_food_fat = st.number_input("Fat",
                                               min_value=0.0,
                                               max_value=100.0,
                                               step=0.1,
                                               key='new_food_fat')
                new_food_carbs = st.number_input("Carbs",
                                                 min_value=0.0,
                                                 max_value=100.0,
                                                 step=0.1,
                                                 key='new_food_carbs')

                # Auto-calculate calories with proper formatting
                calories = calculate_calories_from_macros(new_food_protein,
                                                           new_food_fat,
                                                           new_food_carbs)
                st.metric("Calculated Calories",
                          f"{calories:.1f} kcal",
                          delta=None,
                          delta_color="normal")

            with col2:
                new_food_weight = st.number_input("Weight",
                                                  min_value=0.1,
                                                  max_value=1000.0,
                                                  value=100.0,
                                                  step=0.1,
                                                  key='new_food_weight')
                new_food_basis = st.selectbox("Basis",
                                              options=['gm', 'ml', 'p'],
                                              key='new_food_basis')
                new_food_category = st.selectbox("Category",
                                                 options=['veg', 'non-veg'],
                                                 key='new_food_category')
                new_food_fibre = st.number_input("Fibre",
                                                 min_value=0.0,
                                                 max_value=100.0,
                                                 step=0.1,
                                                 key='new_food_fibre')

            with col3:
                new_food_avg_weight = st.text_input("Average Weight (optional)",
                                                    key='new_food_avg_weight')
                new_food_source = st.text_input("Source (optional)",
                                                key='new_food_source')

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
                        st.success("Food added successfully!")
                        # Set reset flag
                        st.session_state['reset_form'] = True
                        # Reload the food database
                        st.cache_data.clear()
                        st.rerun()

        # Load food database
        food_db = load_food_database()

    with tabs[2]: #Daily Log Tab
        st.header("Daily Log")
        #Add your daily log display code here.  This will require adapting your existing code to display the daily log in a user-friendly manner.
        # Example:  Iterate through st.session_state.daily_log and display the logged food items for each meal.