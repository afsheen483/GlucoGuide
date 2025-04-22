import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from groq import Groq  

client = Groq(api_key=st.secrets["groq_api_key"])

def initialize_database():
    conn = sqlite3.connect("glucoguide.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blood_sugar_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            date TEXT,
            fasting_sugar REAL,
            pre_meal_sugar REAL,
            post_meal_sugar REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            date TEXT,
            meal_plan TEXT,
            is_favorite BOOLEAN DEFAULT 0
        )
    """)
    
    conn.commit()
    return conn, cursor

conn, cursor = initialize_database()

def get_wearable_data():
    try:
        return 120.0, 140.0, 160.0  
    except Exception as e:
        st.error(f"Failed to fetch wearable data: {str(e)}")
        return None, None, None

def validate_inputs(fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences):
    errors = []
    
    if not (50 <= fasting_sugar <= 500):
        errors.append("Fasting sugar level must be between 50 and 500 mg/dL.")
    
    if not (70 <= pre_meal_sugar <= 500):
        errors.append("Pre-meal sugar level must be between 70 and 500 mg/dL.")
    
    if not (70 <= post_meal_sugar <= 500):
        errors.append("Post-meal sugar level must be between 70 and 500 mg/dL.")
    
    if not dietary_preferences:
        errors.append("Dietary preferences cannot be empty.")
    
    return errors

def generate_health_alerts(fasting_sugar, pre_meal_sugar, post_meal_sugar):
    alerts = []
    if fasting_sugar > 126:
        alerts.append("High fasting sugar detected (>126 mg/dL). Consider consulting a doctor.")
    if pre_meal_sugar > 130:
        alerts.append("High pre-meal sugar detected (>130 mg/dL). Consider consulting a doctor.")
    if post_meal_sugar > 180:
        alerts.append("High post-meal sugar detected (>180 mg/dL). Consider consulting a doctor.")
    return alerts

def generate_meal_plan(fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences):
    try:
        prompt = f"""
        Generate a meal plan for a diabetic patient with:
        - Fasting sugar: {fasting_sugar} mg/dL
        - Pre-meal sugar: {pre_meal_sugar} mg/dL
        - Post-meal sugar: {post_meal_sugar} mg/dL
        - Dietary preferences: {dietary_preferences}
        Include low glycemic index options if sugar levels are high.
        Provide detailed nutritional information and portion sizes.
        """
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Expert dietitian specializing in diabetes management"},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating meal plan: {str(e)}")
        return None

def save_blood_sugar_data(user_id, fasting_sugar, pre_meal_sugar, post_meal_sugar):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO blood_sugar_data (user_id, date, fasting_sugar, pre_meal_sugar, post_meal_sugar)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, date, fasting_sugar, pre_meal_sugar, post_meal_sugar))
    conn.commit()

def save_meal_plan(user_id, meal_plan, is_favorite=False):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO meal_plans (user_id, date, meal_plan, is_favorite)
        VALUES (?, ?, ?, ?)
    """, (user_id, date, meal_plan, int(is_favorite)))
    conn.commit()

def get_blood_sugar_trends(user_id):
    cursor.execute("""
        SELECT date, fasting_sugar, pre_meal_sugar, post_meal_sugar
        FROM blood_sugar_data
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 7
    """, (user_id,))
    return cursor.fetchall()

