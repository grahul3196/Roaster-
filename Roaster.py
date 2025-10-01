import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import random
from collections import defaultdict

st.set_page_config(page_title="Automated Roster Generator", layout="wide")
st.title("📅 Fully Automated Monthly Shift Roster Generator")

st.markdown("""
This app automatically:
- Assigns off days per employee
- Distributes shifts fairly
- Prevents **Night → Morning** shift transitions
""")

# Step 1: Upload Employee List
st.header("📥 Step 1: Upload Employee Off-Day Requirements")
uploaded_file = st.file_uploader("Upload a CSV with columns: `Name`, `OffDays`", type="csv")

if uploaded_file:
    try:
        df_employees = pd.read_csv(uploaded_file)
        if 'Name' not in df_employees.columns or 'OffDays' not in df_employees.columns:
            st.error("CSV must contain columns: Name, OffDays")
            st.stop()
        df_employees['OffDays'] = df_employees['OffDays'].astype(int)
        st.success("Employee data loaded successfully.")
        st.dataframe(df_employees)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        st.stop()
else:
    st.info("Please upload a valid CSV to proceed.")
    st.stop()

# Step 2: Month and Shifts
st.header("🗓️ Step 2: Select Month and Shifts")

col1, col2 = st.columns(2)
with col1:
    year = st.number_input("Year", value=datetime.today().year, step=1)
with col2:
    month_name = st.selectbox("Month", list(calendar.month_name[1:]), index=datetime.today().month - 1)
month = list(calendar.month_name).index(month_name)

shifts_input = st.text_input("Enter shift types (comma-separated)", "Morning, Evening, Night")
shifts = [s.strip() for s in shifts_input.split(",") if s.strip()]

if not shifts:
    st.error("Please enter at least one shift.")
    st.stop()

# Generate Button
if st.button("🚀 Generate Roster"):
    st.info("Generating roster...")

    employees = dict(zip(df_employees['Name'], df_employees['OffDays']))

    # Get dates
    num_days = calendar.monthrange(year, month)[1]
    start_date = datetime(year, month, 1)
    all_dates = [start_date + timedelta(days=i) for i in range(num_days)]
    all_date_strs = [d.strftime("%Y-%m-%d") for d in all_dates]

    # Generate off days
    employee_off_days = {}
    for emp, off_count in employees.items():
        off_days = random.sample(all_date_strs, min(off_count, len(all_date_strs)))
        employee_off_days[emp] = set(off_days)

    # Shift assignment with fairness + night→morning prevention
    prev_shift = {emp: None for emp in employees}
    shift_counts = {emp: defaultdict(int) for emp in employees}
    roster = []

    for current_date in all_dates:
        date_str = current_date.strftime("%Y-%m-%d")
        weekday = current_date.strftime("%A")

        daily_assignments = {}
        available_emps = [e for e in employees if date_str not in employee_off_days[e]]
        random.shuffle(available_emps)

        # Score by fairness and night shift rule
        emp_scores = []
        for emp in available_emps:
            penalty = 0
            if prev_shift[emp] == "Night":
                penalty += 100  # Avoid morning after night
            penalty += sum(shift_counts[emp].values())  # Balance load
            emp_scores.append((penalty, emp))

        emp_scores.sort()
        sorted_emps = [emp for _, emp in emp_scores]

        # Assign shifts
        for i, emp in enumerate(sorted_emps):
            shift = shifts[i % len(shifts)]
            if prev_shift[emp] == "Night" and shift == "Morning":
                shift = "Evening" if "Evening" in shifts else "OFF"
            daily_assignments[emp] = shift
            prev_shift[emp] = shift
            shift_counts[emp][shift] += 1

        for emp in employees:
            shift = daily_assignments.get(emp, "OFF")
            roster.append({
                "Date": date_str,
                "Day": weekday,
                "Employee": emp,
                "Shift": shift
            })

    # Output
    df_roster = pd.DataFrame(roster)
    st.success("✅ Roster generated successfully!")
    st.dataframe(df_roster, use_container_width=True)

    # Download
    csv = df_roster.to_csv(index=False).encode("utf-8")
    filename = f"roster_{year}_{month:02}.csv"
    st.download_button("📥 Download Roster as CSV", csv, file_name=filename, mime="text/csv")

