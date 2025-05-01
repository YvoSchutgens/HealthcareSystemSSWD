import secrets
from functools import wraps
from datetime import datetime, date
from cryptography.fernet import Fernet

# Dictionary to store valid tokens
xsrf_tokens = {}

def generate_xsrf_token(username):
    """Generate and store a new XSRF token for the user"""
    token = secrets.token_urlsafe(32)
    xsrf_tokens[username] = token
    return token

def validate_xsrf_token(username, token):
    """Validate the provided token against stored token"""
    stored_token = xsrf_tokens.get(username)
    return stored_token is not None and secrets.compare_digest(stored_token, token)

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

def view_reports():
    while True:
        print("\nView Reports:")
        print("1. View Daily Report")
        print("2. View Monthly Report")
        print("3. Back to CEO Menu")
        choice = input("Choose an option: ")
        
        if choice == '1':
            view_daily_report()
        elif choice == '2':
            view_monthly_report()
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

def view_daily_report():
    from MainSystem import generate_daily_report, generate_monthly_report  # Importing the functions to generate reports
    from MainSystem import conn, c  # Assuming these are defined in MainSystem
    c = conn.cursor()
    today = date.today().isoformat()

    #Auto-generate if missing
    c.execute("SELECT 1 FROM daily_reports WHERE report_date = ?", (today,))
    if not c.fetchone():
        generate_daily_report()
    
    c.execute("SELECT report_data, report_date FROM daily_reports WHERE report_date = ?", (today,))
    result = c.fetchone()
    
    if not result:
        print("No daily report available for today. Please generate one first.")
        return
    
    encrypted_data, report_date = result
    
    # Decrypt the report data
    try:
        cipher = get_cipher()
        decrypted_data = cipher.decrypt(encrypted_data).decode()  # Decrypt and decode back to string
        report_data = eval(decrypted_data)  # Convert string back to list of dicts
    except Exception as e:
        print(f"Error decrypting report: {e}")
        return
    
    # Format the date nicely (e.g., "2023-11-15" → "November 15, 2023")
    try:
        formatted_date = datetime.strptime(report_date, "%Y-%m-%d").strftime("%B %d, %Y")
    except:
        formatted_date = report_date  # Fallback to raw date if formatting fails
    
    print("\n=== Daily Report ===")
    print(f"{'Doctor':<20}{'Patients Served':<20}{'Salary':<15}")
    print("-" * 55)
    for doctor in report_data:
        print(f"{doctor['doctor_username']:<20}{doctor['patients_served']:<20}${doctor['salary']:<15.2f}")
    print()

def view_monthly_report():
    from MainSystem import generate_daily_report, generate_monthly_report  # Importing the functions to generate reports
    from MainSystem import conn, c  # Assuming these are defined in MainSystem
    current_month = date.today().strftime("%Y-%m")

    # Auto-generate if missing
    c.execute("SELECT 1 FROM monthly_reports WHERE report_month = ?", (current_month,))
    if not c.fetchone():
        generate_monthly_report()
    
    c.execute("SELECT report_data FROM monthly_reports WHERE report_month = ?", (current_month,))
    result = c.fetchone()
    
    if not result:
        print("No monthly report available for this month. Please generate one first.")
        return
    
    #report_data = eval(result[0])  # Convert string back to list of dicts
    encrypted_data = result[0]

    # Decrypt the report data
    try:
        cipher = get_cipher()
        decrypted_data = cipher.decrypt(encrypted_data).decode()  # Decrypt and decode back to string
        report_data = eval(decrypted_data)  # Convert string back to list of dicts
    except Exception as e:
        print(f"Error decrypting report: {e}")
        return
    
    print("\n=== Monthly Report ===")
    print(f"{'Doctor':<20}{'Patients Served':<20}{'Salary':<15}")
    print("-" * 55)
    for doctor in report_data:
        print(f"{doctor['doctor_username']:<20}{doctor['patients_served']:<20}${doctor['salary']:<15.2f}")
    print()


def ceo_menu(username):
    from MainSystem import view_payments ,update_salary, view_patient_medical_record #view_reports, 
    
    # Generate initial token
    current_token = generate_xsrf_token(username)
    
    while True:
        print("\nCEO Menu:")
        print("1. View patient payments information")
        print("2. View reports")
        print("3. Update salary")
        print("4. View patient medical record")
        print("5. Logout")
        
        opt = input("Choose an option: ")
        
        if opt == '1':
            view_payments()  # Read-only
            
        elif opt == '2':
            view_reports()  # Read-only
            
        elif opt == '3':
            print(f"[Security] Using XSRF token: {current_token}")
            update_salary()
            current_token = generate_xsrf_token(username)
            
        elif opt == '4':
            view_patient_medical_record()  # Read-only
            
        elif opt == '5':
            if username in xsrf_tokens:
                del xsrf_tokens[username]
            break