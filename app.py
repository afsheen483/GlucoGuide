import streamlit as st
import groq

# Sidebar input for API key
api_key = st.secrets["groq_api_key"]

# Function to call Groq AI API and get a personalized meal plan
def get_meal_plan(api_key, fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences):
    try:
        # Initialize the Groq AI client with the provided API keyssss
        client = groq.Client(api_key=api_key)

        # Define the prompts
        prompt = (
            f"My fasting sugar level is {fasting_sugar} mg/dL, "
            f"my pre-meal sugar level is {pre_meal_sugar} mg/dL, "
            f"and my post-meal sugar level is {post_meal_sugar} mg/dL. "
            f"My dietary preferences are {dietary_preferences}. "
            "Please provide a personalized meal plan that can help me manage my blood sugar levels effectively."
        )

        # Call Groq API with a stable model
        response = client.chat.completions.create(
            model="llama3-8b-8192",  # Use a stable and supported model
            messages=[
                {"role": "system", "content": "You are a world-class nutritionist who specializes in diabetes management."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )

        # Extract the meal plan from the response
        meal_plan = response.choices[0].message.content
        return meal_plan

    except groq.GroqError as e:
        return f"Error: {e.message}"

# Streamlit app
st.title("GlucoGuide")

st.write("""
**GlucoGuide** is a personalized meal planning tool designed specifically for diabetic patients. 
By entering your sugar levels and dietary preferences, GlucoGuide generates meal plans that are 
tailored to help you manage your blood sugar levels effectively.
""")

# Sidebar inputs for sugar levels and dietary preferences
st.sidebar.header("Enter Your Details")

fasting_sugar = st.sidebar.number_input("Fasting Sugar Levels (mg/dL)", min_value=0, max_value=500, step=1)
pre_meal_sugar = st.sidebar.number_input("Pre-Meal Sugar Levels (mg/dL)", min_value=0, max_value=500, step=1)
post_meal_sugar = st.sidebar.number_input("Post-Meal Sugar Levels (mg/dL)", min_value=0, max_value=500, step=1)

dietary_preferences = st.sidebar.text_input("Dietary Preferences (e.g., vegetarian, low-carb)")

# Generate meal plan button
if st.sidebar.button("Generate Meal Plan"):
    meal_plan = get_meal_plan(api_key, fasting_sugar, pre_meal_sugar, post_meal_sugar, dietary_preferences)
    st.write("Based on your sugar levels and dietary preferences, here is a personalized meal plan:")
    st.markdown(meal_plan)
