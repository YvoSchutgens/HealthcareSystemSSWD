from sqlite3 import connect
from hashlib import sha256
from datetime import datetime, date, time, timedelta
import random
from cryptography.fernet import Fernet


# Database setup
conn = connect('healthcare_system_yvojosh.db')
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

from SecurePatientstaffnursedoctorceoInteraction import signup, login, hash_password
from SecureStaffnursedoctorceoInteraction import view_patient_medical_record
from SecurePatientInteraction import patient_menu
from SecureStaffInteraction import staff_menu
from SecureNurseInteraction import nurse_menu
from SecureDoctorInteraction import doctor_menu
from SecureCeoInteraction import ceo_menu
from SecureAppointmentCreation import make_appointment
from SecureAppointmentChanging import change_appointment
from SecureAppointmentCancellation import cancel_appointment
from SecureCreateRecord import create_patient_medical_record
from SecureDisplay import list_patients
from SecureUpdateRecord import update_patient_medical_record
from SecurePerformanceData import (
    should_generate_daily_report,
    check_and_generate_reports,
    generate_reports,
    generate_daily_report,
    generate_monthly_report
)

# Ensure patient_medical_record table exists with all necessary fields
c.execute('''
CREATE TABLE IF NOT EXISTS patient_medical_record (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    name TEXT,
    address TEXT,
    phone TEXT,
    email TEXT,
    ssn TEXT,
    insurance TEXT,
    treatment_content TEXT,
    prescription TEXT,
    weight REAL,
    height REAL,
    blood_pressure TEXT,
    pulse_rate INTEGER,
    doctor_visit_summary TEXT,
    lab_result TEXT,
    radiology_report TEXT,
    pathology_report TEXT,
    allergy_info TEXT,
    prescribed_medicines TEXT,
    doctor_username TEXT,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
)
''')
# Create other tables if not exists
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    datetime TEXT,
    reason TEXT,
    status TEXT,
    FOREIGN KEY (patient_id) REFERENCES patient_medical_record(patient_id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    type TEXT,
    amount REAL,
    status TEXT DEFAULT 'Unpaid',
    reference_number TEXT,
    card_last_four TEXT,
    FOREIGN KEY (patient_id) REFERENCES patient_medical_record(patient_id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS salaries (
    username TEXT PRIMARY KEY,
    role TEXT,
    salary REAL,
    FOREIGN KEY (username) REFERENCES users(username)
)
''')

# Add these table creation statements with the others
c.execute('''
CREATE TABLE IF NOT EXISTS daily_reports (
    report_date TEXT PRIMARY KEY,
    report_data TEXT,
    generated_at TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS monthly_reports (
    report_month TEXT PRIMARY KEY,
    report_data TEXT,
    generated_at TEXT
)
''')

conn.commit()

conn.commit()

def get_patient_id_by_username(username):
    c.execute("SELECT patient_id FROM patient_medical_record WHERE username = ?", (username,))
    result = c.fetchone()
    return result[0] if result else None

# Add this helper function to generate reference numbers
def generate_reference_number():
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def card_info(card_name, card_number, exp_date, cvc):
    """Validate credit card information"""
    errors = []
    
    # Validate card number (16 digits)
    if not (card_number.isdigit() and len(card_number) == 16):
        errors.append("Card number must be 16 digits")
    
    # Validate expiration date (MM/YY format)
    if len(exp_date) != 5 or exp_date[2] != '/' or not exp_date[:2].isdigit() or not exp_date[3:].isdigit():
        errors.append("Expiration date must be in MM/YY format")
    else:
        month, year = map(int, exp_date.split('/'))
        if month < 1 or month > 12:
            errors.append("Invalid month (must be 01-12)")
        # You might want to add year validation against current year
    
    # Validate CVC (3 digits)
    if not (cvc.isdigit() and len(cvc) == 3):
        errors.append("CVC must be 3 digits")
    
    return errors

def make_payment(username):
    patient_id = get_patient_id_by_username(username)
    if not patient_id:
        print("No medical record found.\n")
        return

    payment_type = input("Payment type (copay/invoice): ").lower()
    if payment_type not in ['copay', 'invoice']:
        print("Invalid payment type. Please enter 'copay' or 'invoice'.\n")
        return

    c.execute("SELECT payment_id, amount FROM payments WHERE patient_id = ? AND type = ? AND status = 'Unpaid'",
              (patient_id, payment_type))
    payments = c.fetchall()

    if not payments:
        print(f"No unpaid {payment_type} payments.\n")
        return

    print(f"\nUnpaid {payment_type} payments:")
    for i, (pid, amount) in enumerate(payments, 1):
        print(f"{i}. Payment ID: {pid}, Amount: ${amount:.2f}")

    try:
        choice = int(input("Select a payment to pay (number): ")) - 1
        payment_id, amount_due = payments[choice]
    except (IndexError, ValueError):
        print("Invalid selection.\n")
        return

    try:
        pay_amount = float(input(f"Enter amount to pay (due: ${amount_due:.2f}): "))
    except ValueError:
        print("Invalid amount.\n")
        return

    if pay_amount != amount_due:
        print("You must pay the full amount to complete this payment.\n")
        return
    
    # Get credit card information
    print("\nPlease enter your payment details:")
    card_name = input("Name on card: ").strip()
    card_number = input("Card number (16 digits): ").replace(" ", "")
    exp_date = input("Expiration date (MM/YY): ").strip()
    cvc = input("CVC (3 digits): ").strip()
    
    # Validate card information
    validation_errors = card_info(card_name, card_number, exp_date, cvc)
    if validation_errors:
        print("\nPayment failed. Please correct the following errors:")
        for error in validation_errors:
            print(f"- {error}")
        print()
        return
    
    # Process payment (in a real system, this would connect to payment processor)
    print("\nProcessing payment...")
    
    # Mask card number for display (show first 4 and last 4 digits)
    masked_number = f"{card_number[:4]} **** **** {card_number[-4:]}"
    print(f"Charging ${pay_amount:.2f} to card {masked_number}")

    # After successful validation:
    last_four = card_number[-4:]  # Store just the last 4 digits

    # Generate reference number only for copay payments
    reference_number = generate_reference_number() if payment_type == 'copay' else None

    # Update payment after paying
    if reference_number:
        c.execute("UPDATE payments SET status = 'Paid', reference_number = ?, card_last_four = ? WHERE payment_id = ?", (reference_number, last_four, payment_id)) 
        print("Copay successfully paid.\n")
    else:
        c.execute("UPDATE payments SET status = 'Paid', card_last_four = ? WHERE payment_id = ?", (last_four, payment_id,))
        print("Invoice successfully paid.\n")

    conn.commit()

def view_payments():
    # Get list of all patients
    c.execute("SELECT patient_id, name FROM patient_medical_record ORDER BY name")
    patients = c.fetchall()
    
    if not patients:
        print("No patients found in the system.\n")
        return
    
    # Display patient list
    print("\n=== Patient List ===")
    for idx, (patient_id, name) in enumerate(patients, 1):
        print(f"{idx}. {name} (ID: {patient_id})")
    
    # Get patient selection
    try:
        selection = int(input("\nSelect patient (number): ")) - 1
        if selection < 0 or selection >= len(patients):
            raise ValueError
        patient_id, patient_name = patients[selection]
    except (ValueError, IndexError):
        print("Invalid selection.\n")
        return
    
    # Get payments for selected patient
    c.execute("""
        SELECT payment_id, type, amount, status, reference_number, card_last_four
        FROM payments
        WHERE patient_id = ?
        ORDER BY payment_id
    """, (patient_id,))
    
    payments = c.fetchall()
    
    # Display results
    print(f"\n=== Payments for {patient_name} ===")
    if payments:
        print(f"{'ID':<6}{'Type':<10}{'Amount':<12}{'Status':<10}{'Reference number':<20}{'Card number':<12}")
        print("-" * 80)
        for payment in payments:
            pid, ptype, amount, status, ref, last_four = payment
            ref = ref if ref else "-"
            card_display = f"**** **** **** {last_four}" if last_four else "-"
            print(f"{pid:<6}{ptype:<10}${amount:<11.2f}{status:<10}{ref:<20}{card_display:<12}")
        print("-" * 80 + "\n")
    else:
        print("No payment information found for this patient.\n")


def update_salary():
    # Show all medical staff
    c.execute('''
        SELECT u.username, u.role, COALESCE(s.salary, 0) as salary
        FROM users u
        LEFT JOIN salaries s ON u.username = s.username
        WHERE u.role IN ('Nurse', 'Doctor')
        ORDER BY u.role, u.username
    ''')
    
    staff = c.fetchall()
    
    print("\nDoctor and nurse Salaries:")
    for idx, (username, role, salary) in enumerate(staff, 1):
        print(f"{idx}. {username} ({role}): ${salary:,.2f}")
    
    try:
        choice = int(input("\nSelect nurse or doctor to update (number): ")) - 1
        selected_username, selected_role, _ = staff[choice]
    except (IndexError, ValueError):
        print("Invalid selection.")
        return
    
    try:
        new_salary = float(input(f"Enter new salary for {selected_username}: "))
        c.execute("INSERT OR REPLACE INTO salaries (username, role, salary) VALUES (?, ?, ?)",
                 (selected_username, selected_role, new_salary))
        conn.commit()
        print("Salary successfully changed.\n")
    except ValueError:
        print("Invalid salary amount. Please enter a number.\n")


def show_menu():
    print("1. Signup")
    print("2. Login")
    print("3. Exit")

def main():
    # Auto-generate reports on startup
    check_and_generate_reports()
    while True:
        show_menu()
        choice = input("Choose an option: ")
        if choice == '1':
            signup()
        elif choice == '2':
            username, role = login()
            if role == 'Patient':
                patient_menu(username)
            elif role == 'Staff':
                staff_menu(username)
            elif role == 'Nurse':
                nurse_menu(username)
            elif role == 'Doctor':
                doctor_menu(username)
            elif role == 'CEO':
                ceo_menu(username)
        elif choice == '3':
            print("Exiting system.")
            break
        else:
            print("Invalid choice. Try again.\n")

if __name__ == '__main__':
    main()
    conn.close()
