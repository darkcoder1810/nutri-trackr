import streamlit as st
from sheets_db import load_user_info, save_user_info

# Page config
st.set_page_config(page_title="User Information", page_icon="👤", layout="wide")

# Load custom CSS
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.title("👤 User Information")


def show_user_info_form():
    with st.form("user_info_form"):
        st.subheader("Personal Information")
        # Get user info from sheet first
        mobile = st.text_input("Mobile Number",
                               value=st.session_state.get('mobile', ''))
        full_name = st.text_input("Full Name",
                                  value=st.session_state.user_info.get(
                                      'full_name', ''))
        saved_weight = float(st.session_state.user_info.get('weight', 70.0))
        weight = st.number_input("Weight (kg)",
                                 min_value=20.0,
                                 max_value=200.0,
                                 value=saved_weight)
        calorie_mode = st.radio("Calorie Mode",
                                ['maintenance', 'bulk', 'deficit'],
                                index=['maintenance', 'bulk', 'deficit'].index(
                                    st.session_state.user_info.get(
                                        'calorie_mode', 'maintenance')))

        st.subheader("Macro Settings")
        protein_per_kg = st.slider(
            "Protein (g) per kg of bodyweight", 1.6, 3.0,
            float(st.session_state.user_info.get('protein_per_kg', 2.0)))
        fat_percent = st.slider(
            "Fat (% of total calories)", 20, 35,
            int(
                float(st.session_state.user_info.get('fat_percent', 0.25)) *
                100)) / 100

        submitted = st.form_submit_button("Save Information")
        if submitted:
            if not mobile:
                st.error("Mobile number is required")
            else:
                # Save mobile and full name to session state first
                st.session_state.mobile = mobile
                st.session_state.user_info[
                    'full_name'] = full_name  # Save full name to session state
                mobile = str(mobile).strip()
                if not mobile:
                    st.error("Mobile number is required")
                    return False

                user_data = {
                    'mobile': mobile,
                    'full_name': full_name,  # Include full name in user data
                    'weight': weight,
                    'calorie_mode': calorie_mode,
                    'protein_per_kg': protein_per_kg,
                    'fat_percent': fat_percent
                }
                if save_user_info(user_data):
                    st.session_state.user_info = user_data
                    st.success("Information saved successfully!")
                    return True
                else:
                    st.error("Error saving information")
        return False


# Initialize session state
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
    loaded_user_info = load_user_info()
    if loaded_user_info:
        st.session_state.user_info = loaded_user_info

show_user_info_form()
