import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
from functions import get_workouts_for_bodypart, get_entries_for_latest_day, insert_workout, update_workout_elo
import altair as alt

# MongoDB Connection
client = MongoClient("mongodb+srv://marcfolchpomares:AstonMartin1@mycluster.e19nlo1.mongodb.net/?retryWrites=true&w=majority&appName=mycluster")
db = client['gymelo']  # Replace 'gymelo' with your database name
collection = db['workout_data']  # Replace 'workout_data' with your collection name
cursor = collection.find()
df = pd.DataFrame(cursor).drop('_id', axis=1, errors='ignore')

df2 = update_workout_elo(df).sort_values('day', ascending=False).drop_duplicates(['bodypart', 'workout'])

st.markdown(f"""
    <div style="text-align: center; background: linear-gradient(90deg, #FF7F50, #FFD700); padding: 10px; border-radius: 10px;">
        <h1 style="color: white;">Elo: {df2['elo_score'].mean():,.0f}</h1>
    </div>
    <br>
    <br>
    <br>
""", unsafe_allow_html=True)

# Automatic today's date
today_date = datetime.now().isoformat()

# Fetch bodyparts and workouts
bodyparts = collection.distinct("bodypart")
workouts = collection.distinct("workout")

# Layout for inputs
col1, col2 = st.columns(2)
with col1:
    selected_bodypart = st.selectbox("Select Bodypart", ["Select"] + bodyparts)
    workouts = get_workouts_for_bodypart(selected_bodypart) if selected_bodypart != "Select" else []
    selected_workout = st.selectbox("Select Workout", ["Select"] + workouts)

with col2:
    weight = st.number_input("Enter Weight (kg)", min_value=0.0, step=0.5, format="%.1f")
    repetitions = st.number_input("Enter Repetitions", min_value=0, step=1)

# Latest Entries Section

if selected_bodypart != "Select" and selected_workout != "Select":
    last_entries = get_entries_for_latest_day(selected_bodypart, selected_workout)
    if last_entries:
        df_last_entries = pd.DataFrame(last_entries, columns=["weight", "repetitions", "date"])
        st.dataframe(df_last_entries)
    

# Submit Button with Success Animation
if st.button("🚀 Submit Workout"):
    if selected_bodypart != "Select" and selected_workout != "Select" and weight > 0 and repetitions > 0:
        today_datetime = datetime.now()
        insert_workout(today_datetime, selected_bodypart, selected_workout, weight, repetitions)
        st.success("Your workout has been successfully logged! 🏆")
    else:
        st.error("Please fill all fields correctly.")

filtered_df = df2[df2['workout'] == selected_workout]

if not filtered_df.empty:
    last_item = filtered_df.tail(1)
    st.markdown(f"""
        <div style="text-align: center; background-color: black; padding: 10px; border-radius: 10px;">
            <h1 style="color: white;">Elo Score: {last_item['elo_score'].values[0]:,.0f}</h1>
            <p style="color: white;">Elo Change: {last_item['elo_change'].values[0]:,.0f}</p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.info("No Elo data available for this workout.")
