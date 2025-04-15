import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import requests  # wearable device API calls
from groq import Groq  

client = Groq(api_key=st.secrets["groq_api_key"])

# Initialize SQLite database
conn = sqlite3.connect("glucoguide.db")
cursor = conn.cursor()

# Create tables for historical data and meal plans
cursor.execute("""
    CREATE TABLE IF NOT EXISTS blood_sugar_data (
        user_id TEXT,
        date TEXT,
        fasting_sugar REAL,
        pre_meal_sugar REAL,
        post_meal_sugar REAL
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS meal_plans (
        user_id TEXT,
        date TEXT,
        meal_plan TEXT,
        is_favorite BOOLEAN
    )
""")
conn.commit()

# Simulated wearable device API 
def get_wearable_data():
    try:
        return 120.0, 140.0, 160.0  # Simulated values
    except Exception as e:
        st.error(f"Failed to fetch wearable data: {str(e)}")
        return None, None, None

# Validate user inputs
def validate_inputs(fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences):
    errors = []
    if fasting_sugar < 0:
        errors.append("Fasting sugar level must be greater than or equal to 0.")
    if pre_meal_sugar < 0:
        errors.append("Pre-meal sugar level must be greater than or equal to 0.")
    if post_meal_sugar < 0:
        errors.append("Post-meal sugar level must be greater than or equal to 0.")
    if not dietary_preferences:
        errors.append("Dietary preferences cannot be empty.")
    return errors

# Generate health alerts based on blood sugar levels
def generate_health_alerts(fasting_sugar, pre_meal_sugar, post_meal_sugar):
    alerts = []
    if fasting_sugar > 126:
        alerts.append("High fasting sugar detected (>126 mg/dL). Consider consulting a doctor.")
    if pre_meal_sugar > 130:
        alerts.append("High pre-meal sugar detected (>130 mg/dL). Consider consulting a doctor.")
    if post_meal_sugar > 180:
        alerts.append("High post-meal sugar detected (>180 mg/dL). Consider consulting a doctor.")
    return alerts

# Generate meal plan using Groq AI API
def generate_meal_plan(fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences):
    try:
        prompt = f"""
        Generate a meal plan for a diabetic patient with the following details:
        - Fasting sugar: {fasting_sugar} mg/dL
        - Pre-meal sugar: {pre_meal_sugar} mg/dL
        - Post-meal sugar: {post_meal_sugar} mg/dL
        - Dietary preferences: {dietary_preferences}
        Recommend meals with a low glycemic index if sugar levels are high.
        """
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a dietitian specializing in diabetic meal planning."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192"
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating meal plan: {str(e)}")
        return None

# Save blood sugar data to database
def save_blood_sugar_data(user_id, fasting_sugar, pre_meal_sugar, post_meal_sugar):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO blood_sugar_data (user_id, date, fasting_sugar, pre_meal_sugar, post_meal_sugar)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, date, fasting_sugar, pre_meal_sugar, post_meal_sugar))
    conn.commit()

# Save meal plan to database
def save_meal_plan(user_id, meal_plan, is_favorite=False):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO meal_plans (user_id, date, meal_plan, is_favorite)
        VALUES (?, ?, ?, ?)
    """, (user_id, date, meal_plan, is_favorite))
    conn.commit()

# Retrieve historical blood sugar data
def get_blood_sugar_trends(user_id):
    cursor.execute("""
        SELECT date, fasting_sugar, pre_meal_sugar, post_meal_sugar
        FROM blood_sugar_data
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 7
    """, (user_id,))
    return cursor.fetchall()

# Retrieve saved meal plans
def get_saved_meal_plans(user_id):
    cursor.execute("""
        SELECT date, meal_plan, is_favorite
        FROM meal_plans
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    return cursor.fetchall()

