from cryptography.fernet import Fernet
from datetime import datetime, time

def load_or_create_key():
    try:
        with open("report.key", "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        key = Fernet.generate_key()
        with open("report.key", "wb") as key_file:
            key_file.write(key)
        return key

def get_cipher():
    key = load_or_create_key()
    return Fernet(key)

def should_generate_daily_report():
    from datetime import datetime, time
    """Check if current time is at/past the daily trigger time (9 PM)"""
    trigger_time = time(21, 0)  # 9 PM (21:00 in 24-hour format)
    return datetime.now().time() >= trigger_time


def check_and_generate_reports():
    from MainSystem import conn, c
    from datetime import datetime, date, time
    from SecurePerformanceData import generate_daily_report, generate_monthly_report
    #"""Automatically generate missing reports when system starts"""
    now = datetime.now()
    today = now.date().isoformat()
    
    # Check daily report
    c.execute("SELECT generated_at FROM daily_reports WHERE report_date = ?", (today,))
    existing_report = c.fetchone()

    # Generate if:
    # 1. No report exists today OR
    # 2. It's after 9 PM and last report was before 9 PM
    if not existing_report or (should_generate_daily_report() and 
                             datetime.fromisoformat(existing_report[0]).time() < time(21, 0)):
        print("Generating 9 PM daily report...")
        generate_daily_report()

    # MONTHLY REPORT LOGIC (runs on 1st of month)
    if now.day == 1:  # First day of month
        current_month = now.strftime("%Y-%m")
        c.execute("SELECT 1 FROM monthly_reports WHERE report_month = ?", (current_month,))
        if not c.fetchone():
            generate_monthly_report()

def generate_reports():
    from SecurePerformanceData import generate_daily_report, generate_monthly_report
    while True:
        print("\nGenerate Reports:")
        print("1. Generate Daily Report")
        print("2. Generate Monthly Report")
        print("3. Back to CEO Menu")
        choice = input("Choose an option: ")
        
        if choice == '1':
            generate_daily_report()
        elif choice == '2':
            generate_monthly_report()
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

def generate_daily_report():
    from MainSystem import conn, c
    from datetime import datetime, date

    today = date.today().isoformat()
    
    # Get all doctors
    c.execute("SELECT username FROM users WHERE role = 'Doctor'")
    doctors = c.fetchall()
    
    report_data = []
    
    for (doctor_username,) in doctors:
        # Count patients served today (patients with updated records today)
        c.execute('''
            SELECT COUNT(DISTINCT patient_id)
            FROM patient_medical_record
            WHERE doctor_username = ?
            AND date(patient_medical_record.last_updated) = ?
        ''', (doctor_username, today))
        patients_served = c.fetchone()[0] or 0
        
        # Get doctor's salary
        c.execute("SELECT salary FROM salaries WHERE username = ?", (doctor_username,))
        salary_result = c.fetchone()
        salary = salary_result[0] if salary_result else 0.0
        
        report_data.append({
            'doctor_username': doctor_username,
            'patients_served': patients_served,
            'salary': salary
        })
    
    # Store the report
    generated_at = datetime.now().isoformat()
    cipher = get_cipher()
    encrypted_data = cipher.encrypt(str(report_data).encode())

    c.execute('''
        INSERT OR REPLACE INTO daily_reports (report_date, report_data, generated_at)
        VALUES (?, ?, ?)
    ''', (today, encrypted_data, generated_at))
    conn.commit()
    
    print(f"Encrypted Daily report for {today} generated successfully.")

def generate_monthly_report():
    from MainSystem import conn, c
    from datetime import datetime, date

    current_month = datetime.today().strftime("%Y-%m")
    
    # Get all doctors
    c.execute("SELECT username FROM users WHERE role = 'Doctor'")
    doctors = c.fetchall()
    
    report_data = []
    
    for (doctor_username,) in doctors:
        # Count patients served this month
        c.execute('''
            SELECT COUNT(DISTINCT patient_id)
            FROM patient_medical_record
            WHERE doctor_username = ?
            AND strftime('%Y-%m', patient_medical_record.last_updated) = ?
        ''', (doctor_username, current_month))
        patients_served = c.fetchone()[0] or 0
        
        # Get doctor's salary
        c.execute("SELECT salary FROM salaries WHERE username = ?", (doctor_username,))
        salary_result = c.fetchone()
        salary = salary_result[0] if salary_result else 0.0
        
        report_data.append({
            'doctor_username': doctor_username,
            'patients_served': patients_served,
            'salary': salary
        })
    
    # Store the report
    generated_at = datetime.now().isoformat()
    cipher = get_cipher()
    encrypted_data = cipher.encrypt(str(report_data).encode())

    c.execute('''
        INSERT OR REPLACE INTO monthly_reports (report_month, report_data, generated_at)
        VALUES (?, ?, ?)
    ''', (current_month, encrypted_data, generated_at))
    conn.commit()
    
    print(f"Encrypted Monthly report for {current_month} generated successfully.")