# How to Run the Interview Scheduler

1. **Check if you have Python:**
   Type in Terminal: `which python3`

2. **If not installed, install with Homebrew:**
   Copy and paste into Terminal:

   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

   Then type:

   ```
   brew install python
   ```

3. **Create your student_availability.csv file:**

   - Open Excel or Numbers
   - First row should be: `First Name, Last Name, followed by dates (like 9/9, 9/10, etc.)`
   - Each student row should have:
     - Their first name
     - Their last name
     - For each date: leave blank if they're available, put 'x' if they're not available
   - Save as CSV format with exactly this name: `student_availability.csv`

   Example:

   ```
   First Name,Last Name,9/9,9/10,9/16,9/17
   John,Smith,x,,,x
   Jane,Doe,,x,x,
   Sam,Jones,,,,
   ```

4. **Put both files on your Desktop:**

   - scheduler_script.py
   - student_availability.csv

5. **Open Terminal:**

   - Press `Command (⌘) + Space`
   - Type "Terminal" and press Enter

6. **Go to Desktop:**
   Type in Terminal: `cd Desktop`

7. **Run:**
   Type in Terminal: `python3 scheduler_script.py`

The output will be saved as `interview_schedule.csv` on your Desktop.