# Plot blood sugar trends
def plot_trends(data):
    if not data:
        st.write("No historical data available to display trends.")
        return
    df = pd.DataFrame(data, columns=["Date", "Fasting Sugar", "Pre-Meal Sugar", "Post-Meal Sugar"])
    df["Date"] = pd.to_datetime(df["Date"])
    plt.figure(figsize=(10, 5))
    plt.plot(df["Date"], df["Fasting Sugar"], label="Fasting Sugar", marker="o")
    plt.plot(df["Date"], df["Pre-Meal Sugar"], label="Pre-Meal Sugar", marker="o")
    plt.plot(df["Date"], df["Post-Meal Sugar"], label="Post-Meal Sugar", marker="o")
    plt.xlabel("Date")
    plt.ylabel("Blood Sugar (mg/dL)")
    plt.title("Blood Sugar Trends")
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

# Streamlit app
st.title("GlucoGuide: Personalized Meal Planning for Diabetic Patients")
st.markdown("""
GlucoGuide is a personalized meal planning tool designed specifically for diabetic patients.
By entering your sugar levels and dietary preferences, GlucoGuide generates meal plans that are tailored to help you manage your blood sugar levels effectively.
""")

# User ID (for simplicity, using a session state; in production, use proper authentication)
if "user_id" not in st.session_state:
    st.session_state.user_id = "user1"  # Simulated user ID
user_id = st.session_state.user_id

# Wearable device integration
st.subheader("Import Data from Wearable Device")
if st.button("Connect to Wearable Device"):
    fasting_sugar, pre_meal_sugar, post_meal_sugar = get_wearable_data()
    if fasting_sugar is not None:
        st.session_state.fasting_sugar = fasting_sugar
        st.session_state.pre_meal_sugar = pre_meal_sugar
        st.session_state.post_meal_sugar = post_meal_sugar
        st.success("Successfully imported data from wearable device!")

# User inputs
st.subheader("Enter Your Details")
fasting_sugar = st.number_input("Fasting Sugar Levels (mg/dL)", min_value=0.0, value=st.session_state.get("fasting_sugar", 0.0))
pre_meal_sugar = st.number_input("Pre-Meal Sugar Levels (mg/dL)", min_value=0.0, value=st.session_state.get("pre_meal_sugar", 0.0))
post_meal_sugar = st.number_input("Post-Meal Sugar Levels (mg/dL)", min_value=0.0, value=st.session_state.get("post_meal_sugar", 0.0))
dietary_preferences = st.text_input("Dietary Preferences (e.g., vegetarian, low-carb)")

# Input validation
errors = validate_inputs(fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences)
if errors:
    for error in errors:
        st.error(error)
else:
    # Health alerts
    alerts = generate_health_alerts(fasting_sugar, pre_meal_sugar, post_meal_sugar)
    if alerts:
        st.subheader("Health Alerts")
        for alert in alerts:
            st.warning(alert)

    # Generate meal plan
    if st.button("Generate Meal Plan"):
        meal_plan = generate_meal_plan(fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences)
        if meal_plan:
            st.subheader("Your Personalized Meal Plan")
            st.markdown(meal_plan)

            # Save blood sugar data and meal plan
            save_blood_sugar_data(user_id, fasting_sugar, pre_meal_sugar, post_meal_sugar)
            save_meal_plan(user_id, meal_plan)

            # Option to mark as favorite
            if st.checkbox("Mark this meal plan as a favorite"):
                cursor.execute("UPDATE meal_plans SET is_favorite = 1 WHERE user_id = ? AND meal_plan = ?", (user_id, meal_plan))
                conn.commit()
                st.success("Meal plan marked as favorite!")

# Display blood sugar trends
st.subheader("Blood Sugar Trends (Last 7 Days)")
trends_data = get_blood_sugar_trends(user_id)
plot_trends(trends_data)

# Display saved meal plans
st.subheader("Saved Meal Plans")
saved_plans = get_saved_meal_plans(user_id)
if saved_plans:
    for date, meal_plan, is_favorite in saved_plans:
        st.markdown(f"**Date:** {date} {'(Favorite)' if is_favorite else ''}")
        st.markdown(meal_plan)
        st.markdown("---")
else:
    st.write("No saved meal plans available.")

# Close database connection
conn.close()