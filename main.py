import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils import (calculate_calories, calculate_macros, load_food_database,
                   save_food_to_database, calculate_calories_from_macros,
                   food_exists_in_database)
from sheets_db import load_user_info, save_user_info, save_meal_log, get_daily_logs, delete_logs_by_date_range, get_daily_summaries

import pytz

# Prepare row data
ist_tz = pytz.timezone('Asia/Kolkata')  # Define the IST timezone

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
    st.title("Welcome to NutriTracker")
    st.subheader("Please enter your mobile number to continue")

    mobile = st.text_input("Mobile Number",
                           max_chars=10)  # Limit to 10 characters
    if st.button("Continue", key="continue_mobile"):
        if not mobile:
            st.error("Please enter a mobile number")
        elif not mobile.isdigit() or len(
                mobile) != 10:  # Ensure only digits and length
            st.error(
                "Please enter a valid mobile number with exactly 10 digits.")
        else:
            st.session_state.mobile = mobile
            user_data = load_user_info()

            if user_data:
                st.session_state.user_info = user_data
                st.session_state.mobile_verified = True
                st.rerun()
            else:
                st.warning(
                    "No existing data found. Please enter your information.")
                st.switch_page("pages/user_info.py")

# Main application
elif st.session_state.mobile_verified:
    # Add tabs for navigation
    tabs = st.tabs(
        ["🏠 Home", "➕ Add Food", "📊 Daily Log", "👨🏾‍💻 About Developer"])

    with tabs[0]:  # Home tab
        st.header("Welcome to NutriTracker")
        # Rest of the home content
        # Load food database
        food_db = load_food_database()

        # Main title
        st.title("🥗 Calorie & Macro Tracker")

        # Sidebar for user info and goals
        with st.sidebar:
            st.header("User Information")
            full_name = st.session_state.user_info.get('full_name', 'iHacK')
            st.write(f"Name: {full_name}")  # Displaying Full Name
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

        # Display daily totals and progress
        st.header("Daily Progress")

        # Get today's logs from Google Sheets
        today = datetime.now(pytz.timezone('Asia/Kolkata')).strftime(
            '%d-%m-%Y')  # Ensure today's date is formatted correctly in IST
        today_logs = get_daily_logs(st.session_state.mobile, today)
        if today_logs:
            total_calories = sum(log['Calories'] for log in today_logs)
            total_protein = sum(log['Protein'] for log in today_logs)
            total_fat = sum(log['Fat'] for log in today_logs)
            total_carbs = sum(log['Carbs'] for log in today_logs)
        else:
            total_calories = total_protein = total_fat = total_carbs = 0

        # Calories status calculation
        calorie_difference = target_calories - total_calories
        status_color_calories = "#2ECC71" if calorie_difference >= 0 else "#E74C3C"
        calories_status_text = f"{abs(calorie_difference):.0f} kcal<br> {'remaining' if calorie_difference >= 0 else 'over'}"
        fig_calories = go.Figure()
        fig_calories.add_trace(
            go.Indicator(
                mode="number",
                value=total_calories,
                title={
                    'text':
                    f"Total Calories<br><span style='color: {status_color_calories}'>{calories_status_text}</span>"
                }))
        fig_calories.update_layout(height=250)  # Update the height here

        # Protein status calculation
        protein_difference = protein_target - total_protein
        status_color_protein = "#2ECC71" if protein_difference >= 0 else "#E74C3C"
        protein_status_text = f"{abs(protein_difference):.0f} g<br> {'remaining' if protein_difference >= 0 else 'over'}"
        fig_protein = go.Figure()
        fig_protein.add_trace(
            go.Indicator(
                mode="number",
                value=total_protein,
                title={
                    'text':
                    f"Total Protein (g)<br><span style='color: {status_color_protein}'>{protein_status_text}</span>"
                }))
        fig_protein.update_layout(height=250)  # Update the height here

        # Fat status calculation
        fat_difference = fat_target - total_fat
        status_color_fat = "#2ECC71" if fat_difference >= 0 else "#E74C3C"
        fat_status_text = f"{abs(fat_difference):.0f} g<br> {'remaining' if fat_difference >= 0 else 'over'}"
        fig_fat = go.Figure()
        fig_fat.add_trace(
            go.Indicator(
                mode="number",
                value=total_fat,
                title={
                    'text':
                    f"Total Fat (g)<br><span style='color: {status_color_fat}'>{fat_status_text}</span>"
                }))
        fig_fat.update_layout(height=250)  # Update the height here

        # Carbs status calculation
        carbs_difference = carb_target - total_carbs
        status_color_carbs = "#2ECC71" if carbs_difference >= 0 else "#E74C3C"
        carbs_status_text = f"{abs(carbs_difference):.0f} g<br> {'remaining' if carbs_difference >= 0 else 'over'}"
        fig_carbs = go.Figure()
        fig_carbs.add_trace(
            go.Indicator(
                mode="number",
                value=total_carbs,
                title={
                    'text':
                    f"Total Carbs (g)<br><span style='color: {status_color_carbs}'>{carbs_status_text}</span>"
                }))
        fig_carbs.update_layout(height=250)  # Update the height here

        # Display charts in a single row using columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.plotly_chart(fig_calories, use_container_width=True)
        with col2:
            st.plotly_chart(fig_protein, use_container_width=True)
        with col3:
            st.plotly_chart(fig_fat, use_container_width=True)
        with col4:
            st.plotly_chart(fig_carbs, use_container_width=True)

        # # Clear daily log button
        # if st.button("Clear Daily Log"):
        #     st.session_state.daily_log = {
        #         'breakfast': [],
        #         'lunch': [],
        #         'snacks': [],
        #         'dinner': []
        #     }
        #     st.rerun()

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
                    portion = st.number_input(
                        f"Portion ({portion_unit})",
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
                        st.session_state.daily_log[meal_type].append(
                            logged_item)

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

                        # Rerun to refresh the chart/UI
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
                    st.warning(
                        f"'{new_food_name}' already exists in the database")

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
                calories = calculate_calories_from_macros(
                    new_food_protein, new_food_fat, new_food_carbs)
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
                new_food_avg_weight = st.text_input(
                    "Average Weight (optional)", key='new_food_avg_weight')
                new_food_source = st.text_input("Source (optional)",
                                                key='new_food_source')

            if st.button("Add to Database"):
                if new_food_name and not food_exists_in_database(
                        new_food_name):
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

    with tabs[2]:  # Daily Log Tab
        # st.header("Daily Log")
        # st.divider()

        # Today's date for filtering
        from datetime import datetime
        today = datetime.now(pytz.timezone('Asia/Kolkata')).strftime(
            '%d-%m-%Y')  # Ensure today's date is formatted correctly in IST

        # Get logs for today
        today_logs = get_daily_logs(st.session_state.mobile, today)

        st.subheader("Today's Calorie Intake")
        if today_logs:
            log_df = pd.DataFrame(today_logs)
            display_cols = [
                'Timestamp', 'Meal Type', 'Food Name', 'Category', 'Calories',
                'Protein', 'Carbs', 'Fat'
            ]

            # Format timestamp to show only time
            log_df['Timestamp'] = pd.to_datetime(
                log_df['Timestamp']).dt.strftime('%I:%M %p')

            st.dataframe(log_df[display_cols], hide_index=True)
        else:
            st.info("No meals logged today")

        st.divider()

        # Daily Summary View
        st.subheader("Daywise Total Calorie Intake Summary")
        summaries = get_daily_summaries(st.session_state.mobile)
        if summaries:
            summary_df = pd.DataFrame(summaries)

            # Convert the 'date' column to datetime format for correct sorting
            summary_df['date'] = pd.to_datetime(summary_df['date'],
                                                format='%d-%m-%Y')
            # Sort the summary by date in descending order
            summary_df.sort_values(by='date', ascending=False, inplace=True)
            # Convert 'date' back to string if needed for display
            summary_df['date'] = summary_df['date'].dt.strftime('%d-%m-%Y')

            st.dataframe(summary_df, hide_index=True)
        else:
            st.info("No meal history available")

        st.divider()

        # Delete Logs Section
        st.subheader("Clear Specific Logs")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Select start date to clear logs",
                                       value=datetime.now().date(),
                                       key="start_date")
        with col2:
            end_date = st.date_input("Select end date to clear logs",
                                     value=datetime.now().date(),
                                     key="end_date")
        if st.button("Delete Logs in Range", type="secondary"):
            if start_date > end_date:
                st.error("Start date must be before end date.")
            else:
                if delete_logs_by_date_range(st.session_state.mobile,
                                             start_date, end_date):
                    st.success(
                        f"Logs deleted successfully between {start_date} and {end_date}!"
                    )
                    st.rerun()
                else:
                    st.error("Failed to delete logs.")

    with tabs[3]:  # Developer Details Tab
        st.subheader("It’s Basically AI 🤖")

        st.markdown("""
        -Please do email me at dhiraj1810.db@gmail.com if you have any questions or feedback.  
        -I’m open to new ideas and collaborations. Thank you for using this app! ✌🏽  
            """)
        #st.write("Email : darkcoders2016@gmail.com")
