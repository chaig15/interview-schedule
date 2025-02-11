import csv
from collections import defaultdict
from datetime import datetime, timedelta

# File names configuration
INPUT_FILE = 'test_availability.csv'
OUTPUT_FILE = 'interview_schedule.csv'

# Interview configuration
REQUIRED_PRIMARY = 12
REQUIRED_SECONDARY = 10

# Read the CSV file
students = []
availability = defaultdict(dict)
dates = []

# Read the CSV file
with open(INPUT_FILE, 'r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    # Get dates from headers, excluding First Name and Last Name columns
    dates = [date for date in reader.fieldnames[2:]]
    for row in reader:
        full_name = f"{row['Last Name']}-{row['First Name']}"
        students.append(full_name)
        for date in dates:
            availability[full_name][date] = (row[date] != 'x')
            

# Initialize schedule and counters using dates from CSV
schedule = {date: {"primary": [], "secondary": []} for date in dates}
student_count = {student: {"primary": 0, "secondary": 0} for student in students}
weekly_primary = defaultdict(set)
last_primary_week = {student: -2 for student in students}

# Define weeks
current_year = datetime.now().year
start_date = datetime.strptime(dates[0], "%m/%d").replace(year=current_year)
weeks = {}
for i, date in enumerate(dates):
    current_date = datetime.strptime(date, "%m/%d").replace(year=current_year)
    if current_date.month < start_date.month:
        current_date = current_date.replace(year=current_year + 1)
    week_number = (current_date - start_date).days // 7
    weeks[date] = week_number

def get_available_students(date, role, excluded_students):
    week_number = weeks[date]
    available = [
        s for s in students 
        if availability[s][date] and s not in excluded_students and
        (role == "secondary" or 
         (role == "primary" and last_primary_week[s] < week_number - 1))
    ]
    if role == "primary":
        return sorted(available, key=lambda s: (student_count[s]["primary"], student_count[s]["secondary"]))
    else:  # For secondary, prioritize those with lower secondary counts
        return sorted(available, key=lambda s: (student_count[s]["secondary"], student_count[s]["primary"]))

# Schedule students
for date in dates:
    week_number = weeks[date]
    available_primary = get_available_students(date, "primary", [])
    
    primary = available_primary[:REQUIRED_PRIMARY]
    for student in primary:
        schedule[date]["primary"].append(student)
        student_count[student]["primary"] += 1
        last_primary_week[student] = week_number
    
    available_secondary = get_available_students(date, "secondary", primary)
    secondary = available_secondary[:REQUIRED_SECONDARY]
    for student in secondary:
        schedule[date]["secondary"].append(student)
        student_count[student]["secondary"] += 1

    # If we don't have enough secondary students, try to find more
    while len(secondary) < REQUIRED_SECONDARY and len(available_secondary) > len(secondary):
        next_student = available_secondary[len(secondary)]
        secondary.append(next_student)
        schedule[date]["secondary"].append(next_student)
        student_count[next_student]["secondary"] += 1

# Print summary
print("\nStudent Interview Counts:")
for student in students:
    print(f"{student}: Primary - {student_count[student]['primary']}, Secondary - {student_count[student]['secondary']}")

# Check if all students were scheduled
not_scheduled = [s for s in students if student_count[s]['primary'] + student_count[s]['secondary'] == 0]
if not_scheduled:
    print("\nStudents not scheduled:", ", ".join(not_scheduled))
else:
    print("\nAll students were scheduled at least once.")

# Check for dates with insufficient interviewers
print("\nDates with insufficient interviewers:")
for date in dates:
    if len(schedule[date]["primary"]) < REQUIRED_PRIMARY or len(schedule[date]["secondary"]) < REQUIRED_SECONDARY:
        print(f"{date}: Primary - {len(schedule[date]['primary'])}, Secondary - {len(schedule[date]['secondary'])}")

# Write results to CSV
with open(OUTPUT_FILE, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    
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
    for student in students:
        writer.writerow([student, student_count[student]['primary'], student_count[student]['secondary']])
    
    # Write not scheduled students
    if not_scheduled:
        writer.write

def test_schedule_validity(schedule, availability, weeks):
    print("\nTesting schedule validity...")
    errors = []

    # Create a reverse mapping of weeks to dates
    week_to_dates = defaultdict(list)
    for date, week in weeks.items():
        week_to_dates[week].append(date)

    for student in students:
        last_primary_week = -2  # Initialize to -2 to allow first week assignment
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
                    errors.append(f"{student} is primary on back-to-back weeks: {week_to_dates[last_primary_week]} and {week_to_dates[current_week]}")
                last_primary_week = current_week

    if errors:
        print("Errors found:")
        for error in errors:
            print(f"- {error}")
    else:
        print("No errors found. Schedule is valid.")

    return len(errors) == 0

# Call the test function after scheduling
is_valid = test_schedule_validity(schedule, availability, weeks)
print(f"Schedule is {'valid' if is_valid else 'invalid'}")