def get_saved_meal_plans(user_id):
    cursor.execute("""
        SELECT date, meal_plan, is_favorite
        FROM meal_plans
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    return cursor.fetchall()

def plot_trends(data):
    if not data:
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

st.set_page_config(page_title="GlucoGuide", page_icon="", layout="wide")

# Main App
st.title("GlucoGuide: Diabetes Management System")
st.markdown("### AI-Powered Meal Planning and Blood Sugar Tracking")

# User Session Management
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_123"  # Simplified user management
user_id = st.session_state.user_id

# Sidebar Controls
with st.sidebar:
    st.header("Settings")
    if st.button("Reset Database (Testing)"):
        cursor.execute("DELETE FROM blood_sugar_data")
        cursor.execute("DELETE FROM meal_plans")
        conn.commit()
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Wearable Device Integration**")
    if st.button("Sync Wearable Data"):
        fasting, pre, post = get_wearable_data()
        if fasting:
            st.session_state.update({
                "fasting_sugar": fasting,
                "pre_meal_sugar": pre,
                "post_meal_sugar": post
            })
            st.success("Data synced successfully!")

tab1, tab2 = st.tabs(["Meal Planner", "Health Dashboard"])

with tab1:
    st.header("Generate New Meal Plan")
    
    col1, col2 = st.columns(2)
    with col1:
        fasting_sugar = st.number_input("Fasting Sugar (mg/dL)", min_value=0.0, 
                                      value=st.session_state.get("fasting_sugar", 90.0))
        pre_meal_sugar = st.number_input("Pre-Meal Sugar (mg/dL)", min_value=0.0,
                                       value=st.session_state.get("pre_meal_sugar", 110.0))
    
    with col2:
        post_meal_sugar = st.number_input("Post-Meal Sugar (mg/dL)", min_value=0.0,
                                        value=st.session_state.get("post_meal_sugar", 140.0))
        dietary_preferences = st.selectbox("Dietary Preferences",
                                         options=["", "Vegetarian", "Low-Carb", "Mediterranean",
                                                  "Vegan", "Gluten-Free", "Diabetic-Friendly"],
                                         index=1)  
    
    errors = validate_inputs(fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences)
    if errors:
        for error in errors:
            st.error(error)

    disabled = len(errors) > 0

    if not disabled:
        alerts = generate_health_alerts(fasting_sugar, pre_meal_sugar, post_meal_sugar)
        if alerts:
            st.warning("#### Health Alerts")
            for alert in alerts:
                st.markdown(f"{alert}")

    if st.button("Generate Personalized Meal Plan", use_container_width=True, disabled=disabled):
        with st.spinner("Analyzing your metrics and creating optimal meal plan..."):
            meal_plan = generate_meal_plan(fasting_sugar, pre_meal_sugar, 
                                         post_meal_sugar, dietary_preferences)
            
            if meal_plan:
                st.session_state.meal_plan_generated = True
                save_blood_sugar_data(user_id, fasting_sugar, pre_meal_sugar, post_meal_sugar)
                save_meal_plan(user_id, meal_plan)
                
                st.success("Meal Plan Generated Successfully!")
                st.markdown("---")
                st.markdown(meal_plan)
                
                fav_col, _ = st.columns([1,3])
                with fav_col:
                    if st.button("Mark as Favorite"):
                        cursor.execute("""
                            UPDATE meal_plans SET is_favorite = 1 
                            WHERE user_id = ? AND date = (
                                SELECT MAX(date) FROM meal_plans WHERE user_id = ?
                            )
                        """, (user_id, user_id))
                        conn.commit()
                        st.rerun()

    st.markdown("---")
    st.header("Saved Meal Plans")
    
    if 'meal_plan_generated' in st.session_state:
        saved_plans = get_saved_meal_plans(user_id)
        if saved_plans:
            for date, plan, favorite in saved_plans:
                with st.expander(f"{date.split()[0]} {'' if favorite else ''}"):
                    st.markdown(plan)
                    if st.button("Delete", key=f"del_{date}"):
                        cursor.execute("DELETE FROM meal_plans WHERE date = ?", (date,))
                        conn.commit()
                        st.rerun()
        else:
            st.info("No saved meal plans found. Generate one to get started!")
    else:
        st.info("Generate your first meal plan to see saved plans here")

with tab2:
    st.header("Health Dashboard")
    
    st.subheader("Blood Sugar Trends")
    trends_data = get_blood_sugar_trends(user_id)
    if trends_data:
        plot_trends(trends_data)
    else:
        st.info("No historical data available.")

conn.close()
