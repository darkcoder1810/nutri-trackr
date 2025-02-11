import streamlit as st
import pandas as pd
from utils import load_food_database

# Page config
st.set_page_config(
    page_title="Food Database",
    page_icon="🗄️",
    layout="wide"
)

# Load custom CSS
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Page title
st.title("🗄️ Food Database")

# Load the database
food_db = load_food_database()

# Display database statistics
st.header("Database Statistics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Foods", len(food_db))

with col2:
    if 'Calories' in food_db.columns:
        avg_calories = round(food_db['Calories'].mean(), 1)
        st.metric("Average Calories", f"{avg_calories} kcal")

with col3:
    if 'Protein' in food_db.columns:
        avg_protein = round(food_db['Protein'].mean(), 1)
        st.metric("Average Protein", f"{avg_protein}g")

# Display the full database
st.header("Food Items")

# Add search functionality
search_term = st.text_input("Search foods", "")

# Filter the database based on search
if search_term and 'Food Name' in food_db.columns:
    filtered_db = food_db[food_db['Food Name'].str.contains(search_term, case=False)]
else:
    filtered_db = food_db

# Sort options
if not food_db.empty:
    sort_col = st.selectbox(
        "Sort by",
        options=[col for col in food_db.columns if col in ['Food Name', 'Calories', 'Protein', 'Fat', 'Carbs']]
    )
    sort_order = st.radio("Sort order", ['Ascending', 'Descending'], horizontal=True)

    # Sort the database
    filtered_db = filtered_db.sort_values(
        by=sort_col, 
        ascending=(sort_order == 'Ascending')
    )

# Display the table
if not filtered_db.empty:
    st.dataframe(
        filtered_db,
        column_config={
            "Food Name": "Food Name",
            "Calories": st.column_config.NumberColumn("Calories (kcal)", format="%.1f"),
            "Protein": st.column_config.NumberColumn("Protein (g)", format="%.1f"),
            "Fat": st.column_config.NumberColumn("Fat (g)", format="%.1f"),
            "Carbs": st.column_config.NumberColumn("Carbs (g)", format="%.1f"),
        },
        hide_index=True,
    )
else:
    st.warning("No data available in the database")

# Add a note about the data source
st.markdown("""
---
**Note:** This data is synchronized with Google Sheets. Any changes made through the main page's "Add New Food" form will be reflected here.
""")