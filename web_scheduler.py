import streamlit as st
import csv
from collections import defaultdict
from datetime import datetime
import io
import os
import logging

# Replace the hardcoded page config with environment variables for flexibility
st.set_page_config(
    page_title=os.getenv("PAGE_TITLE", "Interview Scheduler"),
    page_icon=os.getenv("PAGE_ICON", "📅"),
    layout="wide"
)

st.title("Interview Scheduler")

# Remove the constants and add UI elements
st.write("Upload your student availability CSV file to generate the interview schedule.")

col1, col2 = st.columns(2)
with col1:
    required_primary = st.number_input("Required Primary Students", min_value=1, max_value=50, value=12)
with col2:
    required_secondary = st.number_input("Required Secondary Students", min_value=1, max_value=50, value=10)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@st.cache_data
def process_uploaded_file(uploaded_file):
    # Read the CSV file
    students = []
    availability = defaultdict(dict)
    dates = []
    
    # Convert uploaded file to text lines for csv reader with proper encoding
    text_data = io.TextIOWrapper(uploaded_file, encoding='utf-8-sig')
    reader = csv.DictReader(text_data)
    dates = [date for date in reader.fieldnames[2:]]
    
    for row in reader:
        full_name = f"{row['Last Name']}-{row['First Name']}"
        students.append(full_name)
        for date in dates:
            availability[full_name][date] = (row[date] != 'x')
            
    return students, availability, dates

# Rest of your original scheduling logic
def get_available_students(date, role, excluded_students, students, availability, weeks, last_primary_week, student_count):
    week_number = weeks[date]
    available = [
        s for s in students 
        if availability[s][date] and s not in excluded_students and
        (role == "secondary" or 
         (role == "primary" and last_primary_week[s] < week_number - 1))
    ]
    if role == "primary":
        return sorted(available, key=lambda s: (student_count[s]["primary"], student_count[s]["secondary"]))
    else:
        return sorted(available, key=lambda s: (student_count[s]["secondary"], student_count[s]["primary"]))

def create_schedule(students, availability, dates, required_primary, required_secondary):
    schedule = {date: {"primary": [], "secondary": []} for date in dates}
    student_count = {student: {"primary": 0, "secondary": 0} for student in students}
    last_primary_week = {student: -2 for student in students}

    # Define weeks
    start_date = datetime.strptime(dates[0], "%m/%d").replace(year=2023)
    weeks = {}
    for date in dates:
        current_date = datetime.strptime(date, "%m/%d").replace(year=2023)
        if current_date.month < start_date.month:
            current_date = current_date.replace(year=2024)
        week_number = (current_date - start_date).days // 7
        weeks[date] = week_number

    # Schedule students
    for date in dates:
        week_number = weeks[date]
        available_primary = get_available_students(date, "primary", [], students, availability, weeks, last_primary_week, student_count)
        
        primary = available_primary[:required_primary]
        for student in primary:
            schedule[date]["primary"].append(student)
            student_count[student]["primary"] += 1
            last_primary_week[student] = week_number
        
        available_secondary = get_available_students(date, "secondary", primary, students, availability, weeks, last_primary_week, student_count)
        secondary = available_secondary[:required_secondary]
        for student in secondary:
            schedule[date]["secondary"].append(student)
            student_count[student]["secondary"] += 1

    return schedule, student_count, weeks

def create_output_csv(schedule, student_count, dates):
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Primary', 'Secondary'])
    
    # Write schedule for each date
    for date in dates:
        primary = ', '.join(schedule[date]['primary'])
        secondary = ', '.join(schedule[date]['secondary'])
        writer.writerow([date, primary, secondary])
    
    # Write summary
    writer.writerow([])
    writer.writerow(['Student', 'Primary Count', 'Secondary Count'])
    for student in student_count:
        writer.writerow([student, student_count[student]['primary'], student_count[student]['secondary']])
    
    return output.getvalue()

def test_schedule_validity(schedule, availability, weeks, students):
    errors = []
    
    # Create a reverse mapping of weeks to dates
    week_to_dates = defaultdict(list)
    for date, week in weeks.items():
        week_to_dates[week].append(date)

    for student in students:
        last_primary_week = -2
        for date in dates:
            is_primary = student in schedule[date]['primary']
            is_secondary = student in schedule[date]['secondary']
            is_scheduled = is_primary or is_secondary
            
            # Test 1: Student is scheduled only when available
            if is_scheduled and not availability[student][date]:
                errors.append(f"{student} is scheduled on {date} but is not available")
            
            # Test 2: Student is not both primary and secondary
            if is_primary and is_secondary:
                errors.append(f"{student} is both primary and secondary on {date}")
            
            # Test 3: Student is not primary on back-to-back weeks
            if is_primary:
                current_week = weeks[date]
                if current_week - last_primary_week == 1:
                    errors.append(f"{student} is primary on back-to-back weeks")
                last_primary_week = current_week
                



    return errors

# Replace the expander section with direct instructions
st.subheader("CSV Format Instructions")
st.write("""
Your CSV file should have the following format:
- First row: `Last Name,First Name,` followed by dates (e.g., 9/9, 9/10, etc.)
- For each student row:
    - Last name in first column
    - First name in second column
    - For each date: leave blank if available, put 'x' if not available

Example:
```
Last Name,First Name,9/9,9/10,9/16
Smith,John,x,,
Doe,Jane,,x,
```
""")

# File uploader (moved above the instructions)
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    try:
        with st.spinner('Processing schedule...'):
            # Process the uploaded file
            students, availability, dates = process_uploaded_file(uploaded_file)
            # Pass the new variables to create_schedule
            schedule, student_count, weeks = create_schedule(students, availability, dates, required_primary, required_secondary)
            
            # Validate the schedule
            errors = test_schedule_validity(schedule, availability, weeks, students)
            if errors:
                st.warning("Schedule generated with warnings:")
                for error in errors:
                    st.write(f"- {error}")
            else:
                st.success("Schedule generated and validated successfully!")
            
            # Create the output CSV
            output_csv = create_output_csv(schedule, student_count, dates)
            
            # Show success message and download button
            st.download_button(
                label="Download Interview Schedule",
                data=output_csv,
                file_name="interview_schedule.csv",
                mime="text/csv"
            )
            
            # Display some statistics
            st.subheader("Quick Statistics")
            total_students = len(students)
            scheduled_students = sum(1 for s in student_count if student_count[s]['primary'] + student_count[s]['secondary'] > 0)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Students", total_students)
            col2.metric("Scheduled Students", scheduled_students)
            col3.metric("Total Dates", len(dates))
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        st.write("Please make sure your CSV file is properly formatted with 'First Name', 'Last Name', and date columns.")