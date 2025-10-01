import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import random
from collections import defaultdict

st.set_page_config(page_title="Auto Roster Generator", layout="wide")
st.title("📅 Fully Automated Shift Roster Generator (No File Uploads)")

st.markdown("""
This app lets you:
- Enter engineers manually
- Set month, working days, and off-days per person
- Auto-generate fair shift rosters
""")

# Step 1: Enter engineers and off-days
st.header("👥 Step 1: Enter Engineer Names and Off-Days")

names_input = st.text_area("Enter engineer names (one per line)", "John\nSam\nAlice\nBob")
names = [n.strip() for n in names_input.split("\n") if n.strip()]

if not names:
    st.warning("Please enter at least one engineer.")
    st.stop()

default_off = 8
offs = {}
st.write("### 🔧 Off-Days per Engineer")
for name in names:
    offs[name] = st.number_input(f"Off days for {name}", min_value=0, max_value=31, value=default_off, step=1)

# Step 2: Month, shifts, working days
st.header("📆 Step 2: Month, Working Days & Shifts")

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

num_days = calendar.monthrange(year, month)[1]
st.info(f"{calendar.month_name[month]} {year} has **{num_days} days**.")

# Generate button
if st.button("🚀 Generate Roster"):
    st.info("Generating roster...")

    employees = offs  # name -> off days
    start_date = datetime(year, month, 1)
    all_dates = [start_date + timedelta(days=i) for i in range(num_days)]
    all_date_strs = [d.strftime("%Y-%m-%d") for d in all_dates]

    # Step 1: Randomly assign off days
    employee_off_days = {}
    for emp, off_count in employees.items():
        off_days = random.sample(all_date_strs, min(off_count, len(all_date_strs)))
        employee_off_days[emp] = set(off_days)

    # Step 2: Assign shifts
    prev_shift = {emp: None for emp in employees}
    shift_counts = {emp: defaultdict(int) for emp in employees}
    roster = []

    for current_date in all_dates:
        date_str = current_date.strftime("%Y-%m-%d")
        weekday = current_date.strftime("%A")

        daily_assignments = {}
        available_emps = [e for e in employees if date_str not in employee_off_days[e]]
        random.shuffle(available_emps)

        emp_scores = []
        for emp in available_emps:
            penalty = 0
            if prev_shift[emp] == "Night":
                penalty += 100
            penalty += sum(shift_counts[emp].values())
            emp_scores.append((penalty, emp))

        emp_scores.sort()
        sorted_emps = [emp for _, emp in emp_scores]

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
                "Engineer": emp,
                "Shift": shift
            })

    df_roster = pd.DataFrame(roster)
    st.success("✅ Roster generated successfully!")
    st.dataframe(df_roster, use_container_width=True)

    csv = df_roster.to_csv(index=False).encode("utf-8")
    filename = f"roster_{year}_{month:02}.csv"
    st.download_button("📥 Download CSV", csv, file_name=filename, mime="text/csv")
    
