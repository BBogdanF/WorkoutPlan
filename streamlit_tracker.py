import streamlit as st
import json
import os
import re # Import regular expressions for parsing exercise names

# --- Configuration ---
PLAN_FILE = 'workout_plan.json'
STATUS_FILE = 'completion_status.json'
DETAILS_FILE = 'exercise_details.json' # New file for exercise details

# --- Data Loading and Saving ---

def load_workout_plan(filepath=PLAN_FILE):
    """Loads the workout plan from the specified JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            plan = json.load(f)
        if not isinstance(plan, list) or not all(isinstance(month, list) for month in plan):
             raise ValueError("Invalid plan structure in JSON file.")
        if not all(isinstance(week, list) for month in plan for week in month):
             raise ValueError("Invalid plan structure in JSON file.")
        if not all(isinstance(day, dict) or day is None for month in plan for week in month for day in week):
             raise ValueError("Invalid day structure in JSON file.")
        return plan
    except FileNotFoundError:
        st.error(f"Error: Workout plan file '{filepath}' not found.")
        st.stop()
    except json.JSONDecodeError:
        st.error(f"Error: Could not decode JSON from '{filepath}'. Check the file format.")
        st.stop()
    except ValueError as e:
        st.error(f"Error: {e}")
        st.stop()
    except Exception as e:
        st.error(f"An unexpected error occurred loading the plan: {e}")
        st.stop()

def load_completion_status(filepath=STATUS_FILE):
    """Loads the completion status from the specified JSON file."""
    if not os.path.exists(filepath):
        return {}
    try:
        if os.path.getsize(filepath) == 0: return {}
        with open(filepath, 'r', encoding='utf-8') as f:
            status = json.load(f)
        if not isinstance(status, dict):
             st.warning(f"Status file '{filepath}' has invalid format. Starting fresh.")
             return {}
        return status
    except json.JSONDecodeError:
        st.warning(f"Could not decode JSON from '{filepath}'. Starting fresh.")
        return {}
    except Exception as e:
        st.warning(f"An unexpected error occurred loading status: {e}. Starting fresh.")
        return {}

def save_completion_status(status_data, filepath=STATUS_FILE):
    """Saves the completion status dictionary to the specified JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error: Could not save completion status to '{filepath}': {e}")
        return False

def load_exercise_details(filepath=DETAILS_FILE):
    """Loads exercise descriptions and tips from the specified JSON file."""
    if not os.path.exists(filepath):
        st.warning(f"Exercise details file '{filepath}' not found. Descriptions will be unavailable.")
        return {} # Return empty dict if file doesn't exist
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            details = json.load(f)
        if not isinstance(details, dict):
             st.warning(f"Exercise details file '{filepath}' has invalid format.")
             return {}
        return details
    except json.JSONDecodeError:
        st.warning(f"Could not decode JSON from '{filepath}'. Descriptions may be unavailable.")
        return {}
    except Exception as e:
        st.warning(f"An unexpected error occurred loading exercise details: {e}")
        return {}

# --- Streamlit Display Functions ---

