import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Monthly Shift Roster Generator", layout="wide")
st.title("📅 Monthly Shift Roster Generator")

# --- Sidebar Input ---
st.sidebar.header("1️⃣ Configuration")

# Upload employee list or enter manually
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

# Year and Month
year = st.sidebar.number_input("Year", value=datetime.today().year, step=1)
month = st.sidebar.selectbox("Month", list(calendar.month_name[1:]), index=datetime.today().month - 1)
month_num = list(calendar.month_name).index(month)

# Weekly offs
st.sidebar.markdown("### Weekly Offs")
weekly_offs = {}
for emp in employees:
    day = st.sidebar.selectbox(f"{emp}'s weekly off", list(calendar.day_name), key=f"off_{emp}")
    weekly_offs[emp] = list(calendar.day_name).index(day)

# Generate button
if st.sidebar.button("Generate Roster"):
    num_days = calendar.monthrange(year, month_num)[1]
    start_date = datetime(year, month_num, 1)
    days = [start_date + timedelta(days=i) for i in range(num_days)]

    roster_data = []

    for day in days:
        weekday = day.weekday()
        date_str = day.strftime("%Y-%m-%d")
        available_emps = [emp for emp in employees if weekly_offs[emp] != weekday]
        random.shuffle(available_emps)

        day_shifts = {}
        for i, emp in enumerate(available_emps):
            assigned_shift = shifts[i % len(shifts)]
            day_shifts[emp] = assigned_shift

        for emp in employees:
            shift = day_shifts.get(emp, "OFF")
            roster_data.append({
                "Date": date_str,
                "Day": calendar.day_name[weekday],
                "Employee": emp,
                "Shift": shift
            })

    roster_df = pd.DataFrame(roster_data)
    st.success("Roster Generated!")
    
    # Display
    st.dataframe(roster_df, use_container_width=True)

    # Download
    csv = roster_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Roster as CSV", csv, file_name=f"roster_{year}_{month_num}.csv", mime="text/csv")

else:
    st.info("Configure settings and click **Generate Roster** to begin.")

