VERIFICATION_CODE_EXPIRY = 300  # 5 minutes in seconds

login_attempts = {}

# Predefined admin codes for each role
ADMIN_CODES = {
    'Staff': 'Staff5360',
    'Nurse': 'Nurse1439',
    'Doctor': 'Doctor8285',
    'CEO': 'CEO3594'
}

def hash_password(password):
    from hashlib import sha256
    return sha256(password.encode()).hexdigest()

def verify_admin_code(role):
    """Verify admin code for specific roles"""
    if role not in ADMIN_CODES:
        return True  # No admin code required for this role
    
    expected_code = ADMIN_CODES[role]
    attempts = 3
    
    while attempts > 0:
        entered_code = input(f"Enter {role} admin code: ")
        if entered_code == expected_code:
            return True
        attempts -= 1
        print(f"Incorrect admin code.")
    
    print("Admin verification failed.")
    return False


def send_verification_email(recipient_email, verification_code):
    """Simplified email sender"""
    import smtplib
    
    sender = "healthcaresystemsswd@gmail.com"
    password = "necs twyc hxbh lnzl"
    
    message = f"""Subject: Verification Code\n\n
    Your verification code is: {verification_code}
    """
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient_email, message)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def verify_email_code(expected_code, recipient_email):
    """Verify the code entered by the user"""
    import time
    import random
    
    start_time = time.time()
    attempts = 3
    VERIFICATION_CODE_EXPIRY = 300  # 5 minutes in seconds
    
    while attempts > 0 and time.time() - start_time < VERIFICATION_CODE_EXPIRY:
        user_code = input("Enter verification code (or 'resend' to get a new code): ")
        
        if user_code.lower() == 'resend':
            new_code = str(random.randint(100000, 999999))
            if send_verification_email(recipient_email, new_code):
                print("New verification code sent!")
                expected_code = new_code
                start_time = time.time()  # Reset timer
                continue
            else:
                attempts -= 1
                print(f"Failed to resend code. {attempts} attempts remaining.")
                continue
        
        if user_code == expected_code:
            return True
        
        attempts -= 1
        print(f"Incorrect code. {attempts} attempts remaining.")
    
    return False

def is_valid_password(password):
    """Check if password meets requirements"""
    if len(password) < 8:
        return False
    
    num_count = sum(1 for char in password if char.isdigit())
    upper_count = sum(1 for char in password if char.isupper())
    
    return num_count >= 2 and upper_count >= 2

def generate_captcha():
    import random
    """Generate simple math CAPTCHA (1 attempt)"""
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    return f"{a} + {b}", a + b

def verify_captcha():
    """1-attempt CAPTCHA check"""
    question, answer = generate_captcha()
    user_answer = input(f"\nCAPTCHA Verification: What is {question}? ").strip()
    try:
        return int(user_answer) == answer
    except ValueError:
        return False

def signup():
    from MainSystem import conn, c
    import random
    import psutil
    import subprocess
    from sys import platform

    # --- Keylogger Detection (same as before) ---
    def check_for_keyloggers():
        keylogger_indicators = [
            'keylog', 'notep', 'logger', 'logkbd', 'kbdlog', 'keystroke',
            'hook', 'spy', 'recorder', 'capture', 'rat', 'remote',
            'hax', 'inject', 'sniff'
        ]
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if any(indicator in proc_name for indicator in keylogger_indicators):
                        print(f"\n[!] SECURITY ALERT: Keylogger detected (Process: '{proc_name}')")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            print(f"[!] Error during security check: {e}")
            return False

    # --- Initial Security Check ---
    print("\n--- Sign Up ---")
    if check_for_keyloggers():
        print("Signup CANCELLED due to security risk.\n")
        return
    print("[✓] Security check passed\n")

    # --- Secure Input Wrapper ---
    def get_input(prompt, sensitive=False):
        if sensitive and check_for_keyloggers():
            print("Input blocked - potential keylogger detected")
            return None
        return input(prompt)

    # --- Main Signup Flow ---
    username = get_input("Enter username: ")
    if not username:  # Check for security cancellation
        return

    # Password validation loop
    while True:
        password = get_input("Enter password (min 8 chars, 2 numbers, 2 uppercase letters): ", sensitive=True)
        if not password:
            return
        if is_valid_password(password):
            break
        print("Provided information is invalid. Please try again.")

    role = get_input("Enter role (Patient, Staff, Nurse, Doctor, CEO): ")
    if not role:
        return

    valid_roles = ['Patient', 'Staff', 'Nurse', 'Doctor', 'CEO']
    if role not in valid_roles:
        print("Invalid role. Please choose from: Patient, Staff, Nurse, Doctor, CEO.\n")
        return
    
    # Email verification for patients
    if role == 'Patient':
        email = get_input("Enter your email address for verification: ")
        if not email:
            return
            
        verification_code = str(random.randint(100000, 999999))
        if not send_verification_email(email, verification_code):
            print("Failed to send verification email. Please try again later.\n")
            return
            
        print("Verification code sent to your email. Please check your inbox.")
        if not verify_email_code(verification_code, email):
            print("Email verification failed. Signup cancelled.\n")
            return
    
    # Admin code for staff roles
    else:
        if not verify_admin_code(role):
            print("Signup cancelled, incorrect admin code provided.\n")
            return

    # Database operations
    try:
        conn.execute("BEGIN TRANSACTION")
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                 (username, hash_password(password), role))
        
        if role == 'Patient':
            c.execute('''
                INSERT INTO patient_medical_record 
                (username, name, address, phone, email, ssn, insurance, 
                 treatment_content, prescription, weight, height, blood_pressure, 
                 pulse_rate, doctor_visit_summary, lab_result, radiology_report, 
                 pathology_report, allergy_info, prescribed_medicines, doctor_username)
                VALUES (?, '', '', '', '', '', '', '', '', 0, 0, '', 0, '', '', '', '', '', '', '')
            ''', (username,))
        
        if role in ['Nurse', 'Doctor']:
            salary = 6700.00 if role == 'Nurse' else 18100.00
            c.execute("INSERT INTO salaries (username, role, salary) VALUES (?, ?, ?)",
                     (username, role, salary))
        
        conn.commit()
        print(f"Signup complete.\n")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during signup: {str(e)}\n")