def display_week_st(plan, month_idx, week_idx, exercise_details):
    """Displays the details for a specific week using Streamlit elements, including notes and exercise expanders."""
    if month_idx < 0 or month_idx >= len(plan):
        st.error("Invalid month selected.")
        return
    if week_idx < 0 or week_idx >= len(plan[month_idx]):
        st.error("Invalid week selected for the chosen month.")
        return

    week_data = plan[month_idx][week_idx]
    overall_week_num = month_idx * 4 + week_idx + 1

    st.subheader(f"Details for Week {overall_week_num}")

    # Header row for columns
    col_head1, col_head2 = st.columns([4, 1]) # Adjust column ratio if needed
    with col_head1:
        st.markdown("**Workout / Rest Details, Tips & Exercise Info**") # Updated header
    with col_head2:
        st.markdown("**Status**")
    st.divider() # Horizontal line

    for day_idx, day_data in enumerate(week_data):
        if day_data is None: continue # Skip if day data is null

        day_key = f"m{month_idx}_w{week_idx}_d{day_idx}"
        day_num = day_data.get("dayNum", day_idx + 1)
        is_completed = st.session_state.completion_status.get(day_key, False)

        # Create columns for each day entry
        col_info, col_check = st.columns([4, 1]) # Match header ratio

        with col_info:
            # Display day info
            st.markdown(f"**Day {day_num}: {day_data.get('focus', 'N/A')}** ({day_data.get('type', 'N/A')})")

            # Display Workout Details and Exercise Expanders
            details_list = day_data.get("details", [])
            if details_list:
                for detail_item in details_list:
                    st.markdown(f"- {detail_item}") # Display the original detail (e.g., "Squats: 2x8")

                    # --- Add Exercise Expander ---
                    # Try to extract exercise name (simple parsing)
                    # Match letters, spaces, hyphens, potentially parentheses for variations like (opt)
                    match = re.match(r"([a-zA-Z\s-]+(?:\s*\(.*?\))?)", detail_item)
                    exercise_name_raw = match.group(1).strip() if match else None

                    # Clean up the name for lookup (remove set/rep info, variations like (opt))
                    exercise_name_lookup = None
                    if exercise_name_raw:
                         # Remove common patterns like (opt), (Alt), etc. for cleaner lookup
                         exercise_name_lookup = re.sub(r'\s*\(.*?\)', '', exercise_name_raw).strip()
                         # Handle specific known variations if needed
                         if "Push-ups (Knee/Toe" in exercise_name_raw: exercise_name_lookup = "Push-ups"
                         if "Push-ups (try toes" in exercise_name_raw: exercise_name_lookup = "Push-ups"
                         if "Push-ups (Decline" in exercise_name_raw: exercise_name_lookup = "Push-ups" # Or map to "Decline Push-ups" if defined
                         if "Glute Bridge (Single Leg" in exercise_name_raw: exercise_name_lookup = "Single Leg Glute Bridges"


                    if exercise_name_lookup and exercise_name_lookup in exercise_details:
                        ex_detail = exercise_details[exercise_name_lookup]
                        with st.expander(f"ℹ️ How to do {exercise_name_lookup}"):
                            st.markdown(f"**Description:** {ex_detail.get('description', 'N/A')}")
                            if ex_detail.get("tips"):
                                st.markdown("**Tips:**")
                                for tip in ex_detail["tips"]:
                                    st.markdown(f"- *{tip}*")
                            # You could add st.image here if you manage image paths/URLs
                            if os.path.exists(ex_detail.get("image_placeholder", "")):
                                st.image(ex_detail["image_placeholder"])
                    # Fallback if lookup name not found but raw name was parsed
                    elif exercise_name_raw and exercise_name_raw in exercise_details:
                         ex_detail = exercise_details[exercise_name_raw]
                         with st.expander(f"ℹ️ How to do {exercise_name_raw}"):
                             st.markdown(f"**Description:** {ex_detail.get('description', 'N/A')}")
                             # ... (rest of expander content as above)

            elif day_data.get('type') == 'Rest':
                 st.markdown("- *Rest Day*")

            # --- Display Day Notes/Tips ---
            notes = day_data.get("notes")
            if notes:
                # Use st.caption for less emphasis than blockquote
                st.caption(f"💡 Tip for the day: {notes}")


        with col_check:
            # Display checkbox
            new_status = st.checkbox("Done", value=is_completed, key=day_key, label_visibility="collapsed")
            if new_status != is_completed:
                 st.session_state.completion_status[day_key] = new_status
                 st.session_state.needs_saving = True

        st.divider() # Separator between days


