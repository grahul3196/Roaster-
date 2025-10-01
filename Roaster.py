import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import random
from collections import defaultdict

st.set_page_config(page_title="Smart Monthly Roster Generator", layout="wide")
st.title("📅 Smart Monthly Roster Generator (With Fairness & Rules)")

# --- Sidebar Inputs ---
st.sidebar.header("1️⃣ Employee Setup")

# Upload or enter employees
upload_option = st.sidebar.radio("Choose employee input method:", ["Manual Entry", "Upload CSV"])

if upload_option == "Manual Entry":
    employees_input = st.sidebar.text_area("Enter employee names (comma separated)", "Alice, Bob, Charlie, David, Eve")
    employees = [e.strip() for e in employees_input.split(",") if e.strip()]
else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV with 'Name' column", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if 'Name' in df.columns:
            employees = df['Name'].dropna().tolist()
        else:
            st.sidebar.error("CSV must contain a 'Name' column.")
            employees = []
    else:
        employees = []

if not employees:
    st.warning("Please provide a list of employees to continue.")
    st.stop()

# Shifts
shifts_input = st.sidebar.text_input("Enter shift types (comma separated)", "Morning, Evening, Night")
shifts = [s.strip() for s in shifts_input.split(",") if s.strip()]
if not shifts:
    st.warning("Please enter at least one shift type.")
    st.stop()

# Month and Year
year = st.sidebar.number_input("Year", value=datetime.today().year, step=1)
month = st.sidebar.selectbox("Month", list(calendar.month_name[1:]), index=datetime.today().month - 1)
month_num = list(calendar.month_name).index(month)

# Get days in month
num_days = calendar.monthrange(year, month_num)[1]
start_date = datetime(year, month_num, 1)
days = [start_date + timedelta(days=i) for i in range(num_days)]
day_strs = [d.strftime("%Y-%m-%d") for d in days]

# --- Off-days Input ---
st.header("2️⃣ Assign Week Offs (Custom Off-Days)")

off_days_map = {}

off_input_method = st.radio("Select off-day input method:", ["Manual (Calendar)", "Upload CSV with off-dates"])

if off_input_method == "Upload CSV with off-dates":
    off_csv = st.file_uploader("Upload CSV (columns: Name, OffDates)", type="csv", key="off_csv")
    if off_csv:
        df_offs = pd.read_csv(off_csv)
        for _, row in df_offs.iterrows():
            name = row['Name']
            if name in employees:
                try:
                    off_dates = [d.strip() for d in str(row['OffDates']).split(",")]
                    off_days_map[name] = off_dates
                except:
                    st.error(f"Could not parse dates for {name}.")
else:
    for emp in employees:
        selected = st.multiselect(f"Off-days for {emp}", day_strs, key=f"off_{emp}")
        off_days_map[emp] = selected

# --- Generate Button ---
if st.button("🚀 Generate Smart Roster"):
    st.info("Generating roster with fairness and shift rules...")

    prev_shift = {emp: None for emp in employees}
    shift_counts = {emp: defaultdict(int) for emp in employees}
    roster = []

    for current_date in days:
        date_str = current_date.strftime("%Y-%m-%d")
        weekday = current_date.strftime("%A")
        available_emps = [e for e in employees if date_str not in off_days_map.get(e, [])]
        random.shuffle(available_emps)

        # Score employees based on shift history & fairness
        emp_scores = []
        for emp in available_emps:
            penalty = 0
            if prev_shift[emp] == "Night":
                penalty += 100  # Penalize if last shift was Night
            penalty += sum(shift_counts[emp].values())  # Prioritize fair distribution
            emp_scores.append((penalty, emp))

        emp_scores.sort()
        sorted_emps = [emp for _, emp in emp_scores]

        # Assign shifts
        assigned = {}
        for i, emp in enumerate(sorted_emps):
            shift = shifts[i % len(shifts)]

            # Prevent Night → Morning
            if prev_shift[emp] == "Night" and shift == "Morning":
                shift = "Evening" if "Evening" in shifts else "OFF"

            assigned[emp] = shift
            prev_shift[emp] = shift
            shift_counts[emp][shift] += 1

        for emp in employees:
            shift = assigned.get(emp, "OFF")
            roster.append({
                "Date": date_str,
                "Day": weekday,
                "Employee": emp,
                "Shift": shift
            })

    # Display Roster
    df_roster = pd.DataFrame(roster)
    st.success("✅ Roster Generated Successfully!")

    st.dataframe(df_roster, use_container_width=True)

    csv = df_roster.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Roster CSV", csv, file_name=f"roster_{year}_{month_num:02}.csv", mime="text/csv")
else:
    st.info("Configure settings and click **Generate Smart Roster** to begin.")
