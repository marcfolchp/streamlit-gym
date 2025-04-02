import streamlit as st
from pymongo import MongoClient
from datetime import datetime, date

# MongoDB Connection
client = MongoClient("mongodb+srv://marcfolchpomares:AstonMartin1@mycluster.e19nlo1.mongodb.net/?retryWrites=true&w=majority&appName=mycluster")
db = client['gymelo']  # Replace 'gymelo' with your database name
collection = db['workout_data']  # Replace 'workout_data' with your collection name

# Function to insert data into MongoDB
def insert_workout(date, bodypart, workout, weight, repetitions):
    document = {
        "date": date,
        "bodypart": bodypart,
        "workout": workout,
        "weight": weight,
        "repetitions": repetitions,
    }

    result = collection.insert_one(document)
    st.success(f"Data inserted successfully! Record ID: {result.inserted_id}")

'''-------------------------------------------------------------------'''

# Function to fetch all entries for the latest day (earlier than today) for the selected bodypart and workout
def get_entries_for_latest_day(bodypart, workout):
    # Get today's date as a datetime object
    today_date = datetime.now().date()  # Get today's date without time
    
    # Convert today's date to datetime object (set time to 00:00:00 for comparison)
    today_datetime = datetime.combine(today_date, datetime.min.time())

    # Find the latest date earlier than today for the given bodypart and workout, ignoring the time part
    latest_date_cursor = collection.find(
        {"bodypart": bodypart, "workout": workout, "date": {"$lt": today_datetime}}
    ).sort("date", -1).limit(1)

    latest_date = list(latest_date_cursor)
    
    if not latest_date:
        return []  # No data available for this workout
    
    # Extract the date part only (ignoring the time part) for comparison
    latest_date = latest_date[0]["date"].date()  # Only keep the date part

    # Now find all entries with this latest date (ignoring the time)
    query = {
        "bodypart": bodypart,
        "workout": workout,
        "date": {"$gte": datetime.combine(latest_date, datetime.min.time()), 
                 "$lt": datetime.combine(latest_date, datetime.max.time())}
    }

    # Fetch all entries for the latest date (not just one)
    results = list(collection.find(query))  # Fetch all entries for the latest date
    return results

'''-------------------------------------------------------------------'''

def get_workouts_for_bodypart(selected_bodypart):
    if selected_bodypart:
        workouts = collection.distinct("workout", {"bodypart": selected_bodypart})
        return workouts
    return []

'''-------------------------------------------------------------------'''

def update_workout_elo(df, k_factor=32, base_elo=1000):

    def score(w, r):
        return round(((((w) * 16) + r) - (w * 12)), 0) ** 3

    df['new_score'] = score(df['weight'], df['repetitions'])
    df['day'] = df['date'].dt.date

    df = df.groupby(['day', 'bodypart', 'workout'])['new_score'].mean().reset_index()
    
    """
    Update Elo scores for each workout based on performance changes 
    and track the aggregate change in Elo compared to the last session.
    
    :param df: DataFrame with 'day', 'workout', and 'new_score'
    :param k_factor: Sensitivity factor for Elo updates
    :param base_elo: Initial Elo score for workouts
    :return: DataFrame with 'elo_score' and 'elo_change' columns
    """
    # Sort data to ensure chronological order by workout and day
    df = df.sort_values(by=["workout", "day"]).reset_index(drop=True)
    
    # Initialize columns
    df["elo_score"] = base_elo
    df["elo_change"] = 0.0  # Tracks change from the previous session
    
    # Dictionaries to track previous values
    previous_scores = {}
    current_elos = {}

    # Iterate over rows to calculate Elo scores
    for idx, row in df.iterrows():
        workout = row["workout"]
        new_score = row["new_score"]

        # If it's the first appearance of the workout
        if workout not in previous_scores:
            previous_scores[workout] = new_score
            current_elos[workout] = base_elo
            df.at[idx, "elo_score"] = base_elo
            df.at[idx, "elo_change"] = 0.0  # No change since it's the first session
        else:
            # Calculate percentage change in performance
            prev_score = previous_scores[workout]
            performance_change = ((new_score - prev_score) / prev_score) * 100

            # Calculate Elo adjustment
            elo_adjustment = k_factor * (performance_change / 100)

            # Update current Elo and round
            new_elo = round(current_elos[workout] + elo_adjustment, 2)
            
            # Track the Elo change
            elo_change = round(new_elo - current_elos[workout], 2)
            
            # Update DataFrame and dictionaries
            df.at[idx, "elo_score"] = new_elo
            df.at[idx, "elo_change"] = elo_change
            
            current_elos[workout] = new_elo
            previous_scores[workout] = new_score
    
    return df