def display_progress_summary_st(status_session_state, plan):
    """Displays a summary of the workout progress using Streamlit."""
    total_days = 0
    completed_days = 0
    total_workout_days = 0
    completed_workout_days = 0

    for m_idx, month in enumerate(plan):
        if m_idx < len(plan):
            for w_idx, week in enumerate(month):
                if w_idx < len(month): # Check week index validity
                    week_data = month[w_idx]
                    if isinstance(week_data, list):
                        total_days += len(week_data)
                        for d_idx, day in enumerate(week_data):
                            if isinstance(day, dict):
                                day_key = f"m{m_idx}_w{w_idx}_d{d_idx}"
                                is_workout = day.get("type", "").lower() == "workout"
                                if is_workout: total_workout_days += 1
                                if status_session_state.get(day_key, False):
                                    completed_days += 1
                                    if is_workout: completed_workout_days += 1

    if total_days == 0:
        st.write("No workout days found.")
        return

    overall_percentage = (completed_days / total_days) * 100 if total_days > 0 else 0
    workout_percentage = (completed_workout_days / total_workout_days) * 100 if total_workout_days > 0 else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Overall Days Completed", value=f"{completed_days} / {total_days}", delta=f"{overall_percentage:.1f}%")
    with col2:
        st.metric(label="Workout Days Completed", value=f"{completed_workout_days} / {total_workout_days}", delta=f"{workout_percentage:.1f}%")


def display_warmup_stretching_info():
    """Displays general Warm-up and Stretching information."""
    st.header("🤸 Warm-up & Cool-down Info")

    tab1, tab2 = st.tabs(["Warm-up (Before Workout)", "Cool-down (After Workout)"])

    with tab1:
        st.subheader("Warm-up Routine (5-10 Minutes)")
        st.markdown("""
            *Never skip your warm-up! It prepares your muscles for exercise and reduces injury risk.*

            **1. Light Cardio (3-5 minutes):** Get your blood flowing. Choose one or mix:
                - Marching in place
                - Light jogging in place
                - Jumping jacks (or step jacks)
                - Butt kicks
                - High knees

            **2. Dynamic Stretches (3-5 minutes):** Focus on movement. Perform 8-12 reps per side/exercise:
                - **Arm Circles:** Forward and backward, small to large circles.
                - **Leg Swings:** Forward/backward and side-to-side (hold onto something for balance if needed).
                - **Torso Twists:** Stand with feet shoulder-width apart, gently twist your upper body side to side.
                - **Cat-Cow Stretch:** On hands and knees, alternate arching and rounding your back.
                - **Walking Lunges (shallow):** Take small steps into a lunge, focusing on stretching the hip flexor.
        """)

    with tab2:
        st.subheader("Cool-down Routine (5-10 Minutes)")
        st.markdown("""
            *Helps improve flexibility and aids recovery. Hold each stretch gently, without bouncing.*

            **Hold each stretch for 20-30 seconds.**

            - **Quadriceps Stretch:** Stand tall, grab your ankle and gently pull your heel towards your glute. Keep knees close together.
            - **Hamstring Stretch:** Sit on the floor, extend one leg straight, bend the other leg with foot towards inner thigh. Gently lean forward over the straight leg. OR stand and hinge at hips towards toes.
            - **Calf Stretch:** Stand facing a wall, place hands on wall. Step one foot back, keeping leg straight and heel down. Lean forward slightly.
            - **Triceps Stretch:** Reach one arm overhead, bend elbow so hand is behind your head. Use other hand to gently push elbow down.
            - **Shoulder Stretch:** Bring one arm across your body, use the other arm to gently pull it closer to your chest.
            - **Chest Stretch:** Stand in a doorway, place forearm on doorframe, elbow bent at 90 degrees. Gently lean forward.
            - **Glute Stretch (Figure-4):** Lie on back, knees bent. Cross one ankle over the opposite knee. Reach through and gently pull the bottom thigh towards you.
        """)


# --- Streamlit App Main Logic ---

st.set_page_config(layout="wide", page_title="Workout Tracker")
st.title("🗓️ 3-Month Workout Tracker")

# --- Load Data ---
# Use caching to load data only once unless the file changes
@st.cache_data
def get_workout_plan():
    return load_workout_plan()