def login():
    from MainSystem import conn, c
    import random
    import time
    import psutil
    import subprocess
    from sys import platform

    # --- Keylogger Detection ---
    def check_for_keyloggers():
        keylogger_indicators = [
            'keylog', 'notep', 'logger', 'logkbd', 'kbdlog', 'keystroke',
            'hook', 'spy', 'recorder', 'capture', 'rat', 'remote',
            'hax', 'inject', 'sniff'
        ]
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if any(indicator in proc_name for indicator in keylogger_indicators):
                        print(f"\n[!] SECURITY ALERT: Keylogger detected (Process: '{proc_name}')")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            print(f"[!] Error during security check: {e}")
            return False

    # --- Initial Security Check ---
    print("\n--- Login ---")
    if check_for_keyloggers():
        print("Login CANCELLED due to security risk.\n")
        return None, None
    print("[✓] Security check passed\n")

    # --- Secure Input Wrapper ---
    def get_input(prompt, sensitive=False):
        if sensitive and check_for_keyloggers():
            print("Input blocked - potential keylogger detected")
            return None
        return input(prompt)

    # --- Main Login Flow ---
    MAX_ATTEMPTS = 5
    LOCKOUT_TIME = 300
    global login_attempts

    username = get_input("Enter username: ").strip()
    if not username:
        return None, None

    # Account lockout check
    if username in login_attempts:
        last_attempt_time, attempts = login_attempts[username]
        if attempts >= MAX_ATTEMPTS and (time.time() - last_attempt_time) < LOCKOUT_TIME:
            remaining_time = int(LOCKOUT_TIME - (time.time() - last_attempt_time))
            print(f"Account temporarily locked. Please try again in {remaining_time} seconds.\n")
            return None, None

    password = get_input("Enter password: ", sensitive=True)
    if not password:
        return None, None

    # Verify credentials
    c.execute("SELECT role FROM users WHERE username = ? AND password = ?", 
              (username, hash_password(password)))
    result = c.fetchone()

    if not result:
        # Update failed attempts
        attempts = login_attempts.get(username, (0, 0))[1] + 1
        login_attempts[username] = (time.time(), attempts)
        
        remaining_attempts = MAX_ATTEMPTS - attempts
        if remaining_attempts > 0:
            print(f"Invalid credentials. {remaining_attempts} attempts remaining.\n")
        else:
            print("Too many failed attempts. Account temporarily locked for 5 minutes.\n")
        return None, None
    
    # Successful login
    if username in login_attempts:
        del login_attempts[username]
    
    role = result[0]

    # Additional verifications
    if role == 'Staff' and not verify_captcha():
        print("CAPTCHA verification failed. Access denied.")
        return None, None

    if role == 'Patient':
        email = get_input("Enter your email address for verification: ")
        if not email:
            return None, None
            
        verification_code = str(random.randint(100000, 999999))
        if not send_verification_email(email, verification_code):
            print("Failed to send verification email.\n")
            return None, None
            
        print("Verification code sent. Please check your email.")
        if not verify_email_code(verification_code, email):
            print("Email verification failed.\n")
            return None, None
    else:
        if not verify_admin_code(role):
            print("Login cancelled, incorrect admin code provided.\n")
            return None, None

    print(f"Login successful.\n")
    return username, role