@st.cache_data
def get_exercise_details():
    return load_exercise_details()

workout_plan = get_workout_plan()
exercise_details = get_exercise_details()

# --- Initialize Session State ---
# This block runs on every script rerun if the key isn't present
if 'completion_status' not in st.session_state:
    st.session_state.completion_status = load_completion_status()
    # print("DEBUG: Initialized completion_status from file.") # Uncomment for debugging

if 'needs_saving' not in st.session_state:
     st.session_state.needs_saving = False
     # print("DEBUG: Initialized needs_saving.") # Uncomment for debugging

# --- Sidebar Controls ---
st.sidebar.header("Controls")

# Month selection
month_options = {f"Month {i+1}": i for i in range(len(workout_plan))}
default_month_index = st.session_state.get('selected_month_idx', 0)
if default_month_index >= len(month_options): default_month_index = 0
selected_month_name = st.sidebar.selectbox("Select Month", options=list(month_options.keys()), index=default_month_index, key='month_selector')
month_idx = month_options[selected_month_name]
# Store selection in state *after* getting value to avoid potential loop issues on first run
if st.session_state.get('selected_month_idx') != month_idx:
    st.session_state.selected_month_idx = month_idx
    # Reset week index when month changes
    st.session_state.selected_week_idx = 0


# Week selection
weeks_in_month = len(workout_plan[month_idx]) if month_idx < len(workout_plan) else 0
week_options = {}
for i in range(weeks_in_month):
    overall_week_num = month_idx * 4 + i + 1
    week_options[f"Week {overall_week_num} (M{month_idx+1}-W{i+1})"] = i

default_week_index = st.session_state.get('selected_week_idx', 0)
if default_week_index >= len(week_options): default_week_index = 0

if week_options:
    selected_week_name = st.sidebar.selectbox("Select Week", options=list(week_options.keys()), index=default_week_index, key='week_selector')
    week_idx = week_options[selected_week_name]
    # Store selection in state *after* getting value
    if st.session_state.get('selected_week_idx') != week_idx:
        st.session_state.selected_week_idx = week_idx
else:
    st.sidebar.warning("No weeks found for the selected month.")
    selected_week_name = None
    week_idx = None # Ensure week_idx is None if no options

# Save button
st.sidebar.divider()
if st.sidebar.button("💾 Save Progress", use_container_width=True):
    if save_completion_status(st.session_state.completion_status):
        st.session_state.needs_saving = False
        st.sidebar.success("Progress Saved!")
        # Short delay can help user see the success message
        # import time; time.sleep(1.5); st.rerun() # Use rerun cautiously
    else:
        st.sidebar.error("Failed to save progress.")
# Display unsaved changes warning below the button
if st.session_state.needs_saving:
     st.sidebar.warning("🟡 Unsaved changes!")

# --- Main Display Area ---

# Display the selected week's details
if week_idx is not None:
    # Check indices are valid before calling display function
    if month_idx < len(workout_plan) and week_idx < len(workout_plan[month_idx]):
         display_week_st(workout_plan, month_idx, week_idx, exercise_details)
    else:
         st.error("Selected week data index is out of bounds. Check plan file.")
else:
    # Only show warning if weeks were expected for the selected month
    if week_options:
         st.warning("Please select a valid week.")
    # If no weeks available for the month, this area remains blank, which is fine.


st.divider()

# Display progress summary
st.header("📊 Progress Summary")
display_progress_summary_st(st.session_state.completion_status, workout_plan)

st.divider()

# Display Warm-up and Stretching Info
display_warmup_stretching_info()

# --- Footer / Debug Info (Optional) ---
# with st.expander("Debug Info"):
#    st.write("Session State Status (first 10):", dict(list(st.session_state.completion_status.items())[:10])) # Show partial status
#    st.write("Needs Saving:", st.session_state.needs_saving)
#    st.write("Selected Month Index:", st.session_state.get('selected_month_idx'))
#    st.write("Selected Week Index:", st.session_state.get('selected_week_idx'